from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models import DañoPendiente, DañoCerrado, Reprueba, Usuario
from app.schemas import DañoPendienteResponse, DañoCerradoResponse, DashboardResumen
from app.core.security import decode_token

router = APIRouter(prefix="/danos", tags=["Daños"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependencia para verificar autenticación"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado"
        )

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


@router.get("/pendientes", response_model=List[DañoPendienteResponse])
async def listar_daños_pendientes(
    ciudad: Optional[str] = None,
    departamento: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar daños pendientes con filtros opcionales
    """
    query = db.query(DañoPendiente)
    
    if ciudad:
        query = query.filter(DañoPendiente.ciudad == ciudad)
    if departamento:
        query = query.filter(DañoPendiente.departamento == departamento)
    if estado:
        query = query.filter(DañoPendiente.estado == estado)
    
    daños = query.all()
    return daños


@router.get("/cerrados", response_model=List[DañoCerradoResponse])
async def listar_daños_cerrados(
    ciudad: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar daños cerrados con filtros opcionales
    """
    query = db.query(DañoCerrado)
    
    if ciudad:
        query = query.filter(DañoCerrado.ciudad == ciudad)
    if fecha_inicio:
        query = query.filter(DañoCerrado.fecha_cierre >= fecha_inicio)
    if fecha_fin:
        query = query.filter(DañoCerrado.fecha_cierre <= fecha_fin)
    
    daños = query.all()
    return daños


@router.get("/dashboard/resumen", response_model=DashboardResumen)
async def obtener_resumen_dashboard(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    from app.models import GestionGarantia, GestionAnalista

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado")

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    usuario_id = int(payload.get("sub"))
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido o desactivado")

    # Total de repruebas
    total_repruebas = db.query(func.count(Reprueba.id_reprueba)).scalar() or 0

    # Gestiones de garantía registradas
    from app.models import GestionGarantia as GG
    gestionados_ids = db.query(GG.pedido_id, GG.id_reprueba).all()
    gestionados_set = {(g.pedido_id, g.id_reprueba) for g in gestionados_ids}
    ESTADOS_FALLA = ['Falla física', 'Falla lógica', 'Falla física lógica']
    total_con_falla = db.query(Reprueba).join(
    DañoCerrado, Reprueba.pedido_id == DañoCerrado.pedido_id
    ).filter(Reprueba.codigo_estado.in_(ESTADOS_FALLA)).all()
    total_garantias = sum(1 for r in total_con_falla 
                if (r.pedido_id, r.id_reprueba) not in gestionados_set)

    # Fallas masivas detectadas sin gestionar
    alertas = db.query(func.count(GestionAnalista.id)).filter(
        GestionAnalista.estado == 'no_gestionado'
    ).scalar() or 0

    # Daños cerrados
    daños_cerrados = db.query(func.count(DañoCerrado.pedido_id)).scalar() or 0

    return DashboardResumen(
        total_repruebas=total_repruebas,
        daños_pendientes=total_garantias,
        daños_cerrados=daños_cerrados,
        alertas=alertas
    )

@router.get("/dashboard/repruebas-por-estado")
async def repruebas_por_estado(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Conteo de repruebas agrupadas por estado para gráfica de dona"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    resultados = db.query(
        Reprueba.codigo_estado,
        func.count(Reprueba.id_reprueba).label("cantidad")
    ).group_by(Reprueba.codigo_estado).all()

    return [{"estado": r.codigo_estado, "cantidad": r.cantidad} for r in resultados]


@router.get("/dashboard/garantias-por-mes")
async def garantias_por_mes(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Garantías gestionadas agrupadas por mes"""
    from app.models import GestionGarantia
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    resultados = db.query(
        func.to_char(GestionGarantia.fecha_gestion, 'YYYY-MM').label("mes"),
        func.count(GestionGarantia.id).label("cantidad")
    ).filter(
        GestionGarantia.fecha_gestion != None
    ).group_by("mes").order_by("mes").all()

    return [{"mes": r.mes, "cantidad": r.cantidad} for r in resultados]


@router.get("/dashboard/fallas-por-mes")
async def fallas_por_mes(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Fallas masivas gestionadas agrupadas por mes"""
    from app.models import GestionAnalista
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    resultados = db.query(
        func.to_char(GestionAnalista.fecha_deteccion, 'YYYY-MM').label("mes"),
        func.count(GestionAnalista.id).label("cantidad")
    ).filter(
        GestionAnalista.fecha_deteccion != None
    ).group_by("mes").order_by("mes").all()

    return [{"mes": r.mes, "cantidad": r.cantidad} for r in resultados]

@router.get("/dashboard/alertas-count")
async def alertas_count(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    from app.models import GestionAnalista
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Contar gestiones no gestionadas
    no_gestionadas = db.query(func.count(GestionAnalista.id)).filter(
        GestionAnalista.estado == 'no_gestionado'
    ).scalar() or 0

    # Traer fallas masivas detectadas actualmente
    subquery = (
        db.query(
            Reprueba.pedido_id,
            func.max(Reprueba.fecha_reprueba).label("fecha_max")
        ).group_by(Reprueba.pedido_id).subquery()
    )

    registros_falla = (
        db.query(DañoPendiente.nodo, DañoPendiente.cmts, DañoPendiente.amplificador, DañoPendiente.tap, DañoPendiente.pedido_id)
        .join(subquery, DañoPendiente.pedido_id == subquery.c.pedido_id)
        .join(Reprueba, (Reprueba.pedido_id == subquery.c.pedido_id) & (Reprueba.fecha_reprueba == subquery.c.fecha_max))
        .filter(Reprueba.codigo_estado.in_(['Falla física', 'Falla lógica', 'Falla física lógica']))
        .all()
    )

    from collections import defaultdict
    agrupados = defaultdict(set)
    for r in registros_falla:
        for val in [r.nodo, r.cmts, r.amplificador, r.tap]:
            if val:
                agrupados[val].add(r.pedido_id)

    total_detectadas = sum(1 for pedidos in agrupados.values() if len(pedidos) >= 3)
    
    # Elementos ya gestionados
    gestionados = db.query(GestionAnalista.valor_elemento).filter(
        GestionAnalista.estado.in_(['gestionado', 'escalado'])
    ).all()
    gestionados_set = {g.valor_elemento for g in gestionados}

    sin_gestion = sum(1 for elemento, pedidos in agrupados.items() 
                     if len(pedidos) >= 3 and elemento not in gestionados_set)

    return {"alertas": sin_gestion}

@router.get("/dashboard/reportes")
async def reportes_periodo(
    periodo: str = "semana",
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    from app.models import GestionGarantia, GestionAnalista
    from datetime import datetime, timedelta
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    hoy = datetime.today().date()
    
    if periodo == "semana":
        fecha_inicio = hoy - timedelta(days=7)
        formato = "Día %d/%m"
        trunc = "day"
    elif periodo == "mes":
        fecha_inicio = hoy - timedelta(days=30)
        formato = "Sem %W"
        trunc = "week"
    else:  # trimestre
        fecha_inicio = hoy - timedelta(days=90)
        formato = "%b %Y"
        trunc = "month"

    # Total repruebas del período
    total_repruebas = db.query(func.count(Reprueba.id_reprueba)).filter(
        Reprueba.fecha_reprueba >= fecha_inicio
    ).scalar() or 0

    # Total garantías del período
    total_garantias = db.query(func.count(GestionGarantia.id)).filter(
        func.date(GestionGarantia.fecha_gestion) >= fecha_inicio
    ).scalar() or 0

    # Total fallas masivas del período
    total_fallas = db.query(func.count(GestionAnalista.id)).filter(
        func.date(GestionAnalista.fecha_deteccion) >= fecha_inicio
    ).scalar() or 0

    # Repruebas agrupadas por período
    if trunc == "day":
        grupo = func.to_char(Reprueba.fecha_reprueba, 'DD/MM')
    elif trunc == "week":
        grupo = func.to_char(Reprueba.fecha_reprueba, 'IW')
    else:
        grupo = func.to_char(Reprueba.fecha_reprueba, 'Mon YYYY')

    repruebas_agrupadas = db.query(
        grupo.label("etiqueta"),
        func.count(Reprueba.id_reprueba).label("cantidad")
    ).filter(
        Reprueba.fecha_reprueba >= fecha_inicio
    ).group_by("etiqueta").order_by("etiqueta").all()

    return {
        "total_repruebas": total_repruebas,
        "total_garantias": total_garantias,
        "total_fallas": total_fallas,
        "grafica": [{"etiqueta": r.etiqueta, "cantidad": r.cantidad} for r in repruebas_agrupadas]
    }