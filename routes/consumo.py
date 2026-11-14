# routes/consumo.py
from flask import Blueprint, request, jsonify
from pydantic import BaseModel, Field, ValidationError  # <-- Importaciones de Pydantic
from database import db
from models.orm_models import UsuarioModel, CatalogoAlimentoModel, RegistroConsumoModel
from models.factories import ProteinaFactory, FrutaFactory, VerduraFactory
from models.seguimiento import SeguimientoConsumo, RegistroConsumo, NotificadorPendientes, NotificadorObjetivos
from models.nutrientes import Nutrientes
from models.estrategias import AnalizadorNutricional, CaloriasStrategy, MacronutrientesStrategy
from models.componente_comida import IComponenteComida

# Instanciamos el Blueprint (equivalente a APIRouter)
consumo_bp = Blueprint('consumo', __name__, url_prefix='/api/consumo')

# Instanciamos nuestro Sujeto del patrón Observer
sistema_seguimiento = SeguimientoConsumo()

sistema_seguimiento.Suscribir(NotificadorPendientes())
sistema_seguimiento.Suscribir(NotificadorObjetivos())

# --- 1. DTO de Pydantic para Validar Entradas ---
class CrearRegistroDTO(BaseModel):
    usuario_id: int = Field(..., gt=0, description="El ID del usuario debe ser un entero positivo")
    alimento: str = Field(..., min_length=2, max_length=100, description="Nombre del alimento")


# --- 2. Adaptador (Corregido: movido fuera de la ruta y con indentación correcta) ---
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


# --- 3. Rutas (Endpoints) ---
@consumo_bp.route('/registrar', methods=['POST'])
def registrar_consumo():
    # A. Validar con Pydantic
    try:
        json_data = request.get_json() or {}
        datos_validados = CrearRegistroDTO.model_validate(json_data)
    except ValidationError as e:
        return jsonify({
            "error": "Datos de entrada inválidos",
            "detalles": e.errors()
        }), 400

    # Usar los datos tipados y validados
    usuario_id = datos_validados.usuario_id
    nombre_alimento = datos_validados.alimento

    # B. Validar existencia en BD
    usuario = db.session.get(UsuarioModel, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    alimento_db = db.session.query(CatalogoAlimentoModel).filter_by(nombre=nombre_alimento).first()
    if not alimento_db:
        return jsonify({"error": "Alimento no disponible en el catálogo"}), 404

    # C. Patrón Factory
    nutrientes_bd = Nutrientes(
        calorias=alimento_db.calorias, proteina=alimento_db.proteina,
        carbohidratos=alimento_db.carbohidratos, grasas=alimento_db.grasas,
        azucar=alimento_db.azucar, sodio=alimento_db.sodio
    )

    if alimento_db.tipo_factory == "Proteina":
        fabrica = ProteinaFactory()
    elif alimento_db.tipo_factory == "Fruta":
        fabrica = FrutaFactory()
    else:
        fabrica = VerduraFactory()

    alimento_dominio = fabrica.CrearAlimento(alimento_db.nombre)
    alimento_dominio._nutrientes = nutrientes_bd 

    # D. Patrón Observer
    registro_memoria = RegistroConsumo(alimento_dominio)
    sistema_seguimiento.RegistrarConsumo(registro_memoria) 

    # E. Persistencia en BD
    nuevo_registro_db = RegistroConsumoModel(
        usuario_id=usuario.id,
        nombre_consumido=alimento_dominio.GetNombre(),
        calorias_totales=alimento_dominio.GetCalorias(),
        proteina_total=alimento_dominio.GetNutrientes().proteina,
        carbohidratos_total=alimento_dominio.GetNutrientes().carbohidratos,
        grasas_total=alimento_dominio.GetNutrientes().grasas,
        azucar_total=alimento_dominio.GetNutrientes().azucar,
        sodio_total=alimento_dominio.GetNutrientes().sodio
    )
    
    db.session.add(nuevo_registro_db)
    db.session.commit()

    return jsonify({
        "mensaje": f"Consumo de {alimento_dominio.GetNombre()} registrado exitosamente.",
        "calorias_agregadas": alimento_dominio.GetCalorias()
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
    else:
        estrategia = CaloriasStrategy()
        tipo_resultado = "Total de Calorías (kcal)"

    analizador = AnalizadorNutricional(estrategia)
    resultado = analizador.Analizar(registros_dominio)

    return jsonify({
        "usuario": usuario.nombre,
        "registros_analizados": len(registros_dominio),
        "estrategia_aplicada": tipo_reporte,
        "resultado": {
            tipo_resultado: resultado
        },
        "historial": [r.nombre_consumido for r in registros_db]
    }), 200