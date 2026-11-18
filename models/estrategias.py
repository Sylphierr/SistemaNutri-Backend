from abc import ABC, abstractmethod
from typing import List, Any
from .seguimiento import RegistroConsumo

class IIndicadorStrategy(ABC):
    @abstractmethod
    def Calcular(self, registros: List[RegistroConsumo]) -> Any:
        pass

class CaloriasStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> dict:
        total_calorias = sum(r.componente.GetCalorias() for r in registros)
        desglose = [
            {
                "nombre": r.componente.GetNombre(),
                "ingredientes": r.componente.GetDescripcionIngredientes(),
                "calorias": round(r.componente.GetCalorias(), 1),
            }
            for r in registros
        ]

        return {
            "Total de Calorías (kcal)": round(total_calorias, 1),
            "desglose": desglose,
        }

class AzucarSodioStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> dict:
        return {
            "azucar_g": round(sum(r.componente.GetNutrientes().azucar for r in registros), 1),
            "sodio_mg": round(sum(r.componente.GetNutrientes().sodio for r in registros), 1)
        }

class MacronutrientesStrategy(IIndicadorStrategy):
    def Calcular(self, registros: List[RegistroConsumo]) -> dict:
        return {
            "proteina_g": round(sum(r.componente.GetNutrientes().proteina for r in registros), 1),
            "carbohidratos_g": round(sum(r.componente.GetNutrientes().carbohidratos for r in registros), 1),
            "grasas_g": round(sum(r.componente.GetNutrientes().grasas for r in registros), 1)
        }

class AnalizadorNutricional:
    def __init__(self, estrategia: IIndicadorStrategy):
        self._estrategia = estrategia

    def SetEstrategia(self, e: IIndicadorStrategy) -> None:
        self._estrategia = e

    def Analizar(self, registros: List[RegistroConsumo]) -> Any:
        return self._estrategia.Calcular(registros)


# --- Registro de Estrategias (Principio Abierto/Cerrado - OCP) ---
ESTRATEGIAS_REPORTE: dict[str, tuple[type[IIndicadorStrategy], str]] = {
    "calorias": (CaloriasStrategy, "Total de Calorías (kcal)"),
    "macros": (MacronutrientesStrategy, "Desglose de Macronutrientes"),
    "azucar_sodio": (AzucarSodioStrategy, "Desglose de Azúcar y Sodio"),
}