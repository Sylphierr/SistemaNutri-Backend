from typing import List, Any
from .platillo import Platillo

"""
@author Armando Imanol Aguilar Espiricueto
"""

class ObjetivoNutricional:
    def __init__(self, caloriasMeta: float, proteinaMeta: float):
        self.caloriasMeta = caloriasMeta
        self.proteinaMeta = proteinaMeta

    def EstaCumplido(self, valorCalorias: float, valorProteina: float = 0.0) -> bool:
        return valorCalorias <= self.caloriasMeta and valorProteina >= self.proteinaMeta

class Recomendacion:
    def __init__(self, mensaje: str = ""):
        self._mensaje = mensaje

    def AvisoLegal(self) -> str:
        # Requisito explícito del negocio: no sustituye atención médica
        return "Las recomendaciones son informativas y no sustituyen la atención de un nutriólogo."

class ComparadorHabitos:
    def Comparar(self, registros: List[Any], objetivo: ObjetivoNutricional) -> str:
        total_calorias = sum(r.componente.GetCalorias() for r in registros)
        total_proteina = sum(r.componente.GetNutrientes().proteina for r in registros)

        if objetivo.EstaCumplido(total_calorias, total_proteina):
            return (
                f"Objetivo cumplido: {total_calorias}/{objetivo.caloriasMeta} kcal y "
                f"{total_proteina}/{objetivo.proteinaMeta}g de proteína."
            )
        return (
            f"En progreso o fuera de rango: llevas {total_calorias}/{objetivo.caloriasMeta} kcal y "
            f"{total_proteina}/{objetivo.proteinaMeta}g de proteína."
        )

    def ObtenerTendencias(self) -> str:
        return "Tendencia: Alto consumo de proteínas en el desayuno."

class Menu:
    def __init__(self):
        self._platillos: List[Platillo] = []

    def AgregarPlatillo(self, p: Platillo) -> None:
        self._platillos.append(p)

class Usuario:
    def __init__(self, nombre: str, preferencias: str):
        self._nombre = nombre
        self._preferencias = preferencias