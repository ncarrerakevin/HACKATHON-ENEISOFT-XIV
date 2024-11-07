import json
import pandas as pd

# Cargar el archivo JSON
with open('contratos_limpios.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extraer los datos de los registros
records = data['records']

# Crear listas vacías para almacenar la información
ocid_list = []
contract_id_list = []
date_list = []
buyer_id_list = []
buyer_name_list = []
tender_id_list = []
tender_title_list = []
tender_description_list = []
procurement_method_list = []
procurement_method_details_list = []
main_procurement_category_list = []
value_list = []
currency_list = []
date_published_list = []
items_list = []
parties_list = []
documents_list = []

# Procesar cada registro y extraer los datos relevantes
for record in records:
    ocid_list.append(record.get("ocid", ""))
    contract_id_list.append(record.get("contract_id", ""))
    date_list.append(record.get("date", ""))

    buyer = record.get("buyer", {})
    buyer_id_list.append(buyer.get("id", ""))
    buyer_name_list.append(buyer.get("name", ""))

    tender = record.get("tender", {})
    tender_id_list.append(tender.get("id", ""))
    tender_title_list.append(tender.get("title", ""))
    tender_description_list.append(tender.get("description", ""))
    procurement_method_list.append(tender.get("procurementMethod", ""))
    procurement_method_details_list.append(tender.get("procurementMethodDetails", ""))
    main_procurement_category_list.append(tender.get("mainProcurementCategory", ""))
    value_list.append(tender.get("value", 0.0))
    currency_list.append(tender.get("currency", ""))
    date_published_list.append(tender.get("datePublished", ""))

    # Convertir 'items', 'parties' y 'documents' a formato de texto para ser leídos en el Excel
    items_list.append(str(tender.get("items", [])))
    parties_list.append(str(record.get("parties", [])))
    documents_list.append(str(record.get("documents", [])))

# Crear un DataFrame de pandas
df = pd.DataFrame({
    "OCID": ocid_list,
    "Contract ID": contract_id_list,
    "Date": date_list,
    "Buyer ID": buyer_id_list,
    "Buyer Name": buyer_name_list,
    "Tender ID": tender_id_list,
    "Tender Title": tender_title_list,
    "Tender Description": tender_description_list,
    "Procurement Method": procurement_method_list,
    "Procurement Method Details": procurement_method_details_list,
    "Main Procurement Category": main_procurement_category_list,
    "Value": value_list,
    "Currency": currency_list,
    "Date Published": date_published_list,
    "Items": items_list,
    "Parties": parties_list,
    "Documents": documents_list
})

# Exportar a Excel
df.to_excel('records_data.xlsx', index=False, engine='openpyxl')
print("Datos exportados a records_data.xlsx")
