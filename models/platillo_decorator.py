from abc import ABC
from .componente_comida import IComponenteComida
from .nutrientes import Nutrientes

"""
@author Armando Imanol Aguilar Espiricueto
"""

class PlatilloDecorator(IComponenteComida, ABC):
    def __init__(self, componente: IComponenteComida):
        self._componente = componente

    def GetNombre(self) -> str:
        return self._componente.GetNombre()

    def GetCalorias(self) -> float:
        return self._componente.GetCalorias()

    def GetNutrientes(self) -> Nutrientes:
        return self._componente.GetNutrientes()

    def GetDescripcionIngredientes(self) -> str:
        return self._componente.GetDescripcionIngredientes()


class VeganoDecorator(PlatilloDecorator):
    def GetNombre(self) -> str:
        return f"{super().GetNombre()} (Vegano)"


class PorcionDecorator(PlatilloDecorator):
    def __init__(self, componente: IComponenteComida, gramos: float):
        super().__init__(componente)
        self._gramos = gramos
        # Asumimos que los valores en BD son por 100g
        self._multiplicador = gramos / 100.0

    def GetNombre(self) -> str:
        gramos_fmt = int(self._gramos) if float(self._gramos).is_integer() else round(self._gramos, 1)
        return f"{super().GetNombre()} ({gramos_fmt}g)"

    def GetCalorias(self) -> float:
        return round(super().GetCalorias() * self._multiplicador, 1)

    def GetNutrientes(self) -> Nutrientes:
        nutrientes_base = super().GetNutrientes()
        return Nutrientes(
            calorias=round(nutrientes_base.calorias * self._multiplicador, 1),
            proteina=round(nutrientes_base.proteina * self._multiplicador, 1),
            carbohidratos=round(nutrientes_base.carbohidratos * self._multiplicador, 1),
            grasas=round(nutrientes_base.grasas * self._multiplicador, 1),
            azucar=round(nutrientes_base.azucar * self._multiplicador, 1),
            sodio=round(nutrientes_base.sodio * self._multiplicador, 1)
        )