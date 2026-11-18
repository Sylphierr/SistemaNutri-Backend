from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from database import db
from models.orm_models import UsuarioModel

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    datos = request.get_json(silent=True) or {}
    nombre = datos.get("nombre")
    password = datos.get("password")

    if not nombre or not password:
        return jsonify({"error": "Faltan credenciales"}), 400

    usuario = db.session.query(UsuarioModel).filter_by(nombre=nombre).first()

    # Verificamos la contraseña encriptada
    if usuario and check_password_hash(usuario.password_hash, password):
        # El token almacena el ID del usuario en su firma criptográfica
        token = create_access_token(identity=str(usuario.id))
        return jsonify({"access_token": token, "usuario": usuario.nombre}), 200

    return jsonify({"error": "Credenciales incorrectas"}), 401