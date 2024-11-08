import requests
import json

# Configurar la URL inicial de la API
url = 'https://contratacionesabiertas.osce.gob.pe/api/v1/recordsAfter?size=100&sourceId=seace_v3&startDate=2024-04-01&endDate=2024-11-01'

# Almacenar todos los registros
all_records = []
max_pages = 100  # Define el número máximo de páginas para obtener
page_count = 0  # Contador de páginas

# Bucle para obtener todas las páginas
while page_count < max_pages:
    # Hacer la solicitud
    response = requests.get(url)

    # Comprobar si la solicitud fue exitosa
    if response.status_code == 200:
        data = response.json()
        records = data.get('records', [])
        print(f"Registros obtenidos en esta llamada: {len(records)}")

        # Agregar los registros de esta página a la lista completa
        all_records.extend(records)

        # Verificar si hay más registros en la siguiente página
        next_link = data.get('links', {}).get('next')
        print(f"Enlace next: {next_link}")  # Imprimir el enlace `next` para diagnóstico

        if not next_link:
            print("No hay más páginas disponibles.")
            break
        else:
            # Actualizar la URL con el enlace `next`
            url = next_link
            page_count += 1  # Incrementar el contador de páginas
    else:
        print(f"Error en la solicitud: {response.status_code}")
        break

# Guardar todos los datos en un archivo JSON
with open('contratos_completos.json', 'w') as file:
    json.dump({"records": all_records}, file, indent=4)
print(f"Datos guardados en 'contratos_completos.json' con un total de {len(all_records)} registros.")
