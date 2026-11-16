from abc import ABC, abstractmethod
from typing import List, Any
from .seguimiento import RegistroConsumo

class IIndicadorStrategy(ABC):
    @abstractmethod
    def Calcular(self, registros: List[RegistroConsumo]) -> Any:
        pass

class CaloriasStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> float:
        return sum(r.componente.GetCalorias() for r in registros)

class AzucarSodioStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> dict:
        return {
            "azucar_g": sum(r.componente.GetNutrientes().azucar for r in registros),
            "sodio_mg": sum(r.componente.GetNutrientes().sodio for r in registros)
        }

class MacronutrientesStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> dict:
        return {
            "proteina_g": sum(r.componente.GetNutrientes().proteina for r in registros),
            "carbohidratos_g": sum(r.componente.GetNutrientes().carbohidratos for r in registros),
            "grasas_g": sum(r.componente.GetNutrientes().grasas for r in registros)
        }

class AnalizadorNutricional:
    def __init__(self, estrategia: IIndicadorStrategy):
        self._estrategia = estrategia

    def SetEstrategia(self, e: IIndicadorStrategy) -> None:
        self._estrategia = e

    def Analizar(self, registros: List[RegistroConsumo]) -> Any:
        return self._estrategia.Calcular(registros)