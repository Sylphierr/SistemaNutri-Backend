from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from werkzeug.security import generate_password_hash
from database import db
from models.orm_models import (
    UsuarioModel,
    ObjetivoNutricionalModel,
    CatalogoAlimentoModel,
    RegistroConsumoModel,
    SolicitudAyudaModel,
)
from models.reporte_helper import construir_resumen_usuario, serializar_registro_consumo
from routes.auth import requerir_rol, serializar_usuario, ROLES_VALIDOS
from routes.ayuda import _serializar_solicitud

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/resumen-global', methods=['GET'])
@requerir_rol("admin")
def resumen_global():
    usuarios = db.session.query(UsuarioModel).all()
    conteo_roles = {"usuario": 0, "doctor": 0, "admin": 0}
    for u in usuarios:
        conteo_roles[u.rol] = conteo_roles.get(u.rol, 0) + 1

    return jsonify({
        "total_usuarios": len(usuarios),
        "usuarios_por_rol": conteo_roles,
        "total_registros_consumo": db.session.query(RegistroConsumoModel).count(),
        "total_alimentos_catalogo": db.session.query(CatalogoAlimentoModel).count(),
        "total_solicitudes_ayuda": db.session.query(SolicitudAyudaModel).count(),
        "solicitudes_pendientes": db.session.query(SolicitudAyudaModel).filter_by(estado="pendiente").count(),
    }), 200


@admin_bp.route('/usuarios', methods=['GET'])
@requerir_rol("admin")
def listar_todos_usuarios():
    usuarios = db.session.query(UsuarioModel).order_by(UsuarioModel.id).all()
    resultado = []
    for u in usuarios:
        data = serializar_usuario(u)
        data["total_registros"] = db.session.query(RegistroConsumoModel).filter_by(usuario_id=u.id).count()
        data["total_solicitudes"] = db.session.query(SolicitudAyudaModel).filter_by(paciente_id=u.id).count()
        data["objetivo"] = {
            "calorias_meta": round(u.objetivo.calorias_meta, 1),
            "proteina_meta": round(u.objetivo.proteina_meta, 1),
        } if u.objetivo else None
        resultado.append(data)
    return jsonify(resultado), 200


@admin_bp.route('/usuarios', methods=['POST'])
@requerir_rol("admin")
def crear_usuario_admin():
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get("nombre") or "").strip()
    password = datos.get("password") or ""
    rol = (datos.get("rol") or "usuario").strip().lower()

    if len(nombre) < 2 or len(password) < 4:
        return jsonify({"error": "Nombre (mín. 2 caracteres) y contraseña (mín. 4) son obligatorios"}), 400
    if rol not in ROLES_VALIDOS:
        return jsonify({"error": f"Rol no válido. Usa: {', '.join(sorted(ROLES_VALIDOS))}"}), 400
    if db.session.query(UsuarioModel).filter_by(nombre=nombre).first():
        return jsonify({"error": f"El usuario '{nombre}' ya existe"}), 400

    nuevo = UsuarioModel(
        nombre=nombre,
        password_hash=generate_password_hash(password),
        rol=rol,
        preferencias=datos.get("preferencias"),
        email=datos.get("email"),
        edad=int(datos["edad"]) if datos.get("edad") not in (None, "") else None,
        peso_kg=float(datos["peso_kg"]) if datos.get("peso_kg") not in (None, "") else None,
        altura_cm=float(datos["altura_cm"]) if datos.get("altura_cm") not in (None, "") else None,
        telefono=datos.get("telefono"),
    )
    db.session.add(nuevo)
    db.session.flush()

    if rol == "usuario":
        db.session.add(ObjetivoNutricionalModel(
            usuario_id=nuevo.id,
            calorias_meta=2000.0,
            proteina_meta=120.0
        ))

    db.session.commit()
    return jsonify({
        "mensaje": f"Usuario '{nombre}' creado con rol '{rol}'",
        "usuario": serializar_usuario(nuevo)
    }), 201


@admin_bp.route('/usuarios/<int:usuario_id>/rol', methods=['PUT'])
@requerir_rol("admin")
def cambiar_rol_usuario(usuario_id: int):
    admin_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    datos = request.get_json(silent=True) or {}
    nuevo_rol = (datos.get("rol") or "").strip().lower()
    if nuevo_rol not in ROLES_VALIDOS:
        return jsonify({"error": f"Rol inválido. Usa: {', '.join(sorted(ROLES_VALIDOS))}"}), 400

    if usuario.id == admin_id and nuevo_rol != "admin":
        return jsonify({"error": "No puedes quitarte el rol de administrador a ti mismo"}), 400

    usuario.rol = nuevo_rol
    db.session.commit()
    return jsonify({
        "mensaje": f"Rol de '{usuario.nombre}' actualizado a '{nuevo_rol}'",
        "usuario": serializar_usuario(usuario)
    }), 200


@admin_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
@requerir_rol("admin")
def eliminar_usuario(usuario_id: int):
    admin_id = int(get_jwt_identity())
    if usuario_id == admin_id:
        return jsonify({"error": "No puedes eliminar tu propia cuenta de administrador"}), 400

    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"mensaje": f"Usuario '{usuario.nombre}' eliminado"}), 200


@admin_bp.route('/usuarios/<int:usuario_id>/detalle', methods=['GET'])
@requerir_rol("admin")
def detalle_completo_usuario(usuario_id: int):
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    resumen_calorias = construir_resumen_usuario(usuario, "calorias")
    resumen_macros = construir_resumen_usuario(usuario, "macros")
    resumen_alertas = construir_resumen_usuario(usuario, "azucar_sodio")

    registros = (
        db.session.query(RegistroConsumoModel)
        .filter_by(usuario_id=usuario.id)
        .order_by(RegistroConsumoModel.fecha.desc())
        .all()
    )
    solicitudes = (
        db.session.query(SolicitudAyudaModel)
        .filter((SolicitudAyudaModel.paciente_id == usuario.id) | (SolicitudAyudaModel.doctor_id == usuario.id))
        .order_by(SolicitudAyudaModel.fecha_actualizacion.desc())
        .all()
    )

    return jsonify({
        "datos_personales": serializar_usuario(usuario),
        "resumen": resumen_calorias,
        "resumenes": {
            "calorias": resumen_calorias["resultado"],
            "macros": resumen_macros["resultado"],
            "azucar_sodio": resumen_alertas["resultado"],
        },
        "registros": [serializar_registro_consumo(r) for r in registros],
        "solicitudes": [_serializar_solicitud(s) for s in solicitudes],
    }), 200


@admin_bp.route('/registros', methods=['GET'])
@requerir_rol("admin")
def listar_todos_registros():
    registros = (
        db.session.query(RegistroConsumoModel)
        .order_by(RegistroConsumoModel.fecha.desc())
        .limit(200)
        .all()
    )
    resultado = []
    for r in registros:
        item = serializar_registro_consumo(r)
        item["usuario_nombre"] = r.usuario.nombre if r.usuario else "Desconocido"
        item["usuario_rol"] = r.usuario.rol if r.usuario else "usuario"
        resultado.append(item)
    return jsonify(resultado), 200
