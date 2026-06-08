from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import Usuario
from app.routers import auth, usuarios, solicitudes, repruebas, danos, clientes, analista, garantias
from app.core.security import decode_token
from app.routers import exportes
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi.responses import RedirectResponse

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Repruebas Técnicas Tigo",
    description="API Backend para gestión de repruebas técnicas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, usar dominio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(solicitudes.router)
app.include_router(repruebas.router)
app.include_router(danos.router)
app.include_router(clientes.router)
app.include_router(analista.router)
app.include_router(garantias.router)
app.include_router(exportes.router)


# Servir archivos estáticos del frontend
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".")
static_dir = os.path.abspath(static_dir)

@app.get("/")
async def root():
    return RedirectResponse(url="/app")

@app.get("/reset-password", response_class=FileResponse)
async def serve_reset_password():
    return FileResponse(os.path.join(static_dir, "reset-password.html"))


@app.get("/")
async def root():
    """Endpoint de prueba"""
    return {
        "mensaje": "Bienvenido al Sistema de Repruebas Técnicas Tigo",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Endpoint para verificar que la API está funcionando"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)