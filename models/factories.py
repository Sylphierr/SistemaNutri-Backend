from abc import ABC, abstractmethod
from .alimento import Alimento
from .platillo import Platillo
from .nutrientes import Nutrientes

"""
@author Armando Imanol Aguilar Espiricueto
"""

# --- Factories para Alimentos ---
class AlimentoFactory(ABC):
    @abstractmethod
    def CrearAlimento(self, nombre: str) -> Alimento:
        pass

class ProteinaFactory(AlimentoFactory):
    def CrearAlimento(self, nombre: str) -> Alimento:
        # Ejemplo: Valores base por defecto para una proteína
        return Alimento(nombre, Nutrientes(150, 25, 0, 5, 0, 50)) 

class FrutaFactory(AlimentoFactory):
    def CrearAlimento(self, nombre: str) -> Alimento:
        return Alimento(nombre, Nutrientes(80, 1, 20, 0, 15, 2))

class VerduraFactory(AlimentoFactory):
    def CrearAlimento(self, nombre: str) -> Alimento:
        return Alimento(nombre, Nutrientes(30, 2, 5, 0, 2, 10))

# --- Factories para Platillos ---
class PlatilloFactory(ABC):
    @abstractmethod
    def CrearPlatillo(self) -> Platillo:
        pass

class DesayunoFactory(PlatilloFactory):
    def CrearPlatillo(self) -> Platillo:
        return Platillo("Desayuno Estándar")

class ComidaFactory(PlatilloFactory):
    def CrearPlatillo(self) -> Platillo:
        return Platillo("Comida Estándar")