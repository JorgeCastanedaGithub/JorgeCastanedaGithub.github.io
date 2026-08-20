import sys
import requests
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

target_date = datetime.now() - timedelta(days=1)
year = target_date.strftime("%Y")
month = target_date.strftime("%m")
day = target_date.strftime("%d")
CURRENT_DATE_INT = int(target_date.strftime("%Y%m%d"))
BASE_URL = "https://www.dof.gob.mx/"
TARGET_URL = f"https://www.dof.gob.mx/index_111.php?year={year}&month={month}&day={day}#gsc.tab=0"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False

    try:
        response = session.get(TARGET_URL, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching the main page: {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, 'html.parser')
    detail_links = []

    current_title = "[No Header Title Found Yet]"
    
    all_links = soup.find_all('a', href=True)
    
    for tag in all_links:
        href_value = tag['href']
        
        if "nota_to_doc.php?" in href_value:
            parent_td = tag.find_parent('td')
            if parent_td:
                current_title = parent_td.get_text(strip=True)
        
        elif "nota_detalle.php?codigo=" in href_value:
            link_description = tag.get_text(strip=True) or "[No description]"
            full_url = urljoin(BASE_URL, href_value)
            
            # print(f"Title:   {current_title}")
            # print(f"Subject: {link_description}")
            # print(f"Link:    {full_url}")
            # print("-" * 40)

            if not any(item['link'] == full_url for item in detail_links):
                detail_links.append({
                    "title": current_title,
                    "subject": link_description,
                    "link": full_url
                })
            
            # if full_url not in detail_links:
            #     detail_links.append(full_url)

    # 3. Read each detail link and print text inside id="DivDetalleNota"
    for url in detail_links:
        try:
            detail_res = session.get(url, timeout=15)
            detail_res.raise_for_status()
            
            detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
            target_div = detail_soup.find(id="DivDetalleNota")

            cleaned_text = ""
            if target_div:
                cleaned_text = "\n".join([line.strip() for line in target_div.get_text(separator="\n").splitlines() if line.strip()])

            row_data = {
                "date": CURRENT_DATE_INT,
                "title": url['title'],
                "subject": url['subject'],
                "link": url['link'],
                "detail": cleaned_text
            }

            supabase.table("dof_day_text").insert(row_data).execute()
                
        except Exception as e:
            print(f"Error reading detail page {url}: {e}")

if __name__ == "__main__":
    main()
