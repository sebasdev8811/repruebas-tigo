from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


# ==================== Autenticación ====================
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario_id: int
    nombre: str
    rol: str
    debe_cambiar_password: bool


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    zona: Optional[str]
    activo: bool
    debe_cambiar_password: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True


# ==================== Usuarios ====================
class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    rol: str  # analista, supervisor, garantias
    zona: str


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    zona: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    password_actual: str
    password_nuevo: str


# ==================== Solicitudes de Acceso ====================
class SolicitudAccesoCreate(BaseModel):
    nombre: str
    email: str
    zona: str
    rol_solicitado: str  # analista, garantias
    motivo: str


class SolicitudAccesoResponse(BaseModel):
    id: int
    nombre: str
    email: str
    zona: str
    rol_solicitado: str
    motivo: str
    estado: str
    password_temporal: Optional[str] = None
    fecha_solicitud: datetime
    
    class Config:
        from_attributes = True


class SolicitudAccesoUpdate(BaseModel):
    estado: str  # aprobada, rechazada


# ==================== Cliente ====================
class ClienteCreate(BaseModel):
    cedula_cliente: int
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    barrio: Optional[str] = None


class ClienteResponse(BaseModel):
    cedula_cliente: int
    nombre: str
    direccion: Optional[str]
    telefono: Optional[str]
    ciudad: Optional[str]
    departamento: Optional[str]
    barrio: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== Daños Pendientes ====================
class DañoPendienteCreate(BaseModel):
    pedido_id: int
    id_prueba: Optional[int] = None
    fecha_reporte: Optional[date] = None
    fecha_ingreso: Optional[date] = None
    tipo_falla: Optional[str] = None
    descripcion: Optional[str] = None
    cedula_cliente: int
    estado: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    barrio: Optional[str] = None
    nodo: Optional[str] = None
    cmts: Optional[str] = None
    amplificador: Optional[str] = None
    tap: Optional[str] = None


class DañoPendienteResponse(BaseModel):
    pedido_id: int
    id_prueba: Optional[int]
    fecha_reporte: Optional[date]
    fecha_ingreso: Optional[date]
    tipo_falla: Optional[str]
    descripcion: Optional[str]
    cedula_cliente: int
    estado: Optional[str]
    ciudad: Optional[str]
    departamento: Optional[str]
    barrio: Optional[str]
    nodo: Optional[str]
    cmts: Optional[str]
    amplificador: Optional[str]
    tap: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== Daños Cerrados ====================
class DañoCerradoCreate(BaseModel):
    pedido_id: int
    id_prueba: Optional[int] = None
    fecha_cierre: Optional[date] = None
    tipo_falla: Optional[str] = None
    descripcion: Optional[str] = None
    cedula_cliente: int
    observaciones_garantia: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    barrio: Optional[str] = None
    nodo: Optional[str] = None
    cmts: Optional[str] = None
    amplificador: Optional[str] = None
    tap: Optional[str] = None


class DañoCerradoResponse(BaseModel):
    pedido_id: int
    id_prueba: Optional[int]
    fecha_cierre: Optional[date]
    tipo_falla: Optional[str]
    descripcion: Optional[str]
    cedula_cliente: int
    observaciones_garantia: Optional[str]
    ciudad: Optional[str]
    departamento: Optional[str]
    barrio: Optional[str]
    nodo: Optional[str]
    cmts: Optional[str]
    amplificador: Optional[str]
    tap: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== Repruebas ====================
class RepruebaCreate(BaseModel):
    pedido_id: Optional[int] = None
    codigo_estado: Optional[str] = None
    fecha_reprueba: Optional[date] = None


class RepruebaResponse(BaseModel):
    id_reprueba: int
    pedido_id: Optional[int]
    codigo_estado: Optional[str]
    fecha_reprueba: Optional[date]
    
    class Config:
        from_attributes = True


# ==================== Dashboard ====================
class DashboardResumen(BaseModel):
    total_repruebas: int
    daños_pendientes: int
    daños_cerrados: int
    alertas: int  # daños pendientes con más de 5 repruebas


# ==================== Analista ====================
class ResumenRepruebaItem(BaseModel):
    estado: str
    cantidad: int


class ResumenRepruebasResponse(BaseModel):
    resumen: List[ResumenRepruebaItem]
    total: int


class FallaMasivaItem(BaseModel):
    elemento_red: str
    valor_elemento: str
    total_pedidos: int
    pedido_ids: List[int]


class GestionAnalistaRequest(BaseModel):
    id_gestion: Optional[int] = None
    elemento_red: str
    valor_elemento: str
    pedidos_afectados: List[int]
    estado: str
    observaciones: Optional[str] = None


class GestionAnalistaResponse(BaseModel):
    id: int
    tipo: str
    elemento_red: str
    valor_elemento: str
    total_pedidos: int
    pedidos_afectados: List[int]
    estado: str
    observaciones: Optional[str]
    id_usuario: int
    fecha_deteccion: datetime
    fecha_gestion: Optional[datetime]
    numero_ticket: Optional[str]

    class Config:
        from_attributes = True


class TicketResponse(BaseModel):
    id: int
    numero_ticket: str
    tipo: str
    id_gestion: Optional[int]
    id_garantia: Optional[int]
    descripcion: Optional[str]
    estado: str
    id_usuario: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ==================== Garantías ====================
class GarantiaPendienteItem(BaseModel):
    pedido_id: int
    tipo_falla: Optional[str]
    codigo_estado: Optional[str]
    cedula_cliente: Optional[int]
    nombre_cliente: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]
    ciudad: Optional[str]
    departamento: Optional[str]
    barrio: Optional[str]
    id_reprueba: int


class GestionGarantiaRequest(BaseModel):
    pedido_id: int
    id_reprueba: int
    estado: str
    observaciones: Optional[str] = None


class GestionGarantiaResponse(BaseModel):
    id: int
    pedido_id: int
    id_reprueba: int
    codigo_estado_reprueba: str
    estado: str
    observaciones: Optional[str]
    id_usuario: int
    fecha_deteccion: datetime
    fecha_gestion: Optional[datetime]
    numero_ticket: Optional[str]

    class Config:
        from_attributes = True
