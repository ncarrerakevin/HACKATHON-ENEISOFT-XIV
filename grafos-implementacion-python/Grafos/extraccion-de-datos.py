import requests
import json

# Configurar la URL y parámetros del API
url = 'https://contratacionesabiertas.osce.gob.pe/api/v1/records'
params = {
    'page': 1,
    'order': 'desc',
    'sourceId': 'seace_v3',
    'startDate': '2024-11-05',
    'endDate': '2024-11-06'
}

# Hacer la solicitud
response = requests.get(url, params=params)

# Comprobar si la solicitud fue exitosa
if response.status_code == 200:
    data = response.json()

    # Guardar los datos en un archivo JSON
    with open('contratos.json', 'w') as file:
        json.dump(data, file, indent=4)
    print("Datos guardados en 'contratos.json'")
else:
    print(f"Error en la solicitud: {response.status_code}")
