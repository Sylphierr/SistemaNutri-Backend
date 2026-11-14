from abc import ABC, abstractmethod
from typing import List, Any
from datetime import datetime
from .componente_comida import IComponenteComida

"""
@author Armando Imanol Aguilar Espiricueto
"""

class IObservador(ABC):
    @abstractmethod
    def Actualizar(self, evento: Any) -> None:
        pass

class ISujeto(ABC):
    @abstractmethod
    def Suscribir(self, o: IObservador) -> None:
        pass
    
    @abstractmethod
    def Desuscribir(self, o: IObservador) -> None:
        pass
    
    @abstractmethod
    def Notificar(self) -> None:
        pass

class RegistroConsumo:
    def __init__(self, componente: IComponenteComida):
        self.fecha = datetime.now()
        self.componente = componente

class SeguimientoConsumo(ISujeto):
    def __init__(self):
        self._observadores: List[IObservador] = []
        self.registros: List[RegistroConsumo] = []

    def Suscribir(self, o: IObservador) -> None:
        if o not in self._observadores:
            self._observadores.append(o)

    def Desuscribir(self, o: IObservador) -> None:
        if o in self._observadores:
            self._observadores.remove(o)

    def Notificar(self) -> None:
        for obs in self._observadores:
            obs.Actualizar("Nuevo registro de consumo añadido")

    def RegistrarConsumo(self, registro: RegistroConsumo) -> None:
        self.registros.append(registro)
        self.Notificar() # Dispara el patrón Observer

# --- Observadores Concretos ---
class NotificadorPendientes(IObservador):
    def Actualizar(self, evento: Any) -> None:
        print(f"[NotificadorPendientes]: Alerta recibida -> {evento}")

class NotificadorObjetivos(IObservador):
    def Actualizar(self, evento: Any) -> None:
        print(f"[NotificadorObjetivos]: Evaluando progreso de metas tras -> {evento}")