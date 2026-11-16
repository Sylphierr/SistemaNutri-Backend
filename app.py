from flask import Flask, jsonify
from database import db
from routes.consumo import consumo_bp

app = Flask(__name__)

# 1. Configuración de la base de datos (SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sistema_nutri.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 2. Vincular la base de datos y registrar blueprints en la app Flask
db.init_app(app)
app.register_blueprint(consumo_bp)

# 3. Crear las tablas automáticamente
with app.app_context():
    from models.orm_models import (
        UsuarioModel,
        ObjetivoNutricionalModel,
        CatalogoAlimentoModel,
        RegistroConsumoModel,
    )
    db.create_all()

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "sistema": "SISTEMA NUTRI",
        "estado": "En línea",
        "autor": "Armando Imanol Aguilar Espiricueto"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)