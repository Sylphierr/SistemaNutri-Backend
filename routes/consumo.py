# routes/consumo.py
from flask import Blueprint, request, jsonify
from pydantic import BaseModel, Field, ValidationError
from database import db
from models.orm_models import UsuarioModel, CatalogoAlimentoModel, RegistroConsumoModel
from models.factories import (
    ProteinaFactory,
    FrutaFactory,
    VerduraFactory,
    DesayunoFactory,
    ComidaFactory,
)
from models.seguimiento import SeguimientoConsumo, RegistroConsumo, NotificadorPendientes, NotificadorObjetivos
from models.nutrientes import Nutrientes
from models.estrategias import (
    AnalizadorNutricional,
    CaloriasStrategy,
    MacronutrientesStrategy,
    AzucarSodioStrategy,
)
from models.componente_comida import IComponenteComida
from models.platillo_decorator import VeganoDecorator
from models.dominio import ObjetivoNutricional, ComparadorHabitos, Recomendacion

# Instanciamos el Blueprint (equivalente a APIRouter)
consumo_bp = Blueprint('consumo', __name__, url_prefix='/api/consumo')

# Instanciamos nuestro Sujeto del patrón Observer
sistema_seguimiento = SeguimientoConsumo()

sistema_seguimiento.Suscribir(NotificadorPendientes())
sistema_seguimiento.Suscribir(NotificadorObjetivos())

# --- 1. DTO de Pydantic para Validar Entradas ---
class CrearRegistroDTO(BaseModel):
    usuario_id: int = Field(..., gt=0, description="El ID del usuario debe ser un entero positivo")
    alimentos: list[str] = Field(..., min_length=1, description="Lista de nombres de alimentos consumidos")
    tipo_platillo: str = Field(default="comida", description="Tipo de platillo para la fábrica: 'desayuno' o 'comida'")
    es_vegano: bool = Field(default=False, description="Indica si el platillo o alimento se decora como vegano")

