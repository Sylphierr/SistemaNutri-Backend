from database import db
from models.orm_models import UsuarioModel, RegistroConsumoModel
from models.seguimiento import RegistroConsumo
from models.adaptadores import AdaptadorRegistroDB
from models.estrategias import AnalizadorNutricional, CaloriasStrategy, ESTRATEGIAS_REPORTE
from models.dominio import ObjetivoNutricional, ComparadorHabitos, Recomendacion


def construir_resumen_usuario(usuario: UsuarioModel, tipo_reporte: str = "calorias") -> dict:
    """Construye el resumen nutricional de un usuario usando Strategy y ComparadorHabitos."""
    registros_db = db.session.query(RegistroConsumoModel).filter_by(usuario_id=usuario.id).all()
    registros_dominio = [RegistroConsumo(AdaptadorRegistroDB(reg_db)) for reg_db in registros_db]

    clase_estrategia, tipo_resultado = ESTRATEGIAS_REPORTE.get(
        tipo_reporte,
        (CaloriasStrategy, "Total de Calorías (kcal)")
    )
    analizador = AnalizadorNutricional(clase_estrategia())
    resultado = analizador.Analizar(registros_dominio)

    comparador = ComparadorHabitos()
    evaluacion_habitos = "Sin objetivo nutricional configurado para este usuario."
    objetivo_actual = None
    if usuario.objetivo:
        objetivo_dominio = ObjetivoNutricional(
            caloriasMeta=usuario.objetivo.calorias_meta,
            proteinaMeta=usuario.objetivo.proteina_meta
        )
        evaluacion_habitos = comparador.Comparar(registros_dominio, objetivo_dominio)
        objetivo_actual = {
            "calorias_meta": round(usuario.objetivo.calorias_meta, 1),
            "proteina_meta": round(usuario.objetivo.proteina_meta, 1),
        }

    tendencias = comparador.ObtenerTendencias(registros_dominio)
    aviso_legal = Recomendacion().AvisoLegal()

    return {
        "usuario": usuario.nombre,
        "registros_analizados": len(registros_dominio),
        "estrategia_aplicada": tipo_reporte,
        "resultado": {
            tipo_resultado: resultado
        },
        "objetivo": objetivo_actual,
        "evaluacion_objetivo": evaluacion_habitos,
        "tendencias": tendencias,
        "aviso_legal": aviso_legal
    }


def serializar_registro_consumo(reg: RegistroConsumoModel) -> dict:
    """Serializa un registro de consumo de la base de datos."""
    return {
        "id": reg.id,
        "usuario_id": reg.usuario_id,
        "fecha": reg.fecha.isoformat() if reg.fecha else None,
        "nombre_consumido": reg.nombre_consumido,
        "ingredientes_consumidos": reg.ingredientes_consumidos or "",
        "calorias_totales": round(reg.calorias_totales, 1),
        "proteina_total": round(reg.proteina_total, 1),
        "carbohidratos_total": round(reg.carbohidratos_total, 1),
        "grasas_total": round(reg.grasas_total, 1),
        "azucar_total": round(reg.azucar_total, 1),
        "sodio_total": round(reg.sodio_total, 1),
    }
