import os
from datetime import datetime, timedelta
import requests
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
MASSIVE_API_KEY = os.environ.get("MASSIVE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

target_date = datetime.now() - timedelta(days=2)
date_str_api = target_date.strftime("%Y-%m-%d") 
date_int = int(target_date.strftime("%Y%m%d"))

url = f"https://api.massive.com/v2/aggs/grouped/locale/us/market/stocks/{date_str_api}?adjusted=true&apiKey={MASSIVE_API_KEY}"

print(f"Fetching data for {date_str_api}...")
response = requests.get(url)

if response.status_code != 200:
    raise Exception(f"API Error: {response.status_code} - {response.text}")

api_data = response.json()

data_to_insert = {
    "date": date_int,
    "json": api_data
}

db_response = supabase.table("massive_responses").insert(data_to_insert).execute()
print(f"Successfully saved data for date integer: {date_int} to Supabase!")
