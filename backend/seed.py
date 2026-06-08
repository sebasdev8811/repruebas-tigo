"""
Script para cargar datos iniciales en la base de datos
Ejecutar desde el directorio backend: python seed.py
"""

import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Usuario
from app.core.security import hash_password


def seed_db():
    """Inserta el usuario administrador por defecto"""
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Verificar si el usuario admin ya existe
        admin_existente = db.query(Usuario).filter(Usuario.email == "admin@tigo.com").first()
        
        if admin_existente:
            print("✓ El usuario administrador ya existe")
            return
        
        # Crear usuario administrador
        admin = Usuario(
            nombre="Administrador",
            email="admin@tigo.com",
            password_hash=hash_password("Admin2026*"),
            rol="supervisor",
            zona="Nacional",
            activo=True,
            debe_cambiar_password=False
        )
        
        db.add(admin)
        db.commit()
        
        print("✓ Usuario administrador creado exitosamente")
        print("  Email: admin@tigo.com")
        print("  Password: Admin2026*")
        print("  Rol: supervisor")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error al crear usuario: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
