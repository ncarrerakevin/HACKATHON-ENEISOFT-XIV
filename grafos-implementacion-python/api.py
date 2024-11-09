import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_chatgpt_api():
    api_key = os.getenv("OPENAI_API_KEY")
    url = "https://api.openai.com/v1/completions"

    if not api_key:
        print("Error: API key no encontrada. Asegúrate de definir OPENAI_API_KEY en tu archivo .env")
        return
    else:
        print(f"API Key encontrada: {api_key[:5]}... (ocultando por seguridad)")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "text-davinci-003",
        "prompt": "Este es un test para verificar si mi API de OpenAI tiene créditos disponibles.",
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        print("Respuesta de la API:", result)
    except requests.exceptions.RequestException as e:
        print("Error al llamar a la API de OpenAI:", e)

if __name__ == "__main__":
    test_chatgpt_api()
