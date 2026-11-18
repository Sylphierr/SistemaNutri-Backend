from .componente_comida import IComponenteComida
from .nutrientes import Nutrientes
from .orm_models import RegistroConsumoModel

"""
@author Armando Imanol Aguilar Espiricueto
"""

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
            sodio=self._registro.sodio_total,
        )

    def GetDescripcionIngredientes(self) -> str:
        raw_ing = (getattr(self._registro, "ingredientes_consumidos", None) or "").strip()
        return raw_ing if raw_ing else "Ingrediente único"
