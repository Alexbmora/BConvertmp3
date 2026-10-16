# YouTube → MP3

Conversor de audio de YouTube a MP3. Monorepo con API (FastAPI) y web (React + Vite).

> Aviso legal: descargar contenido de YouTube puede infringir sus Términos de
> Servicio. Úsalo solo con contenido propio o para el que tengas autorización.

## Estructura

```
youtube-mp3/
├─ backend/            # API FastAPI + yt-dlp + ffmpeg
│  ├─ app/
│  │  ├─ main.py       # App FastAPI y lifespan
│  │  ├─ config.py     # Settings (pydantic-settings, prefijo APP_)
│  │  ├─ schemas.py    # Modelos Pydantic
│  │  ├─ security.py   # Validación de URLs / bitrate
│  │  ├─ core/         # jobstore, queue (interfaces + impl. en memoria)
│  │  ├─ services/     # downloader (yt-dlp)
│  │  └─ routers/      # jobs, info
│  ├─ requirements.txt
│  └─ Dockerfile
├─ web/                # Frontend Vite + React + TS + Tailwind v4
└─ docker-compose.yml
```

Estado actual (Fase 1): store y cola **en memoria**. El historial y el progreso
se pierden al reiniciar el proceso. La Fase 2 añade Supabase (Postgres + Storage
+ Realtime) implementando las mismas interfaces (`JobStore`, `Storage`).

## Requisitos

- Python 3.12
- Node.js 20+
- ffmpeg en el `PATH`

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

Si ffmpeg no está en el `PATH`, define `APP_FFMPEG_LOCATION` (ver
`backend/.env.example`) apuntando a su carpeta `bin`.

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/jobs` | Crea 1..N conversiones (`urls`, `bitrate`) |
| GET | `/api/v1/jobs` | Historial de jobs |
| GET | `/api/v1/jobs/{id}` | Estado de un job |
| GET | `/api/v1/jobs/{id}/events` | Progreso en vivo (SSE) |
| GET | `/api/v1/jobs/{id}/download` | Descarga el MP3 |
| DELETE | `/api/v1/jobs/{id}` | Elimina el job |
| POST | `/api/v1/info` | Metadatos de un video |

## Frontend

```powershell
cd web
npm install
npm run dev
```

- Web: http://127.0.0.1:5173
- El dev server hace proxy de `/api` hacia `http://127.0.0.1:8000`.

Para apuntar a otro backend, define `VITE_API_BASE_URL`.

## Docker

```powershell
docker compose up --build
```

## Despliegue en Render

El repo incluye `render.yaml` (Blueprint) con dos servicios:

| Servicio | Nombre | URL |
|---|---|---|
| API (Docker) | `ytmp3-api` | https://ytmp3-api.onrender.com |
| Web (estático) | `ytmp3-web` | https://ytmp3-web.onrender.com |

Pasos:

1. Sube el repo a GitHub (si aún no lo has hecho):
   ```powershell
   git init
   git add .
   git commit -m "YouTube a MP3: API FastAPI + web Vite"
   git branch -M main
   git remote add origin https://github.com/<usuario>/youtube-mp3.git
   git push -u origin main
   ```
2. En Render: **New → Blueprint**, conecta el repo y confirma. Render crea los
   dos servicios a partir de `render.yaml`.
3. La web llama a la API vía `VITE_API_BASE_URL` (compilado en el bundle) y la
   API permite el origen de la web vía `APP_CORS_ORIGINS`. Si cambias los
   nombres de servicio o usas dominio propio, actualiza ambos valores.

Notas de Render:

- El `Dockerfile` instala **ffmpeg** y **Deno** (yt-dlp lo usa para extraer de
  YouTube). No hace falta `APP_FFMPEG_LOCATION` en el contenedor.
- En el plan free el servicio **se duerme tras 15 min** de inactividad (cold
  start de ~30-60 s) y el disco es **efímero**: los MP3 se pierden al reiniciar.
  En la Fase 2, Supabase Storage los conserva.
- YouTube suele **bloquear IPs de datacenter** (403 / “confirm you’re not a
  bot”). Mitigación: cookies de YouTube, `--sleep-requests`, concurrencia baja.

## Roadmap

- [ ] Fase 2: Supabase (`PostgresJobStore`, `SupabaseStorage`, Realtime).
- [ ] Worker separado en Render + cookies para evitar el bloqueo de YouTube.
- [ ] App móvil (React Native / Expo) reutilizando la API.
