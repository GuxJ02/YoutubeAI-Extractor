import os
import pyperclip
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
load_dotenv()



# Inicializa el cliente de Groq con la API key desde la variable de entorno
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
url="https://www.youtube.com/watch?v=dkO0hkUfDjo";


def extract_video_id(url):
    """
    Extrae el ID del video de una URL de YouTube.
    """
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc:
        return parse_qs(parsed_url.query)['v'][0]
    elif 'youtu.be' in parsed_url.netloc:
        return parsed_url.path[1:]
    return None

def get_transcript(video_id):
    """
    Obtiene la transcripción en español (auto-generada) de un video de YouTube.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
        return transcript
    except Exception as e:
        print(f"Ocurrió un error al obtener la transcripción: {e}")
        return []

def chunk_text(text, max_words=200):
    """
    Divide el texto en trozos de tamaño máximo 'max_words' palabras.
    Devuelve una lista de strings (trozos).
    """
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        # Si al añadir la siguiente palabra excedemos el límite, creamos un nuevo chunk
        if len(current_chunk) + 1 > max_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    # Agregar el último chunk si hay palabras pendientes
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def rephrase_text(text):
    """
    Envía el texto a la IA de Groq (modelo 'llama-3.2-90b-vision-preview')
    para que corrija y reescriba la transcripción.
    """
    prompt = f"""A continuación, te proporciono un fragmento de la transcripción de un video de YouTube. 
La transcripción tiene algunos errores de transcripción, ortográficos y de puntuación. 
Por favor, corrige y reescribe el texto para que tenga una redacción clara, natural y coherente, 
manteniendo el sentido original del mensaje. 
Si encuentras palabras o frases que no tienen sentido, infiere lo que el hablante quiso decir basándote en el contexto. 
Es importante que unicamente en la respuesta que me des solamente pongas la corrección del texto, nada mas.

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
            stream=True,  # Modo streaming activado
            stop=None,
        )
        result_text = ""
        # Procesa y concatena los chunks que llegan en streaming
        for chunk in completion:
            # Agrega el texto parcial que llega
            result_text += chunk.choices[0].delta.content or ""
        return result_text.strip()
    except Exception as e:
        print(f"Ocurrió un error al llamar a Groq: {e}")
        return None

if __name__ == "__main__":
   
    video_id = extract_video_id(url)
    
if video_id:
    transcript_data = get_transcript(video_id)

    if transcript_data:
        # Concatena todos los textos de cada segmento de la transcripción
        full_transcript = " ".join([entry["text"] for entry in transcript_data])

        # Divide la transcripción en varios trozos para no exceder el límite
        chunks = chunk_text(full_transcript, max_words=200)

        # Para cada trozo, lo reescribimos y concatenamos el resultado
        corrected_transcript_parts = []
        for i, chunk in enumerate(chunks, start=1):
            print(f"Procesando chunk {i}/{len(chunks)}...")
            corrected_part = rephrase_text(chunk)
            if corrected_part:
                corrected_transcript_parts.append(corrected_part)
            else:
                corrected_transcript_parts.append("")  # Evita None

        # Une todos los trozos corregidos
        corrected_transcript = "\n".join(corrected_transcript_parts)

        print("\nTranscripción corregida:\n")
        print(corrected_transcript)
        try:
         pyperclip.copy(corrected_transcript)
         print("\n✅ Transcripción corregida copiada al portapapeles.")
        except pyperclip.PyperclipException as e:
         print(f"\n⚠️ No se pudo copiar al portapapeles: {e}")
    else:
        print("No se obtuvo la transcripción del video.")
else:
    print("No se pudo extraer el ID del video de la URL proporcionada.")
