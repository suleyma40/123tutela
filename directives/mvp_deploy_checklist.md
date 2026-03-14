# MVP Deploy Checklist

## Backend

1. Instalar dependencias con `python -m pip install -r requirements.txt`
2. Configurar `.env` local desde `.env.example`
3. Ejecutar `python main_backend.py`

## Frontend

1. En `frontend/`, ejecutar `npm install`
2. Crear `frontend/.env` desde `frontend/.env.example`
3. Iniciar con `npm run dev`

## Base de datos

- `execution/bootstrap_remote_vps.py` migra la base existente por SSH en el VPS/Coolify
- `execution/bootstrap_database.py` aplica el esquema cuando `DATABASE_URL` es accesible directamente
- `execution/seed_reference_data.py` siembra catálogos y conocimiento por conexión directa

## Despliegue en Coolify

- Backend: usar [Dockerfile.backend](/c:/Users/su-le/OneDrive/Desktop/tutelaapp/Dockerfile.backend)
- Frontend: usar [frontend/Dockerfile](/c:/Users/su-le/OneDrive/Desktop/tutelaapp/frontend/Dockerfile)
- Frontend necesita `VITE_API_URL`
- Backend en producción debe usar la `DATABASE_URL` interna de Coolify
