from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario
from app.schemas import LoginRequest, TokenResponse, UsuarioResponse
from app.core.security import verify_password, create_access_token, decode_token, hash_password
from app.services.email import send_reset_password_email
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import secrets

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password_nuevo: str


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de login. Recibe email y password, valida y retorna JWT
    """
    usuario = db.query(Usuario).filter(Usuario.email == credentials.email).first()
    
    if not usuario or not verify_password(credentials.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña inválidos"
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    access_token = create_access_token(data={"sub": str(usuario.id), "email": usuario.email})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        usuario_id=usuario.id,
        nombre=usuario.nombre,
        rol=usuario.rol,
        debe_cambiar_password=usuario.debe_cambiar_password
    )


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """
    Endpoint para obtener el usuario autenticado
    El token se recibe desde el header Authorization: Bearer <token>
    """
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
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return usuario


@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Endpoint público para solicitar reset de contraseña
    Genera un token y envía un correo al usuario
    """
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    if not usuario:
        # No revelar si el email existe o no (por seguridad)
        return {"mensaje": "Si el email está registrado recibirás un enlace en tu correo"}
    
    # Generar token único
    reset_token = secrets.token_urlsafe(32)
    reset_token_expira = datetime.utcnow() + timedelta(hours=1)
    
    usuario.reset_token = reset_token
    usuario.reset_token_expira = reset_token_expira
    db.commit()
    
    # Enviar correo
    try:
        await send_reset_password_email(usuario.email, reset_token)
    except Exception as e:
        print(f"Error enviando email: {e}")
    
    return {"mensaje": "Si el email está registrado recibirás un enlace en tu correo"}


@router.post("/reset-password", response_model=dict)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Endpoint público para resetear contraseña con token
    """
    usuario = db.query(Usuario).filter(Usuario.reset_token == request.token).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )
    
    if not usuario.reset_token_expira or usuario.reset_token_expira < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado"
        )
    
    # Actualizar contraseña
    usuario.password_hash = hash_password(request.password_nuevo)
    usuario.reset_token = None
    usuario.reset_token_expira = None
    usuario.debe_cambiar_password = False
    db.commit()
    
    return {"mensaje": "Contraseña actualizada correctamente"}
