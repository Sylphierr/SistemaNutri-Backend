from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from database import db
from models.orm_models import UsuarioModel, RegistroConsumoModel, SolicitudAyudaModel
from models.reporte_helper import construir_resumen_usuario, serializar_registro_consumo
from routes.auth import requerir_rol, serializar_usuario
from routes.ayuda import _serializar_solicitud

doctor_bp = Blueprint('doctor', __name__, url_prefix='/api/doctor')


def _doctor_tiene_acceso_paciente(doctor_id: int, paciente_id: int) -> bool:
    """Un doctor solo puede acceder a pacientes que solicitaron ayuda (asignados a él o sin asignar)."""
    solicitud = db.session.query(SolicitudAyudaModel).filter(
        SolicitudAyudaModel.paciente_id == paciente_id,
        (SolicitudAyudaModel.doctor_id == doctor_id) | (SolicitudAyudaModel.doctor_id.is_(None))
    ).first()
    return solicitud is not None


@doctor_bp.route('/pacientes', methods=['GET'])
@requerir_rol("doctor", "admin")
def listar_pacientes_con_solicitud():
    usuario_id = int(get_jwt_identity())
    usuario_actual = db.session.get(UsuarioModel, usuario_id)

    query = db.session.query(SolicitudAyudaModel)
    if usuario_actual.rol == "doctor":
        query = query.filter(
            (SolicitudAyudaModel.doctor_id == usuario_actual.id) | (SolicitudAyudaModel.doctor_id.is_(None))
        )

    solicitudes = query.order_by(SolicitudAyudaModel.fecha_actualizacion.desc()).all()

    pacientes_map = {}
    for sol in solicitudes:
        pac = sol.paciente
        if not pac:
            continue
        if pac.id not in pacientes_map:
            total_reg = db.session.query(RegistroConsumoModel).filter_by(usuario_id=pac.id).count()
            pacientes_map[pac.id] = {
                "paciente": serializar_usuario(pac),
                "total_registros": total_reg,
                "objetivo": {
                    "calorias_meta": round(pac.objetivo.calorias_meta, 1),
                    "proteina_meta": round(pac.objetivo.proteina_meta, 1),
                } if pac.objetivo else None,
                "ultima_solicitud": _serializar_solicitud(sol),
            }

    return jsonify(list(pacientes_map.values())), 200


@doctor_bp.route('/pacientes/<int:paciente_id>', methods=['GET'])
@requerir_rol("doctor", "admin")
def detalle_paciente(paciente_id: int):
    usuario_id = int(get_jwt_identity())
    usuario_actual = db.session.get(UsuarioModel, usuario_id)
    paciente = db.session.get(UsuarioModel, paciente_id)

    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404

    if usuario_actual.rol == "doctor" and not _doctor_tiene_acceso_paciente(usuario_actual.id, paciente_id):
        return jsonify({
            "error": "Acceso denegado: este usuario no ha solicitado ayuda médica."
        }), 403

    tipo_reporte = request.args.get("tipo", "calorias")
    resumen_calorias = construir_resumen_usuario(paciente, "calorias")
    resumen_macros = construir_resumen_usuario(paciente, "macros")
    resumen_alertas = construir_resumen_usuario(paciente, "azucar_sodio")
    resumen_seleccionado = construir_resumen_usuario(paciente, tipo_reporte)

    registros = (
        db.session.query(RegistroConsumoModel)
        .filter_by(usuario_id=paciente.id)
        .order_by(RegistroConsumoModel.fecha.desc())
        .all()
    )

    solicitudes_q = db.session.query(SolicitudAyudaModel).filter_by(paciente_id=paciente.id)
    if usuario_actual.rol == "doctor":
        solicitudes_q = solicitudes_q.filter(
            (SolicitudAyudaModel.doctor_id == usuario_actual.id) | (SolicitudAyudaModel.doctor_id.is_(None))
        )
    solicitudes = solicitudes_q.order_by(SolicitudAyudaModel.fecha_actualizacion.desc()).all()

    return jsonify({
        "datos_personales": serializar_usuario(paciente),
        "resumen": resumen_seleccionado,
        "resumenes": {
            "calorias": resumen_calorias["resultado"],
            "macros": resumen_macros["resultado"],
            "azucar_sodio": resumen_alertas["resultado"],
        },
        "registros": [serializar_registro_consumo(r) for r in registros],
        "solicitudes": [_serializar_solicitud(s) for s in solicitudes],
    }), 200


@doctor_bp.route('/solicitudes/<int:solicitud_id>/atender', methods=['POST'])
@requerir_rol("doctor")
def atender_solicitud(solicitud_id: int):
    doctor_id = int(get_jwt_identity())
    sol = db.session.get(SolicitudAyudaModel, solicitud_id)
    if not sol:
        return jsonify({"error": "Solicitud no encontrada"}), 404

    if sol.doctor_id is not None and sol.doctor_id != doctor_id:
        return jsonify({"error": "Esta solicitud ya está siendo atendida por otro doctor"}), 409

    sol.doctor_id = doctor_id
    sol.estado = "en_atencion"
    sol.fecha_actualizacion = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "mensaje": "Solicitud asignada exitosamente",
        "solicitud": _serializar_solicitud(sol)
    }), 200
