from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioResponse, UsuarioUpdate, PasswordChangeRequest
from app.core.security import hash_password, decode_token, verify_password
import secrets
import string

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Dependencia para verificar que el usuario esté autenticado"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado"
        )

    token = authorization.split(" ", 1)[1]
    
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    
    usuario_id = int(payload.get("sub"))
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido o desactivado"
        )
    
    return usuario


def get_supervisor(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Dependencia para verificar que el usuario es supervisor"""
    current_user = get_current_user(authorization, db)
    if current_user.rol != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores pueden acceder a esta funcionalidad"
        )
    return current_user


def generate_temp_password(length: int = 12) -> str:
    """Genera una contraseña temporal segura"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


@router.post("", response_model=dict)
async def crear_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_supervisor)
):
    """Crear un nuevo usuario (solo supervisores)"""
    
    # Verificar que el email no exista
    if db.query(Usuario).filter(Usuario.email == usuario_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Generar contraseña temporal
    temp_password = generate_temp_password()
    
    nuevo_usuario = Usuario(
        nombre=usuario_data.nombre,
        email=usuario_data.email,
        password_hash=hash_password(temp_password),
        rol=usuario_data.rol,
        zona=usuario_data.zona,
        activo=True
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return {
        "id": nuevo_usuario.id,
        "nombre": nuevo_usuario.nombre,
        "email": nuevo_usuario.email,
        "rol": nuevo_usuario.rol,
        "zona": nuevo_usuario.zona,
        "activo": nuevo_usuario.activo,
        "debe_cambiar_password": nuevo_usuario.debe_cambiar_password,
        "fecha_creacion": nuevo_usuario.fecha_creacion,
        "contraseña_temporal": temp_password
    }


@router.get("", response_model=List[UsuarioResponse])
async def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_supervisor)
):
    """Listar todos los usuarios (solo supervisores)"""
    usuarios = db.query(Usuario).all()
    return usuarios


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_supervisor)
):
    """Editar datos o rol de un usuario (solo supervisores)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if usuario_data.nombre:
        usuario.nombre = usuario_data.nombre
    if usuario_data.rol:
        usuario.rol = usuario_data.rol
    if usuario_data.zona:
        usuario.zona = usuario_data.zona
    
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.delete("/{usuario_id}", response_model=dict)
async def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_supervisor)
):
    """Desactivar un usuario (no borra físicamente) (solo supervisores)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario.activo = False
    db.commit()
    
    return {"mensaje": "Usuario desactivado correctamente"}


@router.put("/me/cambiar-password", response_model=dict)
async def cambiar_password(
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Permite al usuario autenticado cambiar su contraseña"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado"
        )

    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede validar la contraseña actual"
        )

    if not verify_password(data.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )

    current_user.password_hash = hash_password(data.password_nuevo)
    current_user.debe_cambiar_password = False
    db.commit()
    db.refresh(current_user)

    return {"mensaje": "Contraseña actualizada correctamente"}
