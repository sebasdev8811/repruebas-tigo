FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar backend
COPY backend/ ./backend/

# Copiar frontend
COPY index.html .
COPY reset-password.html .
COPY script.js .
COPY style.css .
COPY style-extended.css .

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]