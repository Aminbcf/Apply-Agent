import os
import requests
import zipfile
import io
import pandas as pd
import json
from dotenv import load_dotenv

# Load variables from .env into the environment
load_dotenv()
# Define directories for your RAG pipeline
DATA_DIR = "rag_raw_data"
DIRS = {
    "onet": os.path.join(DATA_DIR, "onet"),
    "esco": os.path.join(DATA_DIR, "esco"),
    "ooh": os.path.join(DATA_DIR, "ooh")
}
api_key = os.getenv("API_KEY")

for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

def fetch_onet_database():
    """
    O*NET provides their entire database as a zipped bundle of text/CSV files.
    """
    print("Fetching O*NET Database...")
    onet_url = "https://www.onetcenter.org/dl_files/database/db_28_2_text.zip"
    
    response = requests.get(onet_url, timeout=30)
    if response.status_code == 200:
        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(DIRS["onet"])
        print(f"✅ O*NET data extracted to {DIRS['onet']}")
        
        tasks_file = os.path.join(DIRS["onet"], "db_28_2_text", "Task Statements.txt")
        if os.path.exists(tasks_file):
            df = pd.read_csv(tasks_file, sep='\t')
            df.to_json(os.path.join(DIRS["onet"], "onet_tasks_clean.json"), orient="records")
            print("✅ O*NET tasks cleaned and saved to JSON.")
    else:
        print(f"❌ Failed to fetch O*NET: {response.status_code}")

def fetch_esco_dataset():
    """
    ESCO provides their entire ontology as downloadable CSVs.
    """
    print("Fetching ESCO Occupations...")
    esco_url = "https://esco.ec.europa.eu/system/files/2022-01/occupations_en.csv"
    
    response = requests.get(esco_url, timeout=30)
    if response.status_code == 200:
        file_path = os.path.join(DIRS["esco"], "esco_occupations.csv")
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        df = pd.read_csv(file_path)
        df_clean = df[['conceptUri', 'preferredLabel', 'description']]
        df_clean.to_json(os.path.join(DIRS["esco"], "esco_clean.json"), orient="records")
        print(f"✅ ESCO data fetched and cleaned in {DIRS['esco']}")
    else:
        print(f"❌ Failed to fetch ESCO: {response.status_code}")

def fetch_ooh_data(api_key=api_key):
    """
    The Occupational Outlook Handbook (OOH) is managed by the BLS.
    """
    print("Fetching OOH/BLS Data...")
    if api_key == "YOUR_BLS_API_KEY":
        print("⚠️ BLS API key not provided. Skipping OOH fetch. Register at data.bls.gov.")
        return

    headers = {'Content-type': 'application/json'}
    data = json.dumps({"seriesid": ['CEU0800000001'], "registrationkey": api_key})
    
    response = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers, timeout=30)
    
    if response.status_code == 200:
        json_data = response.json()
        with open(os.path.join(DIRS["ooh"], "ooh_raw.json"), "w") as f:
            json.dump(json_data, f, indent=4)
        print(f"✅ OOH/BLS data saved to {DIRS['ooh']}")
    else:
        print(f"❌ Failed to fetch OOH: {response.status_code}")

# --- Execution ---
print("Starting RAG Context Ingestion...")
fetch_onet_database()
fetch_esco_dataset()
fetch_ooh_data() # Add your API key as a string argument if you get one
print("\nIngestion Complete. Data is ready for your vector database pipeline.")