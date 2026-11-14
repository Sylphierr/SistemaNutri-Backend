from sqlalchemy import String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database import db

# 1. Tabla de Usuarios
class UsuarioModel(db.Model):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    preferencias: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relaciones
    objetivo: Mapped["ObjetivoNutricionalModel"] = relationship(back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    registros: Mapped[list["RegistroConsumoModel"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")

# 2. Tabla de Objetivos Nutricionales (Relación 1 a 1 con Usuario)
class ObjetivoNutricionalModel(db.Model):
    __tablename__ = "objetivos_nutricionales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    calorias_meta: Mapped[float] = mapped_column(Float, nullable=False)
    proteina_meta: Mapped[float] = mapped_column(Float, nullable=False)

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="objetivo")

# 3. Catálogo de Alimentos (El "motor" de tu Factory Method)
class CatalogoAlimentoModel(db.Model):
    __tablename__ = "catalogo_alimentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # tipo_factory define si es Proteina, Fruta o Verdura para instanciar la clase correcta
    tipo_factory: Mapped[str] = mapped_column(String(50), nullable=False) 
    
    # Nutrientes base por porción
    calorias: Mapped[float] = mapped_column(Float, default=0.0)
    proteina: Mapped[float] = mapped_column(Float, default=0.0)
    carbohidratos: Mapped[float] = mapped_column(Float, default=0.0)
    grasas: Mapped[float] = mapped_column(Float, default=0.0)
    azucar: Mapped[float] = mapped_column(Float, default=0.0)
    sodio: Mapped[float] = mapped_column(Float, default=0.0)

# 4. Historial de Consumo (El "Observer" inserta aquí y el "Strategy" lee de aquí)
class RegistroConsumoModel(db.Model):
    __tablename__ = "registros_consumo"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Guardamos una "fotografía" de lo que se comió (puede ser un Alimento simple o un Platillo compuesto)
    nombre_consumido: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # Guardamos el total calculado por el patrón Composite en el momento del consumo.
    # Esto es crucial: si los macros de un alimento cambian en el catálogo el próximo año, 
    # el historial de consumo de hoy no debe alterarse.
    calorias_totales: Mapped[float] = mapped_column(Float, nullable=False)
    proteina_total: Mapped[float] = mapped_column(Float, nullable=False)
    carbohidratos_total: Mapped[float] = mapped_column(Float, nullable=False)
    grasas_total: Mapped[float] = mapped_column(Float, nullable=False)
    azucar_total: Mapped[float] = mapped_column(Float, nullable=False)
    sodio_total: Mapped[float] = mapped_column(Float, nullable=False)

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="registros")