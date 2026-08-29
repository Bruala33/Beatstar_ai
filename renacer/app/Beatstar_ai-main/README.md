# 🎵 Beatstar Beatmap Generator API (FastAPI + Librosa + yt-dlp)

Servidor backend en Python de alto rendimiento para analizar pistas de audio de YouTube y generar beatmaps interactivos de 3 carriles al estilo **Beatstar** con marcas de tiempo en milisegundos y tipos de nota `tap`, `hold` y `swipe`.

---

## 🚀 Características

1. **Descarga en Memoria con `yt-dlp`**:
   - Extracción directa de pistas de audio desde cualquier URL o ID de YouTube.
   - Decodificación y muestreo automático a mono 22.05 kHz.
   
2. **Análisis Acústico Avanzado con `librosa`**:
   - **Separación Armónica/Percusiva (HPSS)** (`librosa.effects.hpss`): Aísla componentes rítmicos (batería, percusión) de componentes melódicos y vocales sostenidos.
   - **Filtros por Bandas de Frecuencia**:
     - *Bajos* (< 250 Hz): Detección de bombos, sub-bajos y ritmo principal.
     - *Medios* (250 Hz - 2500 Hz): Detección de frecuencias fundamentales vocales, sintetizadores y acordes.
     - *Agudos* (> 2500 Hz): Detección de platos, hi-hats y brillo en transiciones.
   - **Detección de Transitorios**: `librosa.onset.onset_detect` con función de fuerza de inicio (`onset_strength`) y retroceso de picos (`backtracking`).
   - **Estimación de Tempo y Beat Grid**: `librosa.beat.beat_track` con cálculo de BPM y cuantización rítmica.

3. **Generación Inteligente de Beatmap de 3 Carriles (Beatstar)**:
   - **Carril 0** (Izquierda): Orientado a frecuencias bajas y ritmo base.
   - **Carril 1** (Centro): Orientado a voces principales, melodías centrales y sostenidos.
   - **Carril 2** (Derecha): Orientado a frecuencias agudas y adornos.
   - **Tipos de Notas**:
     - `'tap'`: Golpes rítmicos cortos.
     - `'hold'`: Notas vocales o acordes largos sostenidos con `duration_ms` y `end_timestamp_ms`.
     - `'swipe'`: Flechas direccionales (`up`, `left`, `right`, `down`) en transiciones fuertes o picos de flujo espectral.
   - **Prevención de colisiones**: Respeta la ocupación de carriles por notas `hold` y evita solapamientos imposibles de pulsar.

4. **Interfaz Web de Visualización Integrada**:
   - Panel de control interactivo en `http://localhost:8000/`.
   - Visualizador de 3 carriles con código de colores.
   - Generación de demo sintético sin requerir conexión a internet.
   - Copia y descarga de archivos `.json`.

---

## 📦 Instalación y Puesta en Marcha

### Requisitos Previos
- Python 3.10 o superior (o `uv`)
- `ffmpeg` (instalado en el sistema)

### Iniciar el Servidor

```bash
# Con entorno virtual activo
python run.py
```

El servidor estará disponible en:
- **Web UI & Visualizador**: [http://localhost:8000/](http://localhost:8000/)
- **Documentación Swagger / OpenAPI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 📡 Endpoints de la API

### 1. `POST /api/v1/beatmap/generate`

#### Request Body
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "difficulty": "normal",
  "snap_to_grid": true,
  "onset_sensitivity": 1.0
}
```

#### Response Body (Ejemplo)
```json
{
  "video_id": "dQw4w9WgXcQ",
  "metadata": {
    "video_id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "uploader": "RickAstleyVEVO",
    "duration_seconds": 212.0,
    "bpm": 113.5,
    "total_notes": 482,
    "tap_count": 395,
    "hold_count": 52,
    "swipe_count": 35,
    "difficulty": "normal",
    "density_notes_per_second": 2.27
  },
  "notes": [
    {
      "id": 1,
      "lane": 0,
      "type": "tap",
      "timestamp_ms": 1057,
      "duration_ms": null,
      "end_timestamp_ms": null,
      "direction": null,
      "frequency_band": "bass",
      "energy": 0.82
    },
    {
      "id": 2,
      "lane": 1,
      "type": "hold",
      "timestamp_ms": 1586,
      "duration_ms": 850,
      "end_timestamp_ms": 2436,
      "direction": null,
      "frequency_band": "mid",
      "energy": 0.74
    },
    {
      "id": 3,
      "lane": 2,
      "type": "swipe",
      "timestamp_ms": 2645,
      "duration_ms": null,
      "end_timestamp_ms": null,
      "direction": "right",
      "frequency_band": "high",
      "energy": 0.95
    }
  ],
  "lanes": [
    [ /* Notas asignadas al carril 0 (Izquierda) */ ],
    [ /* Notas asignadas al carril 1 (Centro) */ ],
    [ /* Notas asignadas al carril 2 (Derecha) */ ]
  ]
}
```

### 2. `GET /api/v1/beatmap/sample`
Genera un beatmap de prueba con audio sintético (kick + melodía sostenida) para verificación instantánea.
