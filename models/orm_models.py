from sqlalchemy import String, Float, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from database import db

# 1. Tabla de Usuarios
class UsuarioModel(db.Model):
    __tablename__ = "Usuarios"

    id: Mapped[int] = mapped_column("id_usuario", primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column("nombre_usuario", String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="usuario")  # 'usuario', 'doctor', 'admin'
    preferencias: Mapped[str] = mapped_column("preferencias_usuario", String(255), nullable=True)

    # Datos personales del usuario
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    edad: Mapped[int] = mapped_column(Integer, nullable=True)
    peso_kg: Mapped[float] = mapped_column(Float, nullable=True)
    altura_cm: Mapped[float] = mapped_column(Float, nullable=True)
    telefono: Mapped[str] = mapped_column(String(30), nullable=True)

    # Relaciones
    objetivo: Mapped["ObjetivoNutricionalModel"] = relationship(back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    registros: Mapped[list["RegistroConsumoModel"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    solicitudes_enviadas: Mapped[list["SolicitudAyudaModel"]] = relationship(
        foreign_keys="SolicitudAyudaModel.paciente_id",
        back_populates="paciente",
        cascade="all, delete-orphan"
    )
    solicitudes_atendidas: Mapped[list["SolicitudAyudaModel"]] = relationship(
        foreign_keys="SolicitudAyudaModel.doctor_id",
        back_populates="doctor"
    )

# 2. Tabla de Objetivos Nutricionales 
class ObjetivoNutricionalModel(db.Model):
    __tablename__ = "ObjetivosNutricionales"

    id: Mapped[int] = mapped_column("id_objetivos", primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column("id_usuario", ForeignKey("Usuarios.id_usuario"), unique=True)
    calorias_meta: Mapped[float] = mapped_column(Float, nullable=False)
    proteina_meta: Mapped[float] = mapped_column(Float, nullable=False)

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="objetivo")

# 3. Catálogo de Alimentos 
class CatalogoAlimentoModel(db.Model):
    __tablename__ = "catalogo_alimentos"

    id: Mapped[int] = mapped_column("id_alimento", primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column("nombre_alimento", String(100), unique=True, nullable=False)
    tipo_factory: Mapped[str] = mapped_column(String(50), nullable=False) 
    
    # Nutrientes base por porción
    calorias: Mapped[float] = mapped_column(Float, default=0.0)
    proteina: Mapped[float] = mapped_column(Float, default=0.0)
    carbohidratos: Mapped[float] = mapped_column(Float, default=0.0)
    grasas: Mapped[float] = mapped_column(Float, default=0.0)
    azucar: Mapped[float] = mapped_column(Float, default=0.0)
    sodio: Mapped[float] = mapped_column(Float, default=0.0)

# 4. Historial de Consumo 
class RegistroConsumoModel(db.Model):
    __tablename__ = "registros_consumo"

    id: Mapped[int] = mapped_column("id_consumo", primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column("id_usuario", ForeignKey("Usuarios.id_usuario"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Guardamos una "fotografía" de lo que se comió 
    nombre_consumido: Mapped[str] = mapped_column(String(150), nullable=False)
    ingredientes_consumidos: Mapped[str] = mapped_column(String(500), nullable=True, default="")
    
    # Guardamos el total calculado por el patrón Composite en el momento del consumo.
    calorias_totales: Mapped[float] = mapped_column(Float, nullable=False)
    proteina_total: Mapped[float] = mapped_column(Float, nullable=False)
    carbohidratos_total: Mapped[float] = mapped_column(Float, nullable=False)
    grasas_total: Mapped[float] = mapped_column(Float, nullable=False)
    azucar_total: Mapped[float] = mapped_column(Float, nullable=False)
    sodio_total: Mapped[float] = mapped_column(Float, nullable=False)

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="registros")


# 5. Solicitudes de Ayuda al Doctor
class SolicitudAyudaModel(db.Model):
    __tablename__ = "solicitudes_ayuda"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("Usuarios.id_usuario"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("Usuarios.id_usuario"), nullable=True)
    motivo: Mapped[str] = mapped_column(String(300), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="pendiente")  # 'pendiente', 'en_atencion', 'cerrada'
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    paciente: Mapped["UsuarioModel"] = relationship(foreign_keys=[paciente_id], back_populates="solicitudes_enviadas")
    doctor: Mapped["UsuarioModel"] = relationship(foreign_keys=[doctor_id], back_populates="solicitudes_atendidas")
    mensajes: Mapped[list["MensajeChatModel"]] = relationship(
        back_populates="solicitud",
        cascade="all, delete-orphan",
        order_by="MensajeChatModel.fecha_envio"
    )


# 6. Mensajes de Chat entre Paciente y Doctor
class MensajeChatModel(db.Model):
    __tablename__ = "mensajes_chat"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    solicitud_id: Mapped[int] = mapped_column(ForeignKey("solicitudes_ayuda.id"), nullable=False)
    remitente_id: Mapped[int] = mapped_column(ForeignKey("Usuarios.id_usuario"), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_envio: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    leido: Mapped[bool] = mapped_column(Boolean, default=False)

    solicitud: Mapped["SolicitudAyudaModel"] = relationship(back_populates="mensajes")
    remitente: Mapped["UsuarioModel"] = relationship(foreign_keys=[remitente_id])