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


class VeganoDecorator(PlatilloDecorator):
    def GetNombre(self) -> str:
        return f"{super().GetNombre()} (Vegano)"