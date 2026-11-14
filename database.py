from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Definir la clase base
class Base(DeclarativeBase):
    pass

# Inicializar la extensión (sin vincularla aún a la app)
db = SQLAlchemy(model_class=Base)