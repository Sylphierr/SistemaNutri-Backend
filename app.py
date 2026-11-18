from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from database import db
from routes.consumo import consumo_bp
from routes.auth import auth_bp

app = Flask(__name__)

# 1. Configuración de la base de datos (SQLite) y JWT
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sistema_nutri.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "super-secreto-2026"

# 2. Vincular extensiones y registrar blueprints en la app Flask
db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(consumo_bp)

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
    )
    db.create_all()
    try:
        db.session.execute(text("ALTER TABLE registros_consumo ADD COLUMN ingredientes_consumidos VARCHAR(500) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        hash_default = generate_password_hash("123456")
        db.session.execute(
            text(f"ALTER TABLE usuarios ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT '{hash_default}'")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "sistema": "SISTEMA NUTRI",
        "estado": "En línea",
        "autor": "Armando Imanol Aguilar Espiricueto"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)