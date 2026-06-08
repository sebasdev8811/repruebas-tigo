from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
import pandas as pd
import io
from app.database import get_db
from app.models import Reprueba, DañoPendiente, DañoCerrado
from app.schemas import RepruebaResponse, DashboardResumen
from app.core.security import decode_token
from app.models import Usuario
from datetime import date as date_today

router = APIRouter(prefix="/repruebas", tags=["Repruebas"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Dependencia para verificar autenticación"""
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


@router.post("/carga")
async def cargar_repruebas(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Carga un archivo CSV o Excel con repruebas y las guarda en la BD
    El archivo debe tener columnas: pedido_id, codigo_estado, fecha_reprueba
    """
    try:
        contents = await file.read()
        
        # Detectar tipo de archivo
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de archivo no válido. Usa CSV o Excel"
            )
        
        # Validar columnas requeridas
        required_columns = ['id_reprueba', 'pedido_id', 'codigo_estado']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo debe contener las columnas: {', '.join(required_columns)}"
            )
        
    # Insertar registros
        registros_insertados = 0
        registros_omitidos = 0
        for _, row in df.iterrows():
            try:
                id_rep = int(row['id_reprueba']) if pd.notna(row['id_reprueba']) else None
                if not id_rep:
                    continue
                    
                existente = db.query(Reprueba).filter(Reprueba.id_reprueba == id_rep).first()
                if existente:
                    registros_omitidos += 1
                    continue
                    
                reprueba = Reprueba(
                id_reprueba=id_rep,
                pedido_id=int(row['pedido_id']) if pd.notna(row['pedido_id']) else None,
                codigo_estado=str(row['codigo_estado']) if pd.notna(row['codigo_estado']) else None,
                 fecha_reprueba=date_today.today()
)
                db.add(reprueba)
                db.flush()
                registros_insertados += 1
            except Exception as e:
                continue

        db.commit()
        
        return {
            "mensaje": "Archivo cargado exitosamente",
            "registros_insertados": registros_insertados,
            "registros_omitidos": registros_omitidos
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar el archivo: {str(e)}"
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al procesar el archivo: {str(e)}"
        )


