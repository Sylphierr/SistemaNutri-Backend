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
        return sum(c.GetCalorias() for c in self._componentes)

    def GetNutrientes(self) -> Nutrientes:
        total = Nutrientes(0, 0, 0, 0, 0, 0)
        for comp in self._componentes:
            n = comp.GetNutrientes()
            total.calorias += n.calorias
            total.proteina += n.proteina
            total.carbohidratos += n.carbohidratos
            total.grasas += n.grasas
            total.azucar += n.azucar
            total.sodio += n.sodio
        return total