# 📺 YoutubeAI-Extractor

> Extrae y corrige transcripciones de vídeos de YouTube usando IA.

---

## ✨ Descripción

**YoutubeAI-Extractor** es una utilidad en Python que:

1. 📥 Descarga la transcripción auto-generada de un vídeo de YouTube (español e inglés).  
2. 🧩 Divide la transcripción en fragmentos para no exceder el límite de tokens.  
3. 🤖 Envía cada fragmento a un modelo de IA de Groq para corregir errores de ortografía, puntuación y fluidez.  
4. 📋 Imprime la transcripción corregida y la copia automáticamente al portapapeles.

---

## 🚀 Características

- 🌐 Soporte de idiomas: español (`es`) e inglés (`en`) con fallback automático.  
- ✂️ Procesamiento en chunks de hasta 200 palabras.  
- 📝 Corrección de texto mediante modelo LLaMA de Groq.  
- 📋 Copia automática del resultado al portapapeles (Windows, macOS, Linux).

---

## 🛠️ Requisitos

- Python 3.8 o superior  
- Clave de API de Groq (modelo `meta-llama/llama-4-maverick-17b-128e-instruct`)  
- Conexión a Internet para acceder a la API de YouTube Transcript API

---

## ⚙️ Instalación

1. **Clona el repositorio**  
   ```bash
   git clone https://github.com/GuxJ02/YoutubeAI-Extractor.git
   cd YoutubeAI-Extractor
   ```
2. **Crea y activa un entorno virtual**  
   ```bash
   git clopython -m venv venvYT
   # Windows
   venvYT\Scripts\activate
   # macOS/Linux
   source venvYT/bin/activate
   ```
3. **Instala las dependencias**  
   ```bash
   pip install -r requirements.txt
   ```
4. **Configura las variables de entorno**  
   ```bash
   cp .env.example .env
   #Edita .env y añade tu api key de gruq
   ```
---
## ▶️ Uso

1. En `extractor.py`, configura la URL del vídeo:

   ```python
   url = "https://www.youtube.com/watch?v=TU_VIDEO_ID"
   ```
2. Ejecuta el script:
   ```bash
   python extractor.py
   # El script sacará por consola el video de yt transcrito y revisado por la IA
   # y se copiará al portapapeles
   ```
