from werkzeug.security import generate_password_hash
from app import app
from database import db
from models.orm_models import UsuarioModel, ObjetivoNutricionalModel, CatalogoAlimentoModel

def poblar_base_datos():
    with app.app_context():
        # 1. Crear las tablas si no existen
        db.create_all()

        print("Verificando y poblando datos iniciales...")

        # 2. Usuario de Prueba (Armando - rol usuario)
        usuario_prueba = db.session.query(UsuarioModel).filter_by(nombre="Armando").first()
        if not usuario_prueba:
            usuario_prueba = UsuarioModel(
                nombre="Armando",
                password_hash=generate_password_hash("123456"),
                rol="usuario",
                preferencias="Hipertrofia muscular, comida alta en proteína",
                email="armando@nutri.com",
                edad=22,
                peso_kg=74.5,
                altura_cm=176.0,
                telefono="555-123-4567"
            )
            db.session.add(usuario_prueba)
            db.session.flush()

            objetivo_armando = ObjetivoNutricionalModel(
                usuario_id=usuario_prueba.id,
                calorias_meta=2500.0,
                proteina_meta=160.0
            )
            db.session.add(objetivo_armando)

        # 3. Administrador por defecto
        if not db.session.query(UsuarioModel).filter_by(nombre="admin").first():
            admin_user = UsuarioModel(
                nombre="admin",
                password_hash=generate_password_hash("admin123"),
                rol="admin",
                preferencias="Administración del sistema",
                email="admin@nutri.com",
                edad=30,
                telefono="555-000-0001"
            )
            db.session.add(admin_user)

        # 4. Doctor por defecto
        if not db.session.query(UsuarioModel).filter_by(nombre="doctor").first():
            doctor_user = UsuarioModel(
                nombre="doctor",
                password_hash=generate_password_hash("doctor123"),
                rol="doctor",
                preferencias="Nutrición clínica y deportiva",
                email="doctor@nutri.com",
                edad=35,
                telefono="555-000-0002"
            )
            db.session.add(doctor_user)

        # 5. Llenar el Catálogo de Alimentos (Para el Factory) si está vacío
        if not db.session.query(CatalogoAlimentoModel).first():
            alimentos = [
                CatalogoAlimentoModel(
                    nombre="Pechuga de Pollo (100g)", tipo_factory="Proteina",
                    calorias=165.0, proteina=31.0, carbohidratos=0.0, grasas=3.6, azucar=0.0, sodio=74.0
                ),
                CatalogoAlimentoModel(
                    nombre="Plátano", tipo_factory="Fruta",
                    calorias=105.0, proteina=1.3, carbohidratos=27.0, grasas=0.3, azucar=14.0, sodio=1.0
                ),
                CatalogoAlimentoModel(
                    nombre="Brócoli (1 taza)", tipo_factory="Verdura",
                    calorias=55.0, proteina=3.7, carbohidratos=11.2, grasas=0.6, azucar=2.0, sodio=33.0
                )
            ]
            db.session.bulk_save_objects(alimentos)

        # 6. Guardar todos los cambios
        db.session.commit()
        print("¡Base de datos verificada/poblada exitosamente con roles (usuario, doctor, admin)!")

if __name__ == '__main__':
    poblar_base_datos()