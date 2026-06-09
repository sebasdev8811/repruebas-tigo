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
static_dir = os.environ.get("STATIC_DIR", "")
if static_dir and os.path.exists(static_dir):
    from starlette.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/app", response_class=FileResponse)
async def serve_frontend():
    return FileResponse("/app/index.html")

@app.get("/reset-password", response_class=FileResponse)
async def serve_reset_password():
    return FileResponse("/app/reset-password.html")

@app.get("/")
async def root():
    return RedirectResponse(url="/app")

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/debug-path")
async def debug_path():
    import os
    paths = {
        "cwd": os.getcwd(),
        "files_cwd": os.listdir(os.getcwd()),
        "dirname": os.path.dirname(os.path.abspath(__file__))
    }
    return paths

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)