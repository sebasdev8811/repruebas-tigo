from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Cliente, Usuario
from app.schemas import ClienteCreate, ClienteResponse
from app.core.security import decode_token

router = APIRouter(prefix="/clientes", tags=["Clientes"])

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
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


@router.post("", response_model=ClienteResponse)
async def crear_cliente(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo cliente"""
    
    if db.query(Cliente).filter(Cliente.cedula_cliente == cliente_data.cedula_cliente).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente con esa cédula ya existe"
        )
    
    nuevo_cliente = Cliente(**cliente_data.dict())
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    
    return nuevo_cliente


@router.get("", response_model=List[ClienteResponse])
async def listar_clientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los clientes"""
    clientes = db.query(Cliente).all()
    return clientes


@router.get("/{cedula_cliente}", response_model=ClienteResponse)
async def obtener_cliente(
    cedula_cliente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener un cliente por cédula"""
    cliente = db.query(Cliente).filter(Cliente.cedula_cliente == cedula_cliente).first()
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return cliente
