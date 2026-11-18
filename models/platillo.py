from typing import List
from .componente_comida import IComponenteComida
from .nutrientes import Nutrientes

"""
@author Armando Imanol Aguilar Espiricueto
"""

class Platillo(IComponenteComida):
    def __init__(self, nombre: str):
        self._nombre = nombre
        self._componentes: List[IComponenteComida] = []

    def Agregar(self, c: IComponenteComida) -> None:
        self._componentes.append(c)

    def Quitar(self, c: IComponenteComida) -> None:
        if c in self._componentes:
            self._componentes.remove(c)

    def GetNombre(self) -> str:
        return self._nombre

    def GetCalorias(self) -> float:
        return round(sum(c.GetCalorias() for c in self._componentes), 1)

    def GetNutrientes(self) -> Nutrientes:
        total = Nutrientes(0, 0, 0, 0, 0, 0)
        for comp in self._componentes:
            n = comp.GetNutrientes()
            total.calorias = round(total.calorias + n.calorias, 1)
            total.proteina = round(total.proteina + n.proteina, 1)
            total.carbohidratos = round(total.carbohidratos + n.carbohidratos, 1)
            total.grasas = round(total.grasas + n.grasas, 1)
            total.azucar = round(total.azucar + n.azucar, 1)
            total.sodio = round(total.sodio + n.sodio, 1)
        return total

    def GetDescripcionIngredientes(self) -> str:
        if not self._componentes:
            return "Ingrediente único"
        return ", ".join(c.GetNombre() for c in self._componentes)