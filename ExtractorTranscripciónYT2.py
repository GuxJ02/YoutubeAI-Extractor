import os
import pyperclip
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled
)
from groq import Groq
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# 1) Carga las variables de entorno desde .env
load_dotenv()

# Debug: comprueba que la clave se cargó correctamente
print("DEBUG ⇒ Variable GROQ_API_KEY cargada:", os.environ.get("GROQ_API_KEY"))

# 2) Inicializa el cliente de Groq con la API key
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 3) URL de ejemplo (cámbiala por la que necesites)
url = "https://www.youtube.com/watch?v=LYp_zh6eksI"


def extract_video_id(url):
    """
    Extrae el ID del video de una URL de YouTube.
    """
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc:
        return parse_qs(parsed_url.query).get('v', [None])[0]
    elif 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')
    return None


def chunk_text(text, max_words=200):
    """
    Divide el texto en trozos de tamaño máximo 'max_words' palabras.
    Devuelve una lista de strings (cada “chunk”).
    """
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(current_chunk) + 1 > max_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def rephrase_text(text):
    """
    Envía el texto a la IA de Groq (modelo 'meta-llama/llama-4-maverick-17b-128e-instruct')
    para que corrija y reescriba la transcripción.
    """
    prompt = f"""A continuación, te proporciono un fragmento de la transcripción de un video de YouTube. 
La transcripción tiene algunos errores de transcripción, ortográficos y de puntuación. 
Por favor, corrige y reescribe el texto para que tenga una redacción clara, natural y coherente, 
manteniendo el sentido original del mensaje. 
Si encuentras palabras o frases que no tienen sentido, infiere lo que el hablante quiso decir basándote en el contexto. 
Es importante que únicamente en la respuesta que me des pongas solamente la corrección del texto, nada más.

Texto original:
{text}
"""
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        result_text = ""
        for chunk in completion:
            result_text += chunk.choices[0].delta.content or ""
        return result_text.strip()
    except Exception as e:
        print(f"Ocurrió un error al llamar a Groq: {e}")
        return None


def get_transcript_debug(video_id):
    """
    Intenta obtener la transcripción del video paso a paso, imprimiendo debug en cada intento.
    1) Hace list_transcripts para ver qué idiomas existen.
    2) Si existe 'es' o 'en', intenta get_transcript(languages=[...]).
    3) Si falla en ese paso, intenta find_generated_transcript([...]).fetch()
    4) Si aún no hay resultado, intenta get_transcript sin filtro de idiomas.
    5) Devuelve la lista de segmentos o lista vacía.
    """
    # 1) Intentar listar los transcripts disponibles
    try:
        transcripts_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available = [t.language_code for t in transcripts_list]
        print("DEBUG get_transcript ⇒ lista_transcripts encontró idiomas:", available)
    except NoTranscriptFound:
        print("DEBUG get_transcript ⇒ No se encontró ningún subtítulo (ni auto generado).")
        return []
    except TranscriptsDisabled:
        print("DEBUG get_transcript ⇒ Los subtítulos están deshabilitados para este video.")
        return []
    except Exception as e:
        print(f"DEBUG get_transcript ⇒ Error al listar transcripts: {e}")
        return []

    # 2) Si existen "es" o "en", intentar primero get_transcript con languages
    if 'es' in available or 'en' in available:
        langs = []
        if 'es' in available:
            langs.append('es')
        if 'en' in available:
            langs.append('en')

        print(f"DEBUG get_transcript ⇒ Intentando get_transcript con languages={langs} ...")
        try:
            t = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
            print("DEBUG get_transcript ⇒ get_transcript con languages tuvo éxito")
            return t
        except Exception as e:
            print(f"DEBUG get_transcript ⇒ Error get_transcript con languages={langs}: {e}")

        # 3) Si falla get_transcript con languages, probar find_generated_transcript
        print(f"DEBUG get_transcript ⇒ Intentando find_generated_transcript({langs}) ...")
        try:
            tg = transcripts_list.find_generated_transcript(langs)
            fetched = tg.fetch()
            print("DEBUG get_transcript ⇒ find_generated_transcript tuvo éxito")
            return fetched
        except NoTranscriptFound:
            print("DEBUG get_transcript ⇒ NoTranscriptFound en find_generated_transcript")
        except Exception as e2:
            print(f"DEBUG get_transcript ⇒ Error find_generated_transcript: {e2}")

    # 4) Si no hay 'es'/'en' o después de fallar los pasos anteriores, intentar sin idiomas
    print("DEBUG get_transcript ⇒ Intentando get_transcript sin filtro de idiomas ...")
    try:
        t_default = YouTubeTranscriptApi.get_transcript(video_id)
        print("DEBUG get_transcript ⇒ get_transcript sin languages tuvo éxito")
        return t_default
    except Exception as e:
        print(f"DEBUG get_transcript ⇒ Error get_transcript sin languages: {e}")

    # 5) Por último, intentar buscar cualquier generated transcript con el resto de idiomas
    if available:
        print(f"DEBUG get_transcript ⇒ Intentando find_generated_transcript({available}) último recurso ...")
        try:
            tg2 = transcripts_list.find_generated_transcript(available)
            fetched2 = tg2.fetch()
            print("DEBUG get_transcript ⇒ find_generated_transcript (último recurso) tuvo éxito")
            return fetched2
        except Exception as e3:
            print(f"DEBUG get_transcript ⇒ Error find_generated_transcript (último recurso): {e3}")

    # Si llegamos acá, no se pudo obtener nada
    return []


if __name__ == "__main__":
    # 6) Extraer y mostrar el video_id
    video_id = extract_video_id(url)
    print("DEBUG ⇒ Video ID extraído:", video_id)

    if not video_id:
        print("No se pudo extraer el ID del video de la URL proporcionada. Verifica la URL.")
        exit(1)

    # 7) Llamar a nuestra función que hace todo el debug para obtener el transcript
    transcript_data = get_transcript_debug(video_id)

    if not transcript_data:
        print("\nNo se obtuvo la transcripción del video después de todos los intentos.")
        exit(1)

    # 8) Si tenemos transcript_data, construir full_transcript de forma compatible
    #    tanto si vienen dicts (get_transcript) como objetos (FetchedTranscriptSnippet).
    texts = []
    for entry in transcript_data:
        if isinstance(entry, dict):
            texts.append(entry.get("text", ""))
        else:
            texts.append(getattr(entry, "text", ""))
    full_transcript = " ".join(texts)

    # 9) Dividir en chunks y llamar a Groq (igual que antes)
    chunks = chunk_text(full_transcript, max_words=200)

    corrected_transcript_parts = []
    for i, chunk in enumerate(chunks, start=1):
        print(f"Procesando chunk {i}/{len(chunks)}...")
        corrected_part = rephrase_text(chunk)
        if corrected_part:
            corrected_transcript_parts.append(corrected_part)
        else:
            corrected_transcript_parts.append("")

    corrected_transcript = "\n".join(corrected_transcript_parts)

    print("\nTranscripción corregida:\n")
    print(corrected_transcript)

    try:
        pyperclip.copy(corrected_transcript)
        print("\n✅ Transcripción corregida copiada al portapapeles.")
    except pyperclip.PyperclipException as e:
        print(f"\n⚠️ No se pudo copiar al portapapeles: {e}")