@router.get("", response_model=List[RepruebaResponse])
async def listar_repruebas(
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    pedido_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar repruebas con filtros opcionales por fecha y pedido_id
    """
    query = db.query(Reprueba)
    
    if fecha_inicio:
        query = query.filter(Reprueba.fecha_reprueba >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Reprueba.fecha_reprueba <= fecha_fin)
    if pedido_id:
        query = query.filter(Reprueba.pedido_id == pedido_id)
    
    repruebas = query.all()
    return repruebas

@router.post("/carga-clientes")
async def cargar_clientes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != "supervisor":
        raise HTTPException(status_code=403, detail="Solo supervisores pueden cargar datos maestros")
    
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Formato no válido. Usa CSV o Excel")

        required_columns = ['cedula_cliente', 'nombre', 'direccion', 'telefono', 'ciudad', 'departamento', 'barrio']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"El archivo debe contener: {', '.join(required_columns)}")

        from app.models import Cliente
        registros_insertados = 0
        for _, row in df.iterrows():
            try:
                existente = db.query(Cliente).filter(Cliente.cedula_cliente == int(row['cedula_cliente'])).first()
                if existente:
                    continue
                cliente = Cliente(
                    cedula_cliente=int(row['cedula_cliente']),
                    nombre=str(row['nombre']),
                    direccion=str(row['direccion']),
                    telefono=str(row['telefono']),
                    ciudad=str(row['ciudad']),
                    departamento=str(row['departamento']),
                    barrio=str(row['barrio'])
                )
                db.add(cliente)
                registros_insertados += 1
            except:
                continue

        db.commit()
        return {"mensaje": "Clientes cargados exitosamente", "registros_insertados": registros_insertados}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al procesar: {str(e)}")


@router.post("/carga-danos-pendientes")
async def cargar_danos_pendientes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != "supervisor":
        raise HTTPException(status_code=403, detail="Solo supervisores pueden cargar datos maestros")

    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Formato no válido. Usa CSV o Excel")

        required_columns = ['pedido_id', 'tipo_falla', 'cedula_cliente', 'estado', 'ciudad', 'departamento', 'barrio', 'nodo', 'cmts', 'amplificador', 'tap']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"El archivo debe contener: {', '.join(required_columns)}")

        registros_insertados = 0
        for _, row in df.iterrows():
            try:
                existente = db.query(DañoPendiente).filter(DañoPendiente.pedido_id == int(row['pedido_id'])).first()
                if existente:
                    continue
                dano = DañoPendiente(
                    pedido_id=int(row['pedido_id']),
                    id_prueba=int(row['id_prueba']) if 'id_prueba' in df.columns and pd.notna(row['id_prueba']) else None,
                    fecha_reporte=pd.to_datetime(row['fecha_reporte']).date() if 'fecha_reporte' in df.columns and pd.notna(row['fecha_reporte']) else None,
                    fecha_ingreso=pd.to_datetime(row['fecha_ingreso']).date() if 'fecha_ingreso' in df.columns and pd.notna(row['fecha_ingreso']) else None,
                    tipo_falla=str(row['tipo_falla']),
                    descripcion=str(row['descripcion']) if 'descripcion' in df.columns and pd.notna(row['descripcion']) else None,
                    cedula_cliente=int(row['cedula_cliente']),
                    estado=str(row['estado']),
                    ciudad=str(row['ciudad']),
                    departamento=str(row['departamento']),
                    barrio=str(row['barrio']),
                    nodo=str(row['nodo']),
                    cmts=str(row['cmts']),
                    amplificador=str(row['amplificador']),
                    tap=str(row['tap'])
                )
                db.add(dano)
                registros_insertados += 1
            except:
                continue

        db.commit()
        return {"mensaje": "Daños pendientes cargados exitosamente", "registros_insertados": registros_insertados}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al procesar: {str(e)}")


@router.post("/carga-danos-cerrados")
async def cargar_danos_cerrados(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != "supervisor":
        raise HTTPException(status_code=403, detail="Solo supervisores pueden cargar datos maestros")

    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Formato no válido. Usa CSV o Excel")

        required_columns = ['pedido_id', 'tipo_falla', 'cedula_cliente', 'ciudad', 'departamento', 'barrio', 'nodo', 'cmts', 'amplificador', 'tap']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"El archivo debe contener: {', '.join(required_columns)}")

        registros_insertados = 0
        for _, row in df.iterrows():
            try:
                existente = db.query(DañoCerrado).filter(DañoCerrado.pedido_id == int(row['pedido_id'])).first()
                if existente:
                    continue
                dano = DañoCerrado(
                    pedido_id=int(row['pedido_id']),
                    id_prueba=int(row['id_prueba']) if 'id_prueba' in df.columns and pd.notna(row['id_prueba']) else None,
                    fecha_cierre=pd.to_datetime(row['fecha_cierre']).date() if 'fecha_cierre' in df.columns and pd.notna(row['fecha_cierre']) else None,
                    tipo_falla=str(row['tipo_falla']),
                    descripcion=str(row['descripcion']) if 'descripcion' in df.columns and pd.notna(row['descripcion']) else None,
                    cedula_cliente=int(row['cedula_cliente']),
                    observaciones_garantia=str(row['observaciones_garantia']) if 'observaciones_garantia' in df.columns and pd.notna(row['observaciones_garantia']) else None,
                    ciudad=str(row['ciudad']),
                    departamento=str(row['departamento']),
                    barrio=str(row['barrio']),
                    nodo=str(row['nodo']),
                    cmts=str(row['cmts']),
                    amplificador=str(row['amplificador']),
                    tap=str(row['tap'])
                )
                db.add(dano)
                registros_insertados += 1
            except:
                continue

        db.commit()
        return {"mensaje": "Daños cerrados cargados exitosamente", "registros_insertados": registros_insertados}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al procesar: {str(e)}")