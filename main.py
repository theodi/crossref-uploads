# thank you gemini for making my code a lot better

import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import re

# ==========================================
# 1. CONFIGURATION & INPUT DATA
# ==========================================

# Your Crossref Credentials (for the XML header)
DEPOSITOR_NAME = "Neil Majithia (ODI)"
DEPOSITOR_EMAIL = "neil.majithia@theodi.org"
REGISTRANT = "Neil Majithia (ODI)"

# The Batch ID (uses timestamp to be unique)
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d%H%M")
BATCH_ID = f"ODI_Deposit_{TIMESTAMP}"

# *** INPUT YOUR DATA HERE ***
# Replace this list of dicts with actual URLs and DOIs
records_to_process = [
    {
        "url": "https://theodi.org/insights/reports/how-an-ai-ready-national-data-library-would-help-uk-science/",
        "doi": "10.61557/ODZD4015"
    },
    {
        "url": "https://theodi.org/insights/reports/trust-and-transparency-in-privacy-enhancing-technologies/",
        "doi": "10.61557/ASKZ9013"
    },
    {
        "url": "https://theodi.org/insights/reports/mapping-the-role-of-data-work-in-ai-supply-chains/",
        "doi": "10.61557/ZRSB9894"
    },
    {
        "url": "https://theodi.org/insights/reports/a-framework-for-ai-ready-data/",
        "doi": "10.61557/ODEX6433"
    },
    {
        "url": "https://theodi.org/insights/reports/data-infrastructure-for-a-healthy-nation/",
        "doi": "10.61557/JULR4284"
    },
    {
        "url": "https://theodi.org/insights/reports/an-odi-european-data-and-ai-policy-manifesto/",
        "doi": "10.61557/LPXQ8240"
    },
    {
        "url": "https://theodi.org/insights/reports/towards-the-ethical-use-of-synthetic-data-in-health-research/",
        "doi": "10.61557/MAHO3973"
    },
    {
        "url": "https://theodi.org/insights/reports/shared-data-licensing-across-the-uks-energy-networks/",
        "doi": "10.61557/XVYL3760"
    },
    {
        "url": "https://theodi.org/insights/reports/insights-from-uk-councils-on-standards-readiness-and-reform-to-modernise-public-data-for-ai/",
        "doi": "10.61557/LURR7702"
    },
    {
        "url": "https://theodi.org/insights/projects/odi-and-cocoda-technolegal-solutions-for-online-platform-accountability/",
        "doi": "10.61557/QYTA5086"
    },
    {
        "url": "https://theodi.org/insights/reports/an-open-data-strategy-for-the-water-industry/",
        "doi": "10.61557/IGPR2799"
    },
    {
        "url": "https://theodi.org/insights/projects/open-data-use-case-observatory/",
        "doi": "10.61557/AWBG3088"
    },
    # {
    #     "url": "",
    #     "doi": ""
    # },
    # Add more rows as needed...
]

# ==========================================
# 2. HELPERS & SCRAPERS
# ==========================================

def clean_orcid(orcid_url):
    """
    Extracts a valid ORCID (0000-0000-0000-000X) from a URL,
    stripping typos like trailing 'v'.
    """
    if not orcid_url: return None
    
    # Regex for standard ORCID pattern (digits or X at the end)
    match = re.search(r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX])', orcid_url)
    if match:
        clean_id = match.group(1)
        return f"https://orcid.org/{clean_id}"
    return None

def get_orcid_from_profile(profile_url):
    print(f"   --> Checking profile: {profile_url}")
    try:
        time.sleep(0.5) 
        r = requests.get(profile_url)
        if r.status_code != 200: return None
            
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Look for the ORCID block
        orcid_li = soup.select_one('.profile-block__orcid a')
        
        if orcid_li and orcid_li.get('href'):
            raw_href = orcid_li['href']
            # Run it through the cleaner immediately
            return clean_orcid(raw_href)
            
    except Exception as e:
        print(f"   [!] Error fetching ORCID: {e}")
    return None

