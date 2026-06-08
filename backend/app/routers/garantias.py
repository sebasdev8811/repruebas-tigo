from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Cliente,
    DañoCerrado,
    GestionGarantia,
    Reprueba,
    Ticket,
    Usuario,
)
from app.schemas import (
    GarantiaPendienteItem,
    GestionGarantiaRequest,
    GestionGarantiaResponse,
)
from app.core.security import decode_token
from app.services.tickets import generar_numero_ticket

router = APIRouter(prefix="/garantias", tags=["Garantías"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ESTADOS_FALLA = ["Falla física", "Falla lógica", "Falla física lógica"]
ESTADOS_GESTION = ["pendiente", "escalada", "no_escalada"]


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado",
        )

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    usuario = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido o desactivado",
        )

    return usuario


@router.get("/pendientes", response_model=List[GarantiaPendienteItem])
async def listar_garantias_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Pedidos cerrados con fallas en reprueba que aún no tienen gestión de garantía."""
    gestionados = {
        (g.pedido_id, g.id_reprueba)
        for g in db.query(GestionGarantia.pedido_id, GestionGarantia.id_reprueba).all()
    }

    registros = (
        db.query(Reprueba, DañoCerrado, Cliente)
        .join(DañoCerrado, Reprueba.pedido_id == DañoCerrado.pedido_id)
        .outerjoin(Cliente, DañoCerrado.cedula_cliente == Cliente.cedula_cliente)
        .filter(Reprueba.codigo_estado.in_(ESTADOS_FALLA))
        .all()
    )

    pendientes = []
    for reprueba, dano, cliente in registros:
        clave = (dano.pedido_id, reprueba.id_reprueba)
        if clave in gestionados:
            continue

        pendientes.append(
            GarantiaPendienteItem(
                pedido_id=dano.pedido_id,
                tipo_falla=dano.tipo_falla,
                codigo_estado=reprueba.codigo_estado,
                cedula_cliente=dano.cedula_cliente,
                nombre_cliente=cliente.nombre if cliente else None,
                direccion=cliente.direccion if cliente else None,
                telefono=cliente.telefono if cliente else None,
                ciudad=dano.ciudad,
                departamento=dano.departamento,
                barrio=dano.barrio,
                id_reprueba=reprueba.id_reprueba,
            )
        )

    return pendientes


@router.post("/gestionar", response_model=GestionGarantiaResponse)
async def gestionar_garantia(
    datos: GestionGarantiaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra la gestión de una garantía. Genera ticket si se escala."""
    if datos.estado not in ("escalada", "no_escalada"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido. Valores permitidos: escalada, no_escalada",
        )

    dano = db.query(DañoCerrado).filter(DañoCerrado.pedido_id == datos.pedido_id).first()
    if not dano:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido cerrado no encontrado",
        )

    reprueba = (
        db.query(Reprueba)
        .filter(
            Reprueba.id_reprueba == datos.id_reprueba,
            Reprueba.pedido_id == datos.pedido_id,
        )
        .first()
    )
    if not reprueba:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reprueba no encontrada para el pedido indicado",
        )

    existente = (
        db.query(GestionGarantia)
        .filter(
            GestionGarantia.pedido_id == datos.pedido_id,
            GestionGarantia.id_reprueba == datos.id_reprueba,
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una gestión para este pedido y reprueba",
        )

    ahora = datetime.utcnow()
    gestion = GestionGarantia(
        pedido_id=datos.pedido_id,
        id_reprueba=datos.id_reprueba,
        codigo_estado_reprueba=reprueba.codigo_estado,
        estado=datos.estado,
        observaciones=datos.observaciones,
        id_usuario=current_user.id,
        fecha_gestion=ahora,
    )
    db.add(gestion)
    db.flush()

    if datos.estado == "escalada":
        numero = generar_numero_ticket(db)
        descripcion = (
            f"Garantía escalada para pedido {datos.pedido_id}. "
            f"Estado reprueba: {reprueba.codigo_estado}"
        )
        ticket = Ticket(
            numero_ticket=numero,
            tipo="garantia",
            id_garantia=gestion.id,
            descripcion=descripcion,
            estado="abierto",
            id_usuario=current_user.id,
        )
        db.add(ticket)
        gestion.numero_ticket = numero

    db.commit()
    db.refresh(gestion)
    return gestion


@router.get("/gestiones", response_model=List[GestionGarantiaResponse])
async def listar_gestiones_garantia(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista gestiones de garantía con filtro opcional por estado."""
    query = db.query(GestionGarantia)
    if estado:
        query = query.filter(GestionGarantia.estado == estado)
    return query.order_by(GestionGarantia.fecha_deteccion.desc()).all()
