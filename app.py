from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from database import db
from routes.consumo import consumo_bp
from routes.auth import auth_bp
from routes.ayuda import ayuda_bp
from routes.doctor import doctor_bp
from routes.admin import admin_bp

app = Flask(__name__)

# 1. Configuración de la base de datos (SQLite) y JWT
app.config["SQLALCHEMY_DATABASE_URI"] = ("mssql+pyodbc://@localhost\\SQLEXPRESS/sistemanutri""?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "super-secreto-2026"

# 2. Vincular extensiones y registrar blueprints en la app Flask
db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(consumo_bp)
app.register_blueprint(ayuda_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(admin_bp)

@app.after_request
def habilitar_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response

# 3. Crear las tablas automáticamente
with app.app_context():
    from sqlalchemy import text
    from models.orm_models import (
        UsuarioModel,
        ObjetivoNutricionalModel,
        CatalogoAlimentoModel,
        RegistroConsumoModel,
        SolicitudAyudaModel,
        MensajeChatModel,
    )
    db.create_all()

    # Migraciones seguras para columnas agregadas sobre BD existente (SQLite o SQL Server)
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.engine)
    dialecto = db.engine.dialect.name
    es_mssql = dialecto == "mssql"

    def asegurar_columna(tabla: str, columna: str, definicion_sqlite: str, definicion_mssql: str):
        try:
            cols = {c["name"].lower() for c in inspector.get_columns(tabla)}
            if columna.lower() not in cols:
                if es_mssql:
                    stmt = f"ALTER TABLE {tabla} ADD {columna} {definicion_mssql}"
                else:
                    stmt = f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion_sqlite}"
                db.session.execute(text(stmt))
                db.session.commit()
        except Exception:
            db.session.rollback()

    asegurar_columna("registros_consumo", "ingredientes_consumidos", "VARCHAR(500) DEFAULT ''", "VARCHAR(500) DEFAULT ''")
    hash_def = generate_password_hash("123456")
    asegurar_columna("Usuarios", "password_hash", f"VARCHAR(255) NOT NULL DEFAULT '{hash_def}'", f"VARCHAR(255) NOT NULL DEFAULT '{hash_def}'")
    asegurar_columna("Usuarios", "rol", "VARCHAR(20) NOT NULL DEFAULT 'usuario'", "VARCHAR(20) NOT NULL DEFAULT 'usuario'")
    asegurar_columna("Usuarios", "email", "VARCHAR(120)", "VARCHAR(120) NULL")
    asegurar_columna("Usuarios", "edad", "INTEGER", "INT NULL")
    asegurar_columna("Usuarios", "peso_kg", "FLOAT", "FLOAT NULL")
    asegurar_columna("Usuarios", "altura_cm", "FLOAT", "FLOAT NULL")
    asegurar_columna("Usuarios", "telefono", "VARCHAR(30)", "VARCHAR(30) NULL")

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "sistema": "SISTEMA NUTRI",
        "estado": "En línea",
        "autor": "Armando Imanol Aguilar Espiricueto"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)