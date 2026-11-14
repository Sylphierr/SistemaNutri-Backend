from typing import List, Any
from .platillo import Platillo

"""
@author Armando Imanol Aguilar Espiricueto
"""

class ObjetivoNutricional:
    def __init__(self, caloriasMeta: float, proteinaMeta: float):
        self.caloriasMeta = caloriasMeta
        self.proteinaMeta = proteinaMeta

    def EstaCumplido(self, valorCalorias: float) -> bool:
        return valorCalorias <= self.caloriasMeta

class Recomendacion:
    def __init__(self, mensaje: str):
        self._mensaje = mensaje

    def AvisoLegal(self) -> str:
        # Requisito explícito del negocio: no sustituye atención médica
        return "Las recomendaciones son informativas y no sustituyen la atención de un nutriólogo."

class ComparadorHabitos:
    def Comparar(self, registros: List[Any], objetivo: ObjetivoNutricional) -> str:
        # Lógica de comparación
        return "Resultado: Consumo dentro de los parámetros del objetivo."

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