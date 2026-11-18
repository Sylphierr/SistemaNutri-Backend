from .componente_comida import IComponenteComida
from .nutrientes import Nutrientes

"""
@author Armando Imanol Aguilar Espiricueto
"""

class Alimento(IComponenteComida):
    def __init__(self, nombre: str, nutrientes: Nutrientes):
        self._nombre = nombre
        self._nutrientes = nutrientes

    def GetNombre(self) -> str:
        return self._nombre

    def GetCalorias(self) -> float:
        return self._nutrientes.calorias

    def GetNutrientes(self) -> Nutrientes:
        return self._nutrientes

    def GetDescripcionIngredientes(self) -> str:
        return "Ingrediente único"