def scrape_report(url, doi):
    print(f"Processing: {url}")
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
            
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # 1. Title
        title_tag = soup.select_one('h1.header__title')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
        
        # 2. Date
        date_obj = None
        time_tag = soup.select_one('time')
        if time_tag and time_tag.get('datetime'):
            try:
                date_obj = datetime.datetime.strptime(str(time_tag['datetime']), "%Y-%m-%d")
            except ValueError:
                pass 
        
        # 3. Authors
        authors = []
        author_list_items = soup.select('.authors-list li')
        
        for item in author_list_items:
            name_tag = item.select_one('.people-list__person-name a')
            
            if not name_tag:
                # Fallback for plain text names
                name_tag = item.select_one('.people-list__person-name')
                profile_link = None
                full_name = name_tag.get_text(strip=True) #type: ignore
            else:
                profile_link = name_tag['href']
                if str(profile_link).startswith('/'):
                    profile_link = f"https://theodi.org{profile_link}"
                full_name = name_tag.get_text(strip=True)
            
            # Name splitting
            name_parts = full_name.split()
            if len(name_parts) > 1:
                surname = name_parts[-1]
                given_name = " ".join(name_parts[:-1])
            else:
                surname = full_name
                given_name = ""
            
            # Fetch ORCID
            orcid = None
            if profile_link and "theodi.org" in profile_link:
                orcid = get_orcid_from_profile(profile_link)
                
            authors.append({
                'given': given_name,
                'family': surname,
                'orcid': orcid,
                'affiliation': "The Open Data Institute"
            })
            
        return {
            "doi": doi,
            "url": url,
            "title": title,
            "date": date_obj,
            "authors": authors
        }

    except Exception as e:
        print(f"   [!] Critical error processing {url}: {e}")
        return None

# ==========================================
# 3. XML GENERATION (STRICT ORDER)
# ==========================================

processed_data = []

# Scrape
for record in records_to_process:
    data = scrape_report(record['url'], record['doi'])
    if data:
        processed_data.append(data)

# Setup XML
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_CROSSREF = "http://www.crossref.org/schema/5.3.1"
SCHEMA_LOC = "http://www.crossref.org/schema/5.3.1 http://www.crossref.org/schemas/crossref5.3.1.xsd"

root = ET.Element("doi_batch", version="5.3.1", xmlns=NS_CROSSREF)
root.set("xmlns:xsi", NS_XSI)
root.set("xsi:schemaLocation", SCHEMA_LOC)

head = ET.SubElement(root, "head")
ET.SubElement(head, "doi_batch_id").text = BATCH_ID
ET.SubElement(head, "timestamp").text = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
depositor = ET.SubElement(head, "depositor")
ET.SubElement(depositor, "depositor_name").text = DEPOSITOR_NAME
ET.SubElement(depositor, "email_address").text = DEPOSITOR_EMAIL
ET.SubElement(head, "registrant").text = REGISTRANT

body = ET.SubElement(root, "body")

for item in processed_data:
    report = ET.SubElement(body, "report-paper")
    report_meta = ET.SubElement(report, "report-paper_metadata", language="en")
    
    # --- ORDER FIX 1: Contributors MUST come before Titles ---
    if item['authors']:
        contributors = ET.SubElement(report_meta, "contributors")
        for i, auth in enumerate(item['authors']):
            seq = "first" if i == 0 else "additional"
            person = ET.SubElement(contributors, "person_name", sequence=seq, contributor_role="author")
            
            ET.SubElement(person, "given_name").text = auth['given']
            ET.SubElement(person, "surname").text = auth['family']
            
            # --- ORDER FIX 2: Affiliations MUST come before ORCID ---
            # --- STRUCTURE FIX: Nested <institution> tags ---
            affiliations = ET.SubElement(person, "affiliations")
            inst = ET.SubElement(affiliations, "institution")
            ET.SubElement(inst, "institution_name").text = auth['affiliation']
            
            # --- DATA FIX: Clean ORCID ---
            if auth['orcid']:
                # Ensure we only write valid ORCIDs
                ET.SubElement(person, "ORCID").text = auth['orcid']

    # --- Titles (After contributors) ---
    titles = ET.SubElement(report_meta, "titles")
    ET.SubElement(titles, "title").text = item['title']
    
    # --- Publication Date ---
    if item['date']:
        pub_date = ET.SubElement(report_meta, "publication_date", media_type="online")
        ET.SubElement(pub_date, "month").text = item['date'].strftime("%m")
        ET.SubElement(pub_date, "day").text = item['date'].strftime("%d")
        ET.SubElement(pub_date, "year").text = item['date'].strftime("%Y")
    
    # --- DOI Data ---
    doi_data = ET.SubElement(report_meta, "doi_data")
    ET.SubElement(doi_data, "doi").text = item['doi']
    ET.SubElement(doi_data, "resource").text = item['url']

# Save Output
xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
xml_filename = f"{BATCH_ID}.xml"

with open(xml_filename, "w", encoding="utf-8") as f:
    f.write(xml_str)

# Save Audit CSV
df = pd.DataFrame([{
    "DOI": d['doi'], 
    "Title": d['title'], 
    "Authors": str([a['family'] for a in d['authors']])
} for d in processed_data])
df.to_csv(f"{BATCH_ID}_audit.csv", index=False)

print(f"Success. Files generated:\n1. {xml_filename}\n2. {BATCH_ID}_audit.csv")