import json
from collections import defaultdict
from datetime import datetime
from typing import List, Optional
from sqlalchemy import func

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    DañoPendiente,
    GestionAnalista,
    Reprueba,
    Ticket,
    Usuario,
)
from app.schemas import (
    FallaMasivaItem,
    GestionAnalistaRequest,
    GestionAnalistaResponse,
    ResumenRepruebaItem,
    ResumenRepruebasResponse,
    TicketResponse,
)
from app.core.security import decode_token
from app.services.tickets import generar_numero_ticket

router = APIRouter(prefix="/analista", tags=["Analista"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ESTADOS_REPRUEBA = ["OK", "Falla física", "Falla lógica", "Falla física lógica"]
ESTADOS_FALLA = ["Falla física", "Falla lógica", "Falla física lógica"]
ELEMENTOS_RED = ["nodo", "cmts", "amplificador"]
ESTADOS_GESTION = ["no_gestionado", "gestionado", "escalado"]


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


def _gestion_to_response(gestion: GestionAnalista) -> GestionAnalistaResponse:
    return GestionAnalistaResponse(
        id=gestion.id,
        tipo=gestion.tipo,
        elemento_red=gestion.elemento_red,
        valor_elemento=gestion.valor_elemento,
        total_pedidos=gestion.total_pedidos,
        pedidos_afectados=json.loads(gestion.pedidos_afectados),
        estado=gestion.estado,
        observaciones=gestion.observaciones,
        id_usuario=gestion.id_usuario,
        fecha_deteccion=gestion.fecha_deteccion,
        fecha_gestion=gestion.fecha_gestion,
        numero_ticket=gestion.numero_ticket,
    )


@router.get("/resumen-repruebas", response_model=ResumenRepruebasResponse)
async def resumen_repruebas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Agrupa repruebas por estado para gráficas del dashboard del analista."""
    conteos = {estado: 0 for estado in ESTADOS_REPRUEBA}
    conteos["Sin reprueba"] = 0

    repruebas = db.query(Reprueba.codigo_estado).all()
    for (codigo_estado,) in repruebas:
        if codigo_estado in conteos:
            conteos[codigo_estado] += 1
        elif not codigo_estado:
            conteos["Sin reprueba"] += 1
        else:
            conteos[codigo_estado] = conteos.get(codigo_estado, 0) + 1

    pedidos_con_reprueba = {
        r.pedido_id
        for r in db.query(Reprueba.pedido_id).filter(Reprueba.pedido_id.isnot(None)).all()
    }
    total_pendientes = db.query(DañoPendiente.pedido_id).count()
    conteos["Sin reprueba"] += total_pendientes - len(pedidos_con_reprueba)

    resumen = [ResumenRepruebaItem(estado=k, cantidad=v) for k, v in conteos.items()]
    total = sum(item.cantidad for item in resumen)

    return ResumenRepruebasResponse(resumen=resumen, total=total)

@router.get("/fallas-masivas", response_model=List[FallaMasivaItem])
async def detectar_fallas_masivas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Detecta elementos de red con 3 o más pedidos con fallas en la reprueba más reciente."""
    
    # Obtener la reprueba más reciente por pedido
    subquery = (
        db.query(
            Reprueba.pedido_id,
            func.max(Reprueba.fecha_reprueba).label("fecha_max")
        )
        .group_by(Reprueba.pedido_id)
        .subquery()
    )

    # Traer solo la reprueba más reciente de cada pedido
    registros = (
        db.query(Reprueba, DañoPendiente)
        .join(subquery, (Reprueba.pedido_id == subquery.c.pedido_id) & 
                        (Reprueba.fecha_reprueba == subquery.c.fecha_max))
        .join(DañoPendiente, Reprueba.pedido_id == DañoPendiente.pedido_id)
        .filter(Reprueba.codigo_estado.in_(ESTADOS_FALLA))
        .all()
    )

    agrupados: dict[tuple[str, str, str], set[int]] = defaultdict(set)

    for reprueba, dano in registros:
        for elemento in ELEMENTOS_RED:
            valor = getattr(dano, elemento, None)
            ciudad = getattr(dano, 'ciudad', None)
        if valor and str(valor).strip() and ciudad:
                agrupados[(elemento, str(valor).strip(), str(ciudad).strip())].add(dano.pedido_id)

    resultados = []
    for (elemento_red, valor_elemento, ciudad), pedidos in sorted(agrupados.items()):
        if len(pedidos) >= 3:
            pedido_ids = sorted(pedidos)
            resultados.append(
                FallaMasivaItem(
                    elemento_red=elemento_red,
                    valor_elemento=f"{valor_elemento} ({ciudad})",
                    total_pedidos=len(pedido_ids),
                    pedido_ids=pedido_ids,
                )
            )

    return resultados

@router.post("/gestionar", response_model=GestionAnalistaResponse)
async def gestionar_falla_masiva(
    datos: GestionAnalistaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea o actualiza una gestión de falla masiva. Genera ticket si se escala."""
    if datos.estado not in ESTADOS_GESTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Valores permitidos: {', '.join(ESTADOS_GESTION)}",
        )

    if datos.elemento_red not in ELEMENTOS_RED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Elemento de red inválido. Valores permitidos: {', '.join(ELEMENTOS_RED)}",
        )

    if not datos.pedidos_afectados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe incluir al menos un pedido afectado",
        )

    ahora = datetime.utcnow()
    pedidos_json = json.dumps(datos.pedidos_afectados)

    if datos.id_gestion:
        gestion = db.query(GestionAnalista).filter(GestionAnalista.id == datos.id_gestion).first()
        if not gestion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gestión no encontrada",
            )
        gestion.elemento_red = datos.elemento_red
        gestion.valor_elemento = datos.valor_elemento
        gestion.total_pedidos = len(datos.pedidos_afectados)
        gestion.pedidos_afectados = pedidos_json
        gestion.estado = datos.estado
        gestion.observaciones = datos.observaciones
        gestion.id_usuario = current_user.id
    else:
        gestion = GestionAnalista(
            tipo="falla_masiva",
            elemento_red=datos.elemento_red,
            valor_elemento=datos.valor_elemento,
            total_pedidos=len(datos.pedidos_afectados),
            pedidos_afectados=pedidos_json,
            estado=datos.estado,
            observaciones=datos.observaciones,
            id_usuario=current_user.id,
        )
        db.add(gestion)
        db.flush()

    if datos.estado in ("gestionado", "escalado"):
        gestion.fecha_gestion = ahora

    if datos.estado == "escalado":
        if not gestion.numero_ticket:
            numero = generar_numero_ticket(db)
            descripcion = (
                f"Falla masiva en {datos.elemento_red} {datos.valor_elemento}. "
                f"Pedidos afectados: {', '.join(str(p) for p in datos.pedidos_afectados)}"
            )
            ticket = Ticket(
                numero_ticket=numero,
                tipo="falla_masiva",
                id_gestion=gestion.id,
                descripcion=descripcion,
                estado="abierto",
                id_usuario=current_user.id,
            )
            db.add(ticket)
            gestion.numero_ticket = numero

    db.commit()
    db.refresh(gestion)
    return _gestion_to_response(gestion)


@router.get("/gestiones", response_model=List[GestionAnalistaResponse])
async def listar_gestiones(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista gestiones del analista con filtro opcional por estado."""
    query = db.query(GestionAnalista)
    if estado:
        query = query.filter(GestionAnalista.estado == estado)
    gestiones = query.order_by(GestionAnalista.fecha_deteccion.desc()).all()
    return [_gestion_to_response(g) for g in gestiones]


@router.get("/tickets", response_model=List[TicketResponse])
async def listar_tickets(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista todos los tickets generados."""
    tickets = db.query(Ticket).order_by(Ticket.fecha_creacion.desc()).all()
    return tickets
