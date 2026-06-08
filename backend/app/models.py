from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)  # analista, supervisor, garantias
    zona = Column(String(50))
    activo = Column(Boolean, default=True)
    debe_cambiar_password = Column(Boolean, default=True)
    reset_token = Column(String(100), nullable=True)
    reset_token_expira = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class SolicitudAcceso(Base):
    __tablename__ = "solicitudes_acceso"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    zona = Column(String(50), nullable=False)
    rol_solicitado = Column(String(20), nullable=False)  # analista, garantias
    motivo = Column(Text)
    estado = Column(String(20), default="pendiente")  # pendiente, aprobada, rechazada
    password_temporal = Column(String(50), nullable=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)


class Cliente(Base):
    __tablename__ = "cliente"
    
    cedula_cliente = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(150))
    telefono = Column(String(20))
    ciudad = Column(String(50))
    departamento = Column(String(50))
    barrio = Column(String(50))
    
    # Relaciones
    daños_pendientes = relationship("DañoPendiente", back_populates="cliente")
    daños_cerrados = relationship("DañoCerrado", back_populates="cliente")


class DañoPendiente(Base):
    __tablename__ = "daños_pendientes"
    
    pedido_id = Column(Integer, primary_key=True, index=True)
    id_prueba = Column(Integer)
    fecha_reporte = Column(Date)
    fecha_ingreso = Column(Date)
    tipo_falla = Column(String(50))
    descripcion = Column(Text)
    cedula_cliente = Column(Integer, ForeignKey("cliente.cedula_cliente"))
    estado = Column(String(20))
    ciudad = Column(String(50))
    departamento = Column(String(50))
    barrio = Column(String(50))
    nodo = Column(String(50))
    cmts = Column(String(50))
    amplificador = Column(String(50))
    tap = Column(String(50))
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="daños_pendientes")
    repruebas = relationship("Reprueba", back_populates="daño_pendiente", foreign_keys="[Reprueba.pedido_id]")


class DañoCerrado(Base):
    __tablename__ = "daños_cerrados"
    
    pedido_id = Column(Integer, primary_key=True, index=True)
    id_prueba = Column(Integer)
    fecha_cierre = Column(Date)
    tipo_falla = Column(String(50))
    descripcion = Column(Text)
    cedula_cliente = Column(Integer, ForeignKey("cliente.cedula_cliente"))
    observaciones_garantia = Column(Text)
    ciudad = Column(String(50))
    departamento = Column(String(50))
    barrio = Column(String(50))
    nodo = Column(String(50))
    cmts = Column(String(50))
    amplificador = Column(String(50))
    tap = Column(String(50))
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="daños_cerrados")
    repruebas = relationship("Reprueba", back_populates="daño_cerrado", foreign_keys="[Reprueba.pedido_id_cerrado]")


class Reprueba(Base):
    __tablename__ = "repruebas"
    
    id_reprueba = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("daños_pendientes.pedido_id"), nullable=True)
    pedido_id_cerrado = Column(Integer, ForeignKey("daños_cerrados.pedido_id"), nullable=True)
    codigo_estado = Column(String(20))
    fecha_reprueba = Column(Date)
    
    # Relaciones
    daño_pendiente = relationship("DañoPendiente", back_populates="repruebas", foreign_keys=[pedido_id])
    daño_cerrado = relationship("DañoCerrado", back_populates="repruebas", foreign_keys=[pedido_id_cerrado])


class GestionAnalista(Base):
    __tablename__ = "gestion_analista"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)
    elemento_red = Column(String(20), nullable=False)
    valor_elemento = Column(String(50), nullable=False)
    total_pedidos = Column(Integer, nullable=False)
    pedidos_afectados = Column(Text, nullable=False)
    estado = Column(String(20), default="no_gestionado")
    observaciones = Column(Text)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_deteccion = Column(DateTime, default=datetime.utcnow)
    fecha_gestion = Column(DateTime, nullable=True)
    numero_ticket = Column(String(20), nullable=True)

    usuario = relationship("Usuario")
    ticket = relationship("Ticket", back_populates="gestion_analista", uselist=False)


class GestionGarantia(Base):
    __tablename__ = "gestion_garantia"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("daños_cerrados.pedido_id"), nullable=False)
    id_reprueba = Column(Integer, ForeignKey("repruebas.id_reprueba"), nullable=False)
    codigo_estado_reprueba = Column(String(20), nullable=False)
    estado = Column(String(20), default="pendiente")
    observaciones = Column(Text)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_deteccion = Column(DateTime, default=datetime.utcnow)
    fecha_gestion = Column(DateTime, nullable=True)
    numero_ticket = Column(String(20), nullable=True)

    daño_cerrado = relationship("DañoCerrado")
    reprueba = relationship("Reprueba")
    usuario = relationship("Usuario")
    ticket = relationship("Ticket", back_populates="gestion_garantia", uselist=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero_ticket = Column(String(20), unique=True, nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    id_gestion = Column(Integer, ForeignKey("gestion_analista.id"), nullable=True)
    id_garantia = Column(Integer, ForeignKey("gestion_garantia.id"), nullable=True)
    descripcion = Column(Text)
    estado = Column(String(20), default="abierto")
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario")
    gestion_analista = relationship("GestionAnalista", back_populates="ticket")
    gestion_garantia = relationship("GestionGarantia", back_populates="ticket")
