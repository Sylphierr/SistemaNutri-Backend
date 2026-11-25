from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models.orm_models import UsuarioModel, SolicitudAyudaModel, MensajeChatModel
from routes.auth import requerir_rol, serializar_usuario

ayuda_bp = Blueprint('ayuda', __name__, url_prefix='/api/ayuda')


def _serializar_solicitud(sol: SolicitudAyudaModel) -> dict:
    ultimo = sol.mensajes[-1] if sol.mensajes else None
    return {
        "id": sol.id,
        "paciente_id": sol.paciente_id,
        "paciente_nombre": sol.paciente.nombre if sol.paciente else "",
        "doctor_id": sol.doctor_id,
        "doctor_nombre": sol.doctor.nombre if sol.doctor else None,
        "motivo": sol.motivo,
        "estado": sol.estado,
        "fecha_creacion": sol.fecha_creacion.isoformat() if sol.fecha_creacion else None,
        "fecha_actualizacion": sol.fecha_actualizacion.isoformat() if sol.fecha_actualizacion else None,
        "total_mensajes": len(sol.mensajes),
        "ultimo_mensaje": ultimo.contenido if ultimo else None,
    }


def _serializar_mensaje(msg: MensajeChatModel) -> dict:
    return {
        "id": msg.id,
        "solicitud_id": msg.solicitud_id,
        "remitente_id": msg.remitente_id,
        "remitente_nombre": msg.remitente.nombre if msg.remitente else "",
        "remitente_rol": msg.remitente.rol if msg.remitente else "usuario",
        "contenido": msg.contenido,
        "fecha_envio": msg.fecha_envio.isoformat() if msg.fecha_envio else None,
        "leido": msg.leido,
    }


def _usuario_puede_acceder_solicitud(usuario: UsuarioModel, sol: SolicitudAyudaModel) -> bool:
    if usuario.rol == "admin":
        return True
    if usuario.rol == "usuario":
        return sol.paciente_id == usuario.id
    if usuario.rol == "doctor":
        return sol.doctor_id is None or sol.doctor_id == usuario.id
    return False


@ayuda_bp.route('/doctores', methods=['GET'])
@jwt_required()
def listar_doctores():
    doctores = db.session.query(UsuarioModel).filter_by(rol="doctor").order_by(UsuarioModel.nombre).all()
    return jsonify([serializar_usuario(d) for d in doctores]), 200


@ayuda_bp.route('/solicitudes', methods=['POST'])
@requerir_rol("usuario")
def crear_solicitud_ayuda():
    usuario_id = int(get_jwt_identity())
    datos = request.get_json(silent=True) or {}
    motivo = (datos.get("motivo") or "").strip()
    doctor_id = datos.get("doctor_id")

    if len(motivo) < 3:
        return jsonify({"error": "Describe brevemente el motivo de tu consulta (mín. 3 caracteres)"}), 400

    doctor_asignado = None
    if doctor_id is not None:
        doctor = db.session.get(UsuarioModel, int(doctor_id))
        if not doctor or doctor.rol != "doctor":
            return jsonify({"error": "El doctor seleccionado no es válido"}), 404
        doctor_asignado = doctor.id

    nueva_sol = SolicitudAyudaModel(
        paciente_id=usuario_id,
        doctor_id=doctor_asignado,
        motivo=motivo,
        estado="en_atencion" if doctor_asignado else "pendiente"
    )
    db.session.add(nueva_sol)
    db.session.flush()

    # Primer mensaje automático con el motivo de ayuda
    primer_mensaje = MensajeChatModel(
        solicitud_id=nueva_sol.id,
        remitente_id=usuario_id,
        contenido=motivo
    )
    db.session.add(primer_mensaje)
    db.session.commit()

    return jsonify({
        "mensaje": "Solicitud de ayuda enviada al doctor.",
        "solicitud": _serializar_solicitud(nueva_sol)
    }), 201


@ayuda_bp.route('/solicitudes', methods=['GET'])
@jwt_required()
def listar_solicitudes():
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    query = db.session.query(SolicitudAyudaModel)
    if usuario.rol == "usuario":
        query = query.filter_by(paciente_id=usuario.id)
    elif usuario.rol == "doctor":
        query = query.filter(
            (SolicitudAyudaModel.doctor_id == usuario.id) | (SolicitudAyudaModel.doctor_id.is_(None))
        )

    solicitudes = query.order_by(SolicitudAyudaModel.fecha_actualizacion.desc()).all()
    return jsonify([_serializar_solicitud(s) for s in solicitudes]), 200


@ayuda_bp.route('/solicitudes/<int:solicitud_id>/mensajes', methods=['GET'])
@jwt_required()
def obtener_mensajes(solicitud_id: int):
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    sol = db.session.get(SolicitudAyudaModel, solicitud_id)
    if not usuario or not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404

    if not _usuario_puede_acceder_solicitud(usuario, sol):
        return jsonify({"error": "No tienes permisos para ver este chat"}), 403

    # Marcar como leídos los mensajes de la otra parte
    hubo_cambios = False
    for msg in sol.mensajes:
        if msg.remitente_id != usuario.id and not msg.leido:
            msg.leido = True
            hubo_cambios = True
    if hubo_cambios:
        db.session.commit()

    return jsonify({
        "solicitud": _serializar_solicitud(sol),
        "mensajes": [_serializar_mensaje(m) for m in sol.mensajes]
    }), 200


@ayuda_bp.route('/solicitudes/<int:solicitud_id>/mensajes', methods=['POST'])
@jwt_required()
def enviar_mensaje(solicitud_id: int):
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    sol = db.session.get(SolicitudAyudaModel, solicitud_id)
    if not usuario or not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404

    if not _usuario_puede_acceder_solicitud(usuario, sol):
        return jsonify({"error": "No tienes permisos para enviar mensajes en este chat"}), 403

    datos = request.get_json(silent=True) or {}
    contenido = (datos.get("contenido") or "").strip()
    if not contenido:
        return jsonify({"error": "El mensaje no puede estar vacío"}), 400

    # Si un doctor responde a una solicitud pendiente, se la asigna automáticamente
    if usuario.rol == "doctor" and sol.doctor_id is None:
        sol.doctor_id = usuario.id
        sol.estado = "en_atencion"
    elif sol.estado == "cerrada":
        sol.estado = "en_atencion"

    sol.fecha_actualizacion = datetime.now(timezone.utc)

    nuevo_msg = MensajeChatModel(
        solicitud_id=sol.id,
        remitente_id=usuario.id,
        contenido=contenido
    )
    db.session.add(nuevo_msg)
    db.session.commit()

    return jsonify({
        "mensaje": "Mensaje enviado",
        "data": _serializar_mensaje(nuevo_msg)
    }), 201


@ayuda_bp.route('/solicitudes/<int:solicitud_id>/estado', methods=['PUT'])
@jwt_required()
def cambiar_estado_solicitud(solicitud_id: int):
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    sol = db.session.get(SolicitudAyudaModel, solicitud_id)
    if not usuario or not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404

    if not _usuario_puede_acceder_solicitud(usuario, sol):
        return jsonify({"error": "No tienes permisos para modificar esta solicitud"}), 403

    datos = request.get_json(silent=True) or {}
    nuevo_estado = datos.get("estado")
    if nuevo_estado not in {"pendiente", "en_atencion", "cerrada"}:
        return jsonify({"error": "Estado no válido. Usa pendiente, en_atencion o cerrada"}), 400

    sol.estado = nuevo_estado
    sol.fecha_actualizacion = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "mensaje": "Estado actualizado",
        "solicitud": _serializar_solicitud(sol)
    }), 200
