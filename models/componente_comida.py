from abc import ABC, abstractmethod
from .nutrientes import Nutrientes

class IComponenteComida(ABC):
    @abstractmethod
    def GetNombre(self) -> str:
        pass

    @abstractmethod
    def GetCalorias(self) -> float:
        pass

    @abstractmethod
    def GetNutrientes(self) -> Nutrientes:
        pass

    @abstractmethod
    def GetDescripcionIngredientes(self) -> str:
        pass