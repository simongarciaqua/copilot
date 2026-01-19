# 🤖 Copiloto de Atención al Cliente - POC

Sistema multi-agente para asistir a agentes de atención al cliente mediante recomendaciones basadas en reglas de negocio deterministas.

## 🏗️ Arquitectura

```
Cliente → Router Agent → Rules Engine → Specialist Agent → Recomendación
```

### Componentes clave:

1. **Rules Engine**: Evalúa reglas de negocio de forma determinista (sin LLM)
2. **Router Agent**: Detecta qué proceso aplica a la conversación
3. **Specialist Agent**: Genera recomendaciones siguiendo estrictamente las reglas
4. **Frontend**: 3 paneles simultáneos para simulación y visualización

## 📁 Estructura del Proyecto

```
/Copilot/
├── backend/
│   ├── main.py                     # FastAPI server
│   ├── rules_engine/
│   │   └── evaluator.py           # Motor de reglas determinista
│   ├── agents/
│   │   ├── router.py              # Agente router
│   │   └── stop_reparto_agent.py  # Agente especialista
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ClientSimulation.jsx
│   │   │   ├── Recommendation.jsx
│   │   │   └── CustomerContext.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── stop_reparto/
    ├── policy_stop_reparto.txt    # Política del proceso
    └── rules_stop_reparto.json    # Reglas de negocio
```

## 🚀 Instalación y Configuración

### 1️⃣ Backend Setup

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env y añadir tu GOOGLE_API_KEY
```

### 2️⃣ Frontend Setup

```bash
cd frontend

# Instalar dependencias
npm install
```

## ▶️ Ejecución

### Terminal 1 - Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

El backend estará disponible en: `http://localhost:8000`

### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

## 🧪 Prueba del Sistema

### Escenario 1: Reconducción Obligatoria

**Mensaje del cliente:**
```
Me sobra agua y quiero parar el reparto
```

**Contexto sugerido:**
```json
{
  "plan": "Ahorro",
  "scoring": 3.5,
  "motivo": "exceso_agua",
  "stops_ultimo_ano": 1,
  "albaran_descargado": false,
  "tipo_cliente": "residencial"
}
```

**Resultado esperado:**
- Stop permitido: ❌ No
- Recomendación: Reconducción obligatoria
- Acciones: Combinar productos, reducir unidades, cambiar formato

### Escenario 2: Vacaciones (Stop Permitido)

**Mensaje del cliente:**
```
Me voy de vacaciones 2 semanas
```

**Contexto sugerido:**
```json
{
  "plan": "Estandar",
  "scoring": 4.2,
  "motivo": "ausencia_vacaciones",
  "stops_ultimo_ano": 0,
  "tipo_cliente": "residencial"
}
```

**Resultado esperado:**
- Stop permitido: ✅ Sí
- Recomendación: Retención mediante alternativas
- Acciones: Mover fecha, traslado temporal, stop completo

### Escenario 3: Cambio de Contexto

1. Envía el mensaje del Escenario 1
2. Observa la recomendación
3. En el editor JSON, cambia `"plan": "Ahorro"` a `"plan": "Estandar"`
4. Haz clic en "Actualizar Contexto"
5. Observa cómo cambia la recomendación

## 🎯 Criterios de Éxito del POC

✅ **Separación lógica/lenguaje**: Las reglas se evalúan sin LLM  
✅ **Cambio de contexto actualiza recomendación**: Editar JSON cambia la respuesta  
✅ **Reglas nunca se saltan**: El LLM siempre sigue la decisión del motor  
✅ **Formato escaneable**: La recomendación es clara y accionable  
✅ **Extensible**: Añadir procesos solo requiere nueva carpeta + rules.json + policy.txt

## 📚 Añadir un Nuevo Proceso

1. Crear carpeta para el proceso:
```bash
mkdir nuevo_proceso
```

2. Crear `rules_nuevo_proceso.json`:
```json
{
  "process": "NUEVO_PROCESO",
  "version": "1.0",
  "rules": [...]
}
```

3. Crear `policy_nuevo_proceso.txt` con la documentación del proceso

4. Crear agente especialista en `backend/agents/nuevo_proceso_agent.py`

5. Actualizar `backend/main.py` para incluir el nuevo proceso

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python, FastAPI, LangChain, Google Gemini
- **Frontend**: React, Vite, Monaco Editor
- **Estilo**: CSS moderno con gradientes y glassmorphism

## 📝 Notas Importantes

- El sistema requiere una API key de Google AI configurada en `.env` (obtén una en https://makersuite.google.com/app/apikey)
- El modelo por defecto es `gemini-2.0-flash-exp` (puedes cambiarlo en `.env`)
- Las reglas se cargan desde archivos JSON y se evalúan de forma determinista
- El LLM solo se usa para: detectar proceso y redactar recomendaciones

## 🐛 Troubleshooting

**Error: "GOOGLE_API_KEY not set"**
- Verifica que el archivo `.env` existe en `/backend/`
- Confirma que contiene `GOOGLE_API_KEY=tu_clave_aqui`
- Obtén tu API key en: https://makersuite.google.com/app/apikey

**Error de conexión entre frontend y backend**
- Verifica que el backend esté corriendo en puerto 8000
- Verifica CORS en `main.py` si usas otro puerto para frontend

**Error al instalar dependencias de Python**
- Asegúrate de usar Python 3.9 o superior
- Usa un virtual environment limpio
