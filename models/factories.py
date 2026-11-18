from abc import ABC, abstractmethod
from typing import Optional
from .alimento import Alimento
from .platillo import Platillo
from .nutrientes import Nutrientes

"""
@author Armando Imanol Aguilar Espiricueto
"""

# --- Factories para Alimentos ---
class AlimentoFactory(ABC):
    @abstractmethod
    def CrearAlimento(self, nombre: str, nutrientes_db: Optional[Nutrientes] = None) -> Alimento:
        pass

class ProteinaFactory(AlimentoFactory):
    def CrearAlimento(self, nombre: str, nutrientes_db: Optional[Nutrientes] = None) -> Alimento:
        # Ejemplo: Valores base por defecto para una proteína si no provienen de BD
        nutrientes = nutrientes_db if nutrientes_db is not None else Nutrientes(150, 25, 0, 5, 0, 50)
        return Alimento(nombre, nutrientes)

class FrutaFactory(AlimentoFactory):
    def CrearAlimento(self, nombre: str, nutrientes_db: Optional[Nutrientes] = None) -> Alimento:
        nutrientes = nutrientes_db if nutrientes_db is not None else Nutrientes(80, 1, 20, 0, 15, 2)
        return Alimento(nombre, nutrientes)

class VerduraFactory(AlimentoFactory):
    def CrearAlimento(self, nombre: str, nutrientes_db: Optional[Nutrientes] = None) -> Alimento:
        nutrientes = nutrientes_db if nutrientes_db is not None else Nutrientes(30, 2, 5, 0, 2, 10)
        return Alimento(nombre, nutrientes)

class LeguminosaFactory(AlimentoFactory):
    def CrearAlimento(self, nombre: str, nutrientes_db: Optional[Nutrientes] = None) -> Alimento:
        nutrientes = nutrientes_db if nutrientes_db is not None else Nutrientes(120, 8, 20, 1, 1, 15)
        return Alimento(nombre, nutrientes)

# --- Factories para Platillos ---
class PlatilloFactory(ABC):
    @abstractmethod
    def CrearPlatillo(self) -> Platillo:
        pass

class DesayunoFactory(PlatilloFactory):
    def CrearPlatillo(self) -> Platillo:
        return Platillo("Desayuno")

class ComidaFactory(PlatilloFactory):
    def CrearPlatillo(self) -> Platillo:
        return Platillo("Comida")

class CenaFactory(PlatilloFactory):
    def CrearPlatillo(self) -> Platillo:
        return Platillo("Cena")

class MeriendaFactory(PlatilloFactory):
    def CrearPlatillo(self) -> Platillo:
        return Platillo("Merienda")


# --- Registros de Fábricas (Principio Abierto/Cerrado - OCP) ---
FABRICAS_ALIMENTO: dict[str, type[AlimentoFactory]] = {
    "Proteina": ProteinaFactory,
    "Fruta": FrutaFactory,
    "Verdura": VerduraFactory,
    "Leguminosa": LeguminosaFactory,
}

FABRICAS_PLATILLO: dict[str, type[PlatilloFactory]] = {
    "desayuno": DesayunoFactory,
    "comida": ComidaFactory,
    "cena": CenaFactory,
    "merienda": MeriendaFactory,
}