class CrearAlimentoDTO(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre del nuevo alimento")
    grupo: str = Field(..., description="Grupo: 'Proteina', 'Fruta' o 'Verdura'")

# --- 2. Adaptador ---
class AdaptadorRegistroDB(IComponenteComida):
    def __init__(self, registro_db: RegistroConsumoModel):
        self._registro = registro_db

    def GetNombre(self) -> str:
        return self._registro.nombre_consumido

    def GetCalorias(self) -> float:
        return self._registro.calorias_totales

    def GetNutrientes(self) -> Nutrientes:
        return Nutrientes(
            calorias=self._registro.calorias_totales,
            proteina=self._registro.proteina_total,
            carbohidratos=self._registro.carbohidratos_total,
            grasas=self._registro.grasas_total,
            azucar=self._registro.azucar_total,
            sodio=self._registro.sodio_total
        )


def _crear_alimento_desde_bd(alimento_db: CatalogoAlimentoModel):
    nutrientes_bd = Nutrientes(
        calorias=alimento_db.calorias,
        proteina=alimento_db.proteina,
        carbohidratos=alimento_db.carbohidratos,
        grasas=alimento_db.grasas,
        azucar=alimento_db.azucar,
        sodio=alimento_db.sodio,
    )

    if alimento_db.tipo_factory == "Proteina":
        fabrica = ProteinaFactory()
    elif alimento_db.tipo_factory == "Fruta":
        fabrica = FrutaFactory()
    else:
        fabrica = VerduraFactory()

    return fabrica.CrearAlimento(alimento_db.nombre, nutrientes_bd)


# --- 3. Rutas (Endpoints) ---
@consumo_bp.route('/registrar', methods=['POST'])
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

    usuario_id = datos_validados.usuario_id

    # B. Validar existencia de usuario en BD
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # C. Patrón Factory y Patrón Composite
    componentes_creados = []
    for nombre_alimento in datos_validados.alimentos:
        alimento_db = db.session.query(CatalogoAlimentoModel).filter_by(nombre=nombre_alimento).first()
        if not alimento_db:
            return jsonify({"error": f"Alimento '{nombre_alimento}' no disponible en el catálogo"}), 404

        alimento_dominio = _crear_alimento_desde_bd(alimento_db)
        componentes_creados.append(alimento_dominio)

    if len(componentes_creados) == 1:
        componente_base: IComponenteComida = componentes_creados[0]
    else:
        if datos_validados.tipo_platillo.lower() == "desayuno":
            fabrica_platillo = DesayunoFactory()
        else:
            fabrica_platillo = ComidaFactory()

        platillo = fabrica_platillo.CrearPlatillo()
        for comp in componentes_creados:
            platillo.Agregar(comp)
        componente_base = platillo

    # D. Patrón Decorator
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


@consumo_bp.route('/usuario/<int:usuario_id>/reporte', methods=['GET'])
def reporte_consumo(usuario_id):
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    registros_db = db.session.query(RegistroConsumoModel).filter_by(usuario_id=usuario_id).all()

    registros_dominio = []
    for reg_db in registros_db:
        componente_adaptado = AdaptadorRegistroDB(reg_db)
        registros_dominio.append(RegistroConsumo(componente_adaptado))

    tipo_reporte = request.args.get('tipo', 'calorias')

    # Patrón Strategy
    if tipo_reporte == 'macros':
        estrategia = MacronutrientesStrategy()
        tipo_resultado = "Desglose de Macronutrientes"
    elif tipo_reporte == 'azucar_sodio':
        estrategia = AzucarSodioStrategy()
        tipo_resultado = "Desglose de Azúcar y Sodio"
    else:
        estrategia = CaloriasStrategy()
        tipo_resultado = "Total de Calorías (kcal)"

    analizador = AnalizadorNutricional(estrategia)
    resultado = analizador.Analizar(registros_dominio)

    # Integración con entidades de Dominio
    evaluacion_habitos = "Sin objetivo nutricional configurado para este usuario."
    if usuario.objetivo:
        objetivo_dominio = ObjetivoNutricional(
            caloriasMeta=usuario.objetivo.calorias_meta,
            proteinaMeta=usuario.objetivo.proteina_meta
        )
        comparador = ComparadorHabitos()
        evaluacion_habitos = comparador.Comparar(registros_dominio, objetivo_dominio)

    aviso_legal = Recomendacion().AvisoLegal()

    return jsonify({
        "usuario": usuario.nombre,
        "registros_analizados": len(registros_dominio),
        "estrategia_aplicada": tipo_reporte,
        "resultado": {
            tipo_resultado: resultado
        },
        "evaluacion_objetivo": evaluacion_habitos,
        "aviso_legal": aviso_legal,
        "historial": [r.nombre_consumido for r in registros_db]
    }), 200

@consumo_bp.route('/alimento/personalizado', methods=['POST'])
def crear_alimento_personalizado():
    try:
        json_data = request.get_json(silent=True) or {}
        datos = CrearAlimentoDTO.model_validate(json_data)
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "detalles": e.errors()}), 400

    # 1. Normalizamos el grupo para que coincida con las fábricas
    grupo_normalizado = datos.grupo.capitalize()

    # 2. Verificamos que el alimento no exista ya en la base de datos
    existe = db.session.query(CatalogoAlimentoModel).filter_by(nombre=datos.nombre).first()
    if existe:
        return jsonify({"error": f"El alimento '{datos.nombre}' ya existe."}), 400

    # 3. Disparamos el Patrón Factory según el grupo
    if grupo_normalizado == "Proteina":
        fabrica = ProteinaFactory()
    elif grupo_normalizado == "Fruta":
        fabrica = FrutaFactory()
    elif grupo_normalizado == "Verdura":
        fabrica = VerduraFactory()
    else:
        return jsonify({"error": "Grupo no válido. Usa Proteina, Fruta o Verdura"}), 400

    # 4. Creamos el alimento en memoria (la fábrica le asigna los nutrientes por defecto)
    alimento_dominio = fabrica.CrearAlimento(datos.nombre)
    nutrientes = alimento_dominio.GetNutrientes()

    # 5. Lo persistimos en el catálogo para futuras consultas
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