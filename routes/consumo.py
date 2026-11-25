# routes/consumo.py
from typing import Union
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import BaseModel, Field, ValidationError
from database import db
from models.orm_models import (
    UsuarioModel,
    ObjetivoNutricionalModel,
    CatalogoAlimentoModel,
    RegistroConsumoModel,
)
from models.factories import (
    VerduraFactory,
    ComidaFactory,
    FABRICAS_ALIMENTO,
    FABRICAS_PLATILLO,
)
from models.seguimiento import SeguimientoConsumo, RegistroConsumo, NotificadorPendientes, NotificadorObjetivos
from models.nutrientes import Nutrientes
from models.estrategias import (
    AnalizadorNutricional,
    CaloriasStrategy,
    ESTRATEGIAS_REPORTE,
)
from models.componente_comida import IComponenteComida
from models.platillo_decorator import VeganoDecorator, PorcionDecorator
from models.reporte_helper import construir_resumen_usuario

# Instanciamos el Blueprint (equivalente a APIRouter)
consumo_bp = Blueprint('consumo', __name__, url_prefix='/api/consumo')

# Instanciamos nuestro Sujeto del patrón Observer
sistema_seguimiento = SeguimientoConsumo()

sistema_seguimiento.Suscribir(NotificadorPendientes())
sistema_seguimiento.Suscribir(NotificadorObjetivos())

