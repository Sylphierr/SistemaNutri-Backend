from abc import ABC, abstractmethod
from typing import List
from .seguimiento import RegistroConsumo

"""
@author Armando Imanol Aguilar Espiricueto
"""

class IIndicadorStrategy(ABC):
    @abstractmethod
    def Calcular(self, registros: List[RegistroConsumo]) -> float:
        pass

class CaloriasStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> float:
        return sum(r.componente.GetCalorias() for r in registros)

class AzucarSodioStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> float:
        return sum(r.componente.GetNutrientes().azucar + r.componente.GetNutrientes().sodio for r in registros)

class MacronutrientesStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> float:
        # Suma de macros principales
        return sum(r.componente.GetNutrientes().proteina + 
                   r.componente.GetNutrientes().carbohidratos + 
                   r.componente.GetNutrientes().grasas for r in registros)

class AnalizadorNutricional:
    def __init__(self, estrategia: IIndicadorStrategy):
        self._estrategia = estrategia

    def SetEstrategia(self, e: IIndicadorStrategy) -> None:
        self._estrategia = e

    def Analizar(self, registros: List[RegistroConsumo]) -> float:
        return self._estrategia.Calcular(registros)