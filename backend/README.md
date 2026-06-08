# Sistema de Repruebas Técnicas Tigo - Backend

## Instalación y Configuración

### 1. Crear entorno virtual (opcional pero recomendado)
```bash
python -m venv venv
source venv/Scripts/activate  # En Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar PostgreSQL
- Crear una base de datos llamada `repruebas_db`
- Actualizar el archivo `.env` con los datos de conexión:
  ```
  DATABASE_URL=postgresql://usuario:password@localhost:5432/repruebas_db
  ```

### 4. Ejecutar seed (datos iniciales)
```bash
python seed.py
```

Este comando crea el usuario administrador:
- Email: `admin@tigo.com`
- Password: `Admin2026*`
- Rol: `supervisor`

### 5. Ejecutar la API
```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`

## Documentación de API

Accede a `http://localhost:8000/docs` para ver la documentación interactiva (Swagger)

## Estructura de carpetas
```
backend/
├── app/
│   ├── main.py              # Aplicación principal
│   ├── database.py          # Configuración de BD
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Esquemas Pydantic
│   ├── core/
│   │   ├── config.py        # Configuración
│   │   └── security.py      # JWT y contraseñas
│   └── routers/
│       ├── auth.py          # Autenticación
│       ├── usuarios.py      # CRUD usuarios
│       ├── solicitudes.py   # Solicitudes de acceso
│       ├── repruebas.py     # Repruebas
│       ├── daños.py         # Daños pendientes/cerrados
│       └── clientes.py      # Clientes
├── requirements.txt
├── .env
└── seed.py
```

## Variables de entorno (.env)
```
DATABASE_URL=postgresql://usuario:password@localhost:5432/repruebas_db
SECRET_KEY=tu_clave_secreta_muy_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```
