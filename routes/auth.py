from functools import wraps
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import db
from models.orm_models import UsuarioModel, ObjetivoNutricionalModel

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

ROLES_VALIDOS = {"usuario", "doctor", "admin"}


def requerir_rol(*roles_permitidos):
    """Decorador que valida el JWT y verifica que el usuario tenga uno de los roles permitidos."""
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            usuario_id = int(get_jwt_identity())
            usuario = db.session.get(UsuarioModel, usuario_id)
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404
            if usuario.rol not in roles_permitidos:
                return jsonify({
                    "error": "No tienes permisos para acceder a este recurso",
                    "rol_requerido": list(roles_permitidos),
                    "rol_actual": usuario.rol
                }), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper


def serializar_usuario(usuario: UsuarioModel) -> dict:
    """Serializa los datos públicos y personales de un usuario sin exponer su contraseña."""
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "rol": usuario.rol,
        "preferencias": usuario.preferencias or "",
        "email": usuario.email or "",
        "edad": usuario.edad,
        "peso_kg": usuario.peso_kg,
        "altura_cm": usuario.altura_cm,
        "telefono": usuario.telefono or "",
    }


@auth_bp.route('/login', methods=['POST'])
def login():
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get("nombre") or "").strip()
    password = datos.get("password")

    if not nombre or not password:
        return jsonify({"error": "Faltan credenciales"}), 400

    usuario = db.session.query(UsuarioModel).filter_by(nombre=nombre).first()

    if usuario and check_password_hash(usuario.password_hash, password):
        token = create_access_token(
            identity=str(usuario.id),
            additional_claims={"rol": usuario.rol}
        )
        return jsonify({
            "access_token": token,
            "usuario": usuario.nombre,
            "id": usuario.id,
            "rol": usuario.rol
        }), 200

    return jsonify({"error": "Credenciales incorrectas"}), 401


@auth_bp.route('/register', methods=['POST'])
def register():
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get("nombre") or "").strip()
    password = datos.get("password") or ""

    if len(nombre) < 2 or len(password) < 4:
        return jsonify({"error": "Nombre (mín. 2 caracteres) y contraseña (mín. 4) son obligatorios"}), 400

    if db.session.query(UsuarioModel).filter_by(nombre=nombre).first():
        return jsonify({"error": f"El usuario '{nombre}' ya existe"}), 400

    nuevo = UsuarioModel(
        nombre=nombre,
        password_hash=generate_password_hash(password),
        rol="usuario",
        preferencias=datos.get("preferencias"),
        email=datos.get("email"),
        edad=datos.get("edad"),
        peso_kg=datos.get("peso_kg"),
        altura_cm=datos.get("altura_cm"),
        telefono=datos.get("telefono"),
    )
    db.session.add(nuevo)
    db.session.flush()

    objetivo = ObjetivoNutricionalModel(
        usuario_id=nuevo.id,
        calorias_meta=2000.0,
        proteina_meta=120.0
    )
    db.session.add(objetivo)
    db.session.commit()

    token = create_access_token(
        identity=str(nuevo.id),
        additional_claims={"rol": nuevo.rol}
    )
    return jsonify({
        "mensaje": "Usuario registrado exitosamente",
        "access_token": token,
        "usuario": nuevo.nombre,
        "id": nuevo.id,
        "rol": nuevo.rol
    }), 201


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def obtener_perfil():
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(serializar_usuario(usuario)), 200


@auth_bp.route('/perfil', methods=['PUT'])
@jwt_required()
def actualizar_perfil():
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    datos = request.get_json(silent=True) or {}
    if "email" in datos:
        usuario.email = datos["email"]
    if "telefono" in datos:
        usuario.telefono = datos["telefono"]
    if "preferencias" in datos:
        usuario.preferencias = datos["preferencias"]
    if "edad" in datos:
        usuario.edad = int(datos["edad"]) if datos["edad"] not in (None, "") else None
    if "peso_kg" in datos:
        usuario.peso_kg = float(datos["peso_kg"]) if datos["peso_kg"] not in (None, "") else None
    if "altura_cm" in datos:
        usuario.altura_cm = float(datos["altura_cm"]) if datos["altura_cm"] not in (None, "") else None

    db.session.commit()
    return jsonify({
        "mensaje": "Datos personales actualizados correctamente",
        "perfil": serializar_usuario(usuario)
    }), 200