# --- 1. DTOs de Pydantic para Validar Entradas ---
class IngredientePorcionDTO(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre del alimento en el catálogo")
    gramos: float = Field(default=100.0, gt=0, description="Cantidad en gramos del alimento")

class CrearRegistroDTO(BaseModel):
    alimentos: list[Union[IngredientePorcionDTO, str]] = Field(
        ...,
        min_length=1,
        description="Lista de alimentos (objetos con nombre y gramos, o nombres en string)"
    )
    tipo_platillo: str = Field(
        default="comida",
        description="Tipo de platillo para la fábrica: 'desayuno', 'comida', 'cena' o 'merienda'"
    )
    es_vegano: bool = Field(default=False, description="Indica si el platillo o alimento se decora como vegano")

class CrearAlimentoDTO(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre del nuevo alimento")
    grupo: str = Field(..., description="Grupo: 'Proteina', 'Fruta', 'Verdura' o 'Leguminosa'")

class ActualizarObjetivoDTO(BaseModel):
    calorias_meta: float = Field(..., gt=0, description="Meta diaria de calorías (kcal)")
    proteina_meta: float = Field(..., gt=0, description="Meta diaria de proteína (g)")


def _crear_alimento_desde_bd(alimento_db: CatalogoAlimentoModel):
    nutrientes_bd = Nutrientes(
        calorias=alimento_db.calorias,
        proteina=alimento_db.proteina,
        carbohidratos=alimento_db.carbohidratos,
        grasas=alimento_db.grasas,
        azucar=alimento_db.azucar,
        sodio=alimento_db.sodio,
    )

    clase_fabrica = FABRICAS_ALIMENTO.get(alimento_db.tipo_factory, VerduraFactory)
    return clase_fabrica().CrearAlimento(alimento_db.nombre, nutrientes_bd)


# --- 2. Rutas (Endpoints) ---
@consumo_bp.route('/registrar', methods=['POST'])
@jwt_required()
def registrar_consumo():
    # A. Validar con Pydantic
    try:
        json_data = request.get_json(silent=True) or {}
        datos_validados = CrearRegistroDTO.model_validate(json_data)
    except ValidationError as e:
        return jsonify({
            "error": "Datos de entrada inválidos",
            "detalles": e.errors()
        }), 400

    usuario_id = int(get_jwt_identity())

    # B. Validar existencia de usuario en BD
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # C. Patrón Factory, Patrón Decorator (PorcionDecorator) y Patrón Composite
    componentes_creados = []
    for item_alimento in datos_validados.alimentos:
        if isinstance(item_alimento, str):
            nombre_alimento = item_alimento
            gramos = 100.0
        else:
            nombre_alimento = item_alimento.nombre
            gramos = item_alimento.gramos

        alimento_db = db.session.query(CatalogoAlimentoModel).filter_by(nombre=nombre_alimento).first()
        if not alimento_db:
            return jsonify({"error": f"Alimento '{nombre_alimento}' no disponible en el catálogo"}), 404

        alimento_dominio = _crear_alimento_desde_bd(alimento_db)
        alimento_porcionado = PorcionDecorator(alimento_dominio, gramos)
        componentes_creados.append(alimento_porcionado)

    if len(componentes_creados) == 1:
        componente_base: IComponenteComida = componentes_creados[0]
    else:
        clase_fabrica_platillo = FABRICAS_PLATILLO.get(
            datos_validados.tipo_platillo.lower(),
            ComidaFactory
        )
        platillo = clase_fabrica_platillo().CrearPlatillo()
        for comp in componentes_creados:
            platillo.Agregar(comp)
        componente_base = platillo

    # D. Patrón Decorator (Vegano)
    if datos_validados.es_vegano:
        componente_final: IComponenteComida = VeganoDecorator(componente_base)
    else:
        componente_final = componente_base

    # E. Patrón Observer
    registro_memoria = RegistroConsumo(componente_final)
    sistema_seguimiento.RegistrarConsumo(registro_memoria, usuario.id)

    # F. Persistencia en BD
    nutrientes_finales = componente_final.GetNutrientes()
    nuevo_registro_db = RegistroConsumoModel(
        usuario_id=usuario.id,
        nombre_consumido=componente_final.GetNombre(),
        ingredientes_consumidos=componente_final.GetDescripcionIngredientes(),
        calorias_totales=componente_final.GetCalorias(),
        proteina_total=nutrientes_finales.proteina,
        carbohidratos_total=nutrientes_finales.carbohidratos,
        grasas_total=nutrientes_finales.grasas,
        azucar_total=nutrientes_finales.azucar,
        sodio_total=nutrientes_finales.sodio
    )

    db.session.add(nuevo_registro_db)
    db.session.commit()

    return jsonify({
        "mensaje": f"Consumo de {componente_final.GetNombre()} registrado exitosamente.",
        "calorias_agregadas": componente_final.GetCalorias()
    }), 201


@consumo_bp.route('/reporte', methods=['GET'])
@consumo_bp.route('/usuario/<int:usuario_id>/reporte', methods=['GET'])
@jwt_required()
def reporte_consumo(usuario_id=None):
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    tipo_reporte = request.args.get('tipo', 'calorias')
    resumen = construir_resumen_usuario(usuario, tipo_reporte)
    return jsonify(resumen), 200


@consumo_bp.route('/objetivo', methods=['PUT'])
@consumo_bp.route('/usuario/<int:usuario_id>/objetivo', methods=['PUT'])
@jwt_required()
def actualizar_objetivo_usuario(usuario_id=None):
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    try:
        json_data = request.get_json(silent=True) or {}
        datos = ActualizarObjetivoDTO.model_validate(json_data)
    except ValidationError as e:
        return jsonify({"error": "Datos de objetivo inválidos", "detalles": e.errors()}), 400

    if usuario.objetivo:
        usuario.objetivo.calorias_meta = round(datos.calorias_meta, 1)
        usuario.objetivo.proteina_meta = round(datos.proteina_meta, 1)
    else:
        nuevo_obj = ObjetivoNutricionalModel(
            usuario_id=usuario.id,
            calorias_meta=round(datos.calorias_meta, 1),
            proteina_meta=round(datos.proteina_meta, 1),
        )
        db.session.add(nuevo_obj)

    db.session.commit()
    return jsonify({
        "mensaje": "Objetivo nutricional actualizado correctamente.",
        "calorias_meta": round(datos.calorias_meta, 1),
        "proteina_meta": round(datos.proteina_meta, 1),
    }), 200


@consumo_bp.route('/alimento/personalizado', methods=['POST'])
@jwt_required()
def crear_alimento_personalizado():
    try:
        json_data = request.get_json(silent=True) or {}
        datos = CrearAlimentoDTO.model_validate(json_data)
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "detalles": e.errors()}), 400

    grupo_normalizado = datos.grupo.capitalize()

    existe = db.session.query(CatalogoAlimentoModel).filter_by(nombre=datos.nombre).first()
    if existe:
        return jsonify({"error": f"El alimento '{datos.nombre}' ya existe."}), 400

    # Patrón Factory resuelto mediante diccionario (OCP)
    clase_fabrica = FABRICAS_ALIMENTO.get(grupo_normalizado)
    if not clase_fabrica:
        return jsonify({"error": "Grupo no válido. Usa Proteina, Fruta, Verdura o Leguminosa"}), 400

    alimento_dominio = clase_fabrica().CrearAlimento(datos.nombre)
    nutrientes = alimento_dominio.GetNutrientes()

    nuevo_alimento_db = CatalogoAlimentoModel(
        nombre=alimento_dominio.GetNombre(),
        tipo_factory=grupo_normalizado,
        calorias=nutrientes.calorias,
        proteina=nutrientes.proteina,
        carbohidratos=nutrientes.carbohidratos,
        grasas=nutrientes.grasas,
        azucar=nutrientes.azucar,
        sodio=nutrientes.sodio
    )

    db.session.add(nuevo_alimento_db)
    db.session.commit()

    return jsonify({"mensaje": f"Alimento '{datos.nombre}' creado y guardado en el catálogo."}), 201


@consumo_bp.route('/alimentos', methods=['GET'])
@jwt_required()
def obtener_catalogo_alimentos():
    alimentos_db = db.session.query(CatalogoAlimentoModel).order_by(CatalogoAlimentoModel.nombre).all()
    return jsonify([
        {
            "id": a.id,
            "nombre": a.nombre,
            "tipo_factory": a.tipo_factory,
            "calorias": a.calorias,
            "proteina": a.proteina,
            "carbohidratos": a.carbohidratos,
            "grasas": a.grasas,
            "azucar": a.azucar,
            "sodio": a.sodio,
        }
        for a in alimentos_db
    ]), 200