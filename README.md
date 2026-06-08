# Sistema de Repruebas Técnicas — Tigo

Sistema web interno para gestionar repruebas de servicios técnicos. Permite detectar fallas recurrentes en elementos de red, gestionar garantías y tomar decisiones técnicas basadas en datos reales.

---

## Stack

- **Backend:** Python + FastAPI + SQLAlchemy
- **Base de datos:** PostgreSQL
- **Autenticación:** JWT con bcrypt (tokens de 8 horas)
- **Frontend:** HTML + CSS + JavaScript vanilla + Chart.js

---

## Cómo levantar el sistema

Se necesitan dos terminales abiertas al mismo tiempo.

**Terminal 1 — Backend:**
```bash
cd C:\Users\sebas\OneDrive\Desktop\Repruebastigo\backend
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd C:\Users\sebas\OneDrive\Desktop\Repruebastigo
python -m http.server 5500
```

Luego abrir en el navegador: http://localhost:5500

La documentación de la API queda en: http://localhost:8000/docs

---

## Primera vez que se instala

1. Instalar PostgreSQL y crear la base de datos:
```sql
CREATE DATABASE repruebas_db;
```

2. Configurar el archivo `backend/.env`:
```
DATABASE_URL=postgresql://postgres:TU_CONTRASEÑA@localhost:5432/repruebas_db
SECRET_KEY=clave_secreta_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
MAIL_USERNAME=correo@gmail.com
MAIL_PASSWORD=contraseña_de_aplicacion_gmail
MAIL_FROM=correo@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

3. Instalar dependencias:
```bash
cd backend
pip install -r requirements.txt
pip install bcrypt==4.0.1
```

4. Crear el usuario administrador inicial:
```bash
python seed.py
```

5. Levantar el sistema con los comandos de arriba.

**Credenciales iniciales:**
- Email: admin@tigo.com
- Contraseña: Admin2026*

---

## Roles

El sistema tiene tres roles con accesos diferentes:

**Supervisor** — acceso completo. Puede cargar datos maestros (daños pendientes y cerrados), gestionar usuarios, aprobar solicitudes de acceso y ver todos los módulos.

**Analista** — puede cargar repruebas, ver fallas masivas detectadas, gestionar y escalar fallas, generar tickets.

**Garantías** — puede ver los daños cerrados con falla en reprueba, gestionar garantías y escalar casos.

---

## Flujo del sistema

El flujo normal de uso es:

1. El supervisor carga daños pendientes y daños cerrados desde archivos CSV/Excel (módulo Analista, sección "Carga de datos maestros").
2. El analista carga las repruebas del período desde un archivo CSV/Excel (módulo Analista, sección "Carga de repruebas"). El archivo debe tener las columnas: `id_reprueba`, `pedido_id`, `codigo_estado`. La fecha se asigna automáticamente al momento de la carga.
3. El sistema detecta automáticamente fallas masivas: elementos de red (nodo, CMTS, amplificador, tap) donde 3 o más pedidos tienen falla en su reprueba más reciente.
4. El analista revisa cada falla masiva, registra sus observaciones y la marca como gestionada o escalada. Si escala, se genera un ticket automático (formato TKT-YYYYMMDD-XXXX).
5. El módulo de Garantías muestra los daños cerrados que tienen reprueba con Falla física, Falla lógica o Falla física lógica. El encargado gestiona cada caso y decide si escala o no.

---

## Códigos de estado de reprueba

Los únicos valores válidos para `codigo_estado` son:
- `OK`
- `Falla física`
- `Falla lógica`
- `Falla física lógica`
- `Sin reprueba`

---

## Estructura de archivos

```
Repruebastigo/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── services/
│   │   │   ├── email.py
│   │   │   └── tickets.py
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── usuarios.py
│   │       ├── solicitudes.py
│   │       ├── repruebas.py
│   │       ├── danos.py
│   │       ├── clientes.py
│   │       ├── analista.py
│   │       ├── garantias.py
│   │       └── exportes.py
│   ├── requirements.txt
│   ├── .env
│   └── seed.py
├── index.html
├── script.js
├── style.css
├── style-extended.css
└── reset-password.html
```

---

## Notas técnicas

- El `id_reprueba` viene del sistema externo de Tigo y debe ser único. No es autoincremental.
- Si se insertan datos manualmente con SQL, hay que sincronizar la secuencia: `SELECT setval('repruebas_id_reprueba_seq', (SELECT MAX(id_reprueba) FROM repruebas));`
- El router de daños usa el prefijo `/danos` (sin ñ) para evitar problemas de encoding en URLs.
- La versión de bcrypt debe ser 4.0.1: `pip install bcrypt==4.0.1`
- La `MAIL_PASSWORD` en el `.env` es la contraseña de aplicación de Gmail (16 caracteres), no la contraseña personal de la cuenta.
- La tabla `daños_pendientes` tiene FK hacia `cliente`. La `cedula_cliente` debe existir en la tabla `cliente` antes de cargar daños.
- El frontend debe servirse desde un servidor local (http://localhost:5500), no abrirse directamente como archivo `file://`.

---

## Solución a errores comunes

**El backend no arranca con "No module named app"** — hay que ejecutar `uvicorn` desde dentro de la carpeta `backend/`, no desde la raíz del proyecto.

**Error de bcrypt al hacer login** — instalar la versión correcta: `pip install bcrypt==4.0.1`

**El frontend muestra "Failed to fetch"** — el backend no está corriendo. Verificar que uvicorn esté activo en otra terminal.

**Error de llave duplicada al cargar repruebas** — el `id_reprueba` ya existe en la BD. Verificar los IDs del archivo o sincronizar la secuencia con el comando de arriba.

**Las garantías no muestran datos** — verificar que haya daños cerrados con repruebas de falla asociadas ejecutando: `SELECT COUNT(*) FROM repruebas r JOIN daños_cerrados dc ON r.pedido_id = dc.pedido_id WHERE r.codigo_estado IN ('Falla física', 'Falla lógica', 'Falla física lógica');`
