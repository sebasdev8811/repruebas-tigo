from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import SolicitudAcceso, Usuario
from app.schemas import SolicitudAccesoCreate, SolicitudAccesoResponse, SolicitudAccesoUpdate
from app.core.security import decode_token, hash_password
import secrets
import string

router = APIRouter(prefix="/solicitudes", tags=["Solicitudes de Acceso"])


def get_supervisor(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Dependencia para verificar que el usuario es supervisor"""
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
    
    if usuario.rol != "supervisor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores pueden acceder a esta funcionalidad"
        )
    
    return usuario


def generate_temp_password(length: int = 12) -> str:
    """Genera una contraseña temporal segura"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


@router.post("", response_model=SolicitudAccesoResponse)
async def crear_solicitud(solicitud_data: SolicitudAccesoCreate, db: Session = Depends(get_db)):
    """
    Endpoint público para que cualquier persona envíe una solicitud de acceso
    """
    nueva_solicitud = SolicitudAcceso(
        nombre=solicitud_data.nombre,
        email=solicitud_data.email,
        zona=solicitud_data.zona,
        rol_solicitado=solicitud_data.rol_solicitado,
        motivo=solicitud_data.motivo,
        estado="pendiente"
    )
    
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    
    return nueva_solicitud


@router.get("", response_model=List[SolicitudAccesoResponse])
async def listar_solicitudes(
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_supervisor)
):
    """
    Listar solicitudes de acceso (solo supervisores), filtrable por estado
    """
    query = db.query(SolicitudAcceso)
    
    if estado:
        query = query.filter(SolicitudAcceso.estado == estado)
    
    solicitudes = query.all()
    return solicitudes


@router.put("/{solicitud_id}/aprobar", response_model=dict)
async def aprobar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_supervisor)
):
    """
    Aprobar una solicitud: cambia estado a aprobada y crea el usuario automáticamente
    """
    solicitud = db.query(SolicitudAcceso).filter(SolicitudAcceso.id == solicitud_id).first()
    
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada"
        )
    
    if solicitud.estado != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden aprobar solicitudes pendientes"
        )
    
    # Generar contraseña temporal
    temp_password = generate_temp_password()
    
    # Crear usuario
    nuevo_usuario = Usuario(
        nombre=solicitud.nombre,
        email=solicitud.email,
        password_hash=hash_password(temp_password),
        rol=solicitud.rol_solicitado,
        zona=solicitud.zona,
        activo=True
    )
    
    solicitud.estado = "aprobada"
    solicitud.password_temporal = temp_password
    
    db.add(nuevo_usuario)
    db.commit()
    
    return {
        "mensaje": "Solicitud aprobada y usuario creado",
        "usuario_email": solicitud.email,
        "contraseña_temporal": temp_password
    }


@router.put("/{solicitud_id}/rechazar", response_model=dict)
async def rechazar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_supervisor)
):
    """
    Rechazar una solicitud de acceso
    """
    solicitud = db.query(SolicitudAcceso).filter(SolicitudAcceso.id == solicitud_id).first()
    
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada"
        )
    
    if solicitud.estado != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden rechazar solicitudes pendientes"
        )
    
    solicitud.estado = "rechazada"
    db.commit()
    
    return {"mensaje": "Solicitud rechazada"}
