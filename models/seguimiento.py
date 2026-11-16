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
    def Notificar(self, evento: Any) -> None:
        pass

class RegistroConsumo:
    def __init__(self, componente: IComponenteComida):
        self.fecha = datetime.now()
        self.componente = componente

class SeguimientoConsumo(ISujeto):
    def __init__(self):
        self._observadores: List[IObservador] = []

    def Suscribir(self, o: IObservador) -> None:
        if o not in self._observadores:
            self._observadores.append(o)

    def Desuscribir(self, o: IObservador) -> None:
        if o in self._observadores:
            self._observadores.remove(o)

    def Notificar(self, evento: Any) -> None:
        for obs in self._observadores:
            obs.Actualizar(evento)

    def RegistrarConsumo(self, registro: RegistroConsumo, usuario_id: int) -> None:
        evento = {
            "usuario_id": usuario_id,
            "registro": registro
        }
        self.Notificar(evento) # Dispara el patrón Observer

# --- Observadores Concretos ---
class NotificadorPendientes(IObservador):
    def Actualizar(self, evento: Any) -> None:
        registro = evento.get("registro") if isinstance(evento, dict) else None
        nombre = registro.componente.GetNombre() if registro else evento
        print(f"[NotificadorPendientes]: Alerta recibida -> Consumo registrado: {nombre}")

class NotificadorObjetivos(IObservador):
    def Actualizar(self, evento: Any) -> None:
        from database import db
        from .orm_models import ObjetivoNutricionalModel

        usuario_id = evento.get("usuario_id")
        registro: RegistroConsumo = evento.get("registro")

        objetivo_db = db.session.query(ObjetivoNutricionalModel).filter_by(usuario_id=usuario_id).first()
        calorias_consumidas = registro.componente.GetCalorias()
        nombre_consumido = registro.componente.GetNombre()

        if objetivo_db:
            porcentaje = (calorias_consumidas / objetivo_db.calorias_meta) * 100 if objetivo_db.calorias_meta > 0 else 0
            print(
                f"[NotificadorObjetivos]: Usuario {usuario_id} consumió '{nombre_consumido}' "
                f"({calorias_consumidas} kcal), aportando un {porcentaje:.1f}% hacia su meta de "
                f"{objetivo_db.calorias_meta} kcal."
            )
        else:
            print(
                f"[NotificadorObjetivos]: Usuario {usuario_id} consumió '{nombre_consumido}' "
                f"({calorias_consumidas} kcal). Sin objetivo nutricional registrado."
            )