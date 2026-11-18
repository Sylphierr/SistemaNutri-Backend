from werkzeug.security import generate_password_hash
from app import app
from database import db
from models.orm_models import UsuarioModel, ObjetivoNutricionalModel, CatalogoAlimentoModel

def poblar_base_datos():
    with app.app_context():
        # 1. Crear las tablas si no existen
        db.create_all()

        # 2. Verificar si ya hay datos para no duplicarlos
        if db.session.query(UsuarioModel).first():
            print("La base de datos ya contiene información. Poblado omitido.")
            return

        print("Poblando la base de datos...")

        # 3. Crear tu Usuario de Prueba (Armando)
        usuario_prueba = UsuarioModel(
            nombre="Armando",
            password_hash=generate_password_hash("123456"),
            preferencias="Hipertrofia muscular, comida alta en proteína"
        )
        db.session.add(usuario_prueba)
        db.session.flush() # Flush para obtener el ID generado (usuario_prueba.id)

        # 4. Crear un Objetivo Nutricional para el usuario
        objetivo_armando = ObjetivoNutricionalModel(
            usuario_id=usuario_prueba.id,
            calorias_meta=2500.0,
            proteina_meta=160.0
        )
        db.session.add(objetivo_armando)

        # 5. Llenar el Catálogo de Alimentos (Para el Factory)
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
        print("¡Base de datos poblada exitosamente con el catálogo y el usuario de prueba!")

if __name__ == '__main__':
    poblar_base_datos()