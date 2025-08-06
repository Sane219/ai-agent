# # scraper_agent.py
# import os
# import json
# import requests
# from bs4 import BeautifulSoup
# import google.generativeai as genai
# import pandas as pd

# # --- CONFIGURATION ---
# try:
#     # This is a fallback for local development if you use a .env file
#     # from dotenv import load_dotenv
#     # load_dotenv()
#     # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
#     # For this script, we'll read it directly.
#     # Ensure you have a GOOGLE_API_KEY in your environment or hardcode it carefully.
#     GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
#     if not GOOGLE_API_KEY:
#         # A simple input fallback for ease of use.
#         GOOGLE_API_KEY = input("Please enter your Google Gemini API Key: ")

#     genai.configure(api_key=GOOGLE_API_KEY)
#     llm = genai.GenerativeModel('gemini-1.5-flash')
# except Exception as e:
#     print(f"Error configuring Google AI. Please ensure you have a valid API key. Error: {e}")
#     exit()

# # --- COMPONENT 1: WEB CONTENT SCRAPER ---
# def get_page_content(url: str) -> str:
#     """Fetches and extracts clean text content from a URL."""
#     try:
#         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
#         response = requests.get(url, headers=headers, timeout=15)
#         response.raise_for_status()
        
#         soup = BeautifulSoup(response.content, 'html.parser')
#         for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
#             script_or_style.decompose()
        
#         text = soup.get_text()
#         lines = (line.strip() for line in text.splitlines())
#         chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
#         text = '\n'.join(chunk for chunk in chunks if chunk)
        
#         print(f"Successfully scraped content from {url}. Content length: {len(text)} characters.")
#         return text
#     except requests.exceptions.RequestException as e:
#         print(f"Error scraping {url}: {e}")
#         return None

# # --- COMPONENT 2: THE INFORMATION EXTRACTION AGENT'S PROMPT ---
# EXTRACTION_PROMPT_TEMPLATE = """
# You are an expert data extraction AI. Your task is to read the unstructured text from a government scheme webpage and extract the specified information into a clean JSON object.

# Follow these rules strictly:
# 1.  Extract the information for the fields listed in the desired JSON format below.
# 2.  If you cannot find a specific piece of information, you MUST use the value "Information not found". Do not leave any field blank.
# 3.  The `description` should be a concise one or two-sentence summary.
# 4.  `min_age` and `max_age` should be integers. If not specified, use 0 and 100 respectively.
# 5.  `min_income` and `max_income` should be integers. If not specified, use 0 and 5000000 respectively.
# 6.  Your entire response MUST be only the JSON object, with no other text before or after it.

# **Desired JSON Format:**
# {{
#   "scheme_name": "string",
#   "description": "string",
#   "category": "string (e.g., Health, Agriculture, Education, Social Justice, Women & Child Development)",
#   "target_state": "string (e.g., All, Maharashtra, Delhi)",
#   "min_age": "integer",
#   "max_age": "integer",
#   "min_income": "integer",
#   "max_income": "integer",
#   "target_gender": "string (e.g., Any, Male, Female)",
#   "eligibility_criteria": "string",
#   "documents_required": "string",
#   "application_steps": "string"
# }}

# ---
# **Unstructured Web Page Text to Analyze:**
# {web_page_text}
# ---
# """

# # --- COMPONENT 3: THE ORCHESTRATOR ---
# def main():
#     """Main function to run the scraping and extraction pipeline."""
#     target_urls = {
#         "https://www.india.gov.in/spotlight/ayushman-bharat-pradhan-mantri-jan-arogya-yojana": "static",
#         "https://pib.gov.in/PressReleasePage.aspx?PRID=1983842": "static",

#         # Add your new, good links here, replacing the broken one.
#         "https://pib.gov.in/PressReleaseIframePage.aspx?PRID=2005838": "static"
#     }
    
#     all_extracted_schemes = []
    
#     for url in target_urls:
#         print("-" * 50)
#         scraped_text = get_page_content(url)
        
#         if scraped_text:
#             prompt = EXTRACTION_PROMPT_TEMPLATE.format(web_page_text=scraped_text)
            
#             print("Sending text to AI for information extraction...")
#             try:
#                 response = llm.generate_content(prompt)
#                 json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
#                 scheme_data = json.loads(json_string)
#                 scheme_data['official_link'] = url
                
#                 all_extracted_schemes.append(scheme_data)
#                 print(f"Successfully extracted data for: {scheme_data.get('scheme_name')}")
                
#             except (json.JSONDecodeError, Exception) as e:
#                 print(f"Could not parse AI response for URL {url}. Error: {e}")

#     if not all_extracted_schemes:
#         print("No new schemes were extracted. Exiting.")
#         return

#     output_filename = 'schemes.json'
#     with open(output_filename, 'w', encoding='utf-8') as f:
#         json.dump(all_extracted_schemes, f, indent=4, ensure_ascii=False)
    
#     print("-" * 50)
#     print(f"Successfully saved {len(all_extracted_schemes)} schemes to {output_filename}")
    
#     print("\nLoading the new data into a Pandas DataFrame:")
#     df = pd.read_json(output_filename)
#     print(df.info())

# if __name__ == "__main__":
#     main()












































# scraper_agent.py (Final Version with Smarter Prompt)
import os
import json
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import pandas as pd

# --- 1. CONFIGURATION ---
try:
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        GOOGLE_API_KEY = input("Please enter your Google Gemini API Key: ")
    genai.configure(api_key=GOOGLE_API_KEY)
    llm = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Google AI: {e}")
    exit()

# --- 2. UPGRADED SCRAPER ---
def get_page_data_static(url: str) -> dict:
    """Fetches text AND title from a static URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the page title
        page_title = soup.title.string if soup.title else "No Title Found"
        
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        print(f"STATIC SCRAPE OK: {url}. Title: '{page_title}'. Length: {len(text)}.")
        return {"text": text, "title": page_title}
        
    except requests.exceptions.RequestException as e:
        print(f"Error during static scrape of {url}: {e}")
        return None

# --- 3. THE ULTIMATE EXTRACTION PROMPT ---
# In scraper_agent.py

EXTRACTION_PROMPT_TEMPLATE = """
You are an expert data extraction AI. Your task is to read the unstructured text from a government scheme webpage and extract the specified information into a clean JSON object.

Follow these rules strictly:
1.  Extract the information for the fields listed in the desired JSON format below.
2.  If you cannot find an official scheme name in the text, use a concise version of the webpage's title for the `scheme_name`.
3.  For text fields like `description`, `eligibility_criteria`, etc., if you cannot find the information, you MUST use the value "Information not found".
4.  **CRITICAL RULE FOR NUMBERS:** For numeric fields (`min_age`, `max_age`, `min_income`, `max_income`), if the information is not found, you MUST use a default integer value.
    - For `min_age` and `min_income`, use `0`.
    - For `max_age`, use `100`.
    - For `max_income`, use `5000000`.
    - DO NOT write text like 'Information not found' in these number fields.
5.  Your entire response MUST be only the JSON object, with no other text before or after it.

**Desired JSON Format:**
{{
  "scheme_name": "string",
  "description": "string",
  "category": "string",
  "target_state": "string",
  "min_age": "integer",
  "max_age": "integer",
  "min_income": "integer",
  "max_income": "integer",
  "target_gender": "string",
  "eligibility_criteria": "string",
  "documents_required": "string",
  "application_steps": "string"
}}

---
**Unstructured Web Page Text to Analyze:**
{web_page_text}
---
"""

# --- 4. THE ORCHESTRATOR ---
def main():
    """Main function to run the scraping and extraction pipeline."""
    # Let's use the links from your last test run
    target_urls = [
        # The original one that works well
        "https://www.india.gov.in/spotlight/ayushman-bharat-pradhan-mantri-jan-arogya-yojana",
        
        # A PIB release for PM-SVANidhi
        "https://pib.gov.in/PressReleasePage.aspx?PRID=1983842",
        
        # A PIB release for PM-Mudra Yojana (PMMY)
        "https://pib.gov.in/PressReleaseIframePage.aspx?PRID=1914233",
        
        # A PIB release for Lakhpati Didi
        "https://pib.gov.in/PressReleaseIframePage.aspx?PRID=1997395",
        
        # A PIB release for PM Fasal Bima Yojana
        "https://pib.gov.in/PressReleaseIframePage.aspx?PRID=1900133"
    ]
    
    all_extracted_schemes = []
    
    for url in target_urls:
        print("-" * 50)
        time.sleep(5) #
        page_data = get_page_data_static(url)
        
        if page_data and len(page_data["text"]) > 100:
            prompt = EXTRACTION_PROMPT_TEMPLATE.format(
                page_title=page_data["title"],
                url=url,
                web_page_text=page_data["text"]
            )
            
            print("Sending enhanced context to AI for information extraction...")
            try:
                response = llm.generate_content(prompt)
                json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
                scheme_data = json.loads(json_string)
                scheme_data['official_link'] = url
                
                all_extracted_schemes.append(scheme_data)
                print(f"Successfully extracted data for: {scheme_data.get('scheme_name')}")
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"Could not parse AI response for URL {url}. Error: {e}")
        else:
            print(f"Skipping AI extraction for {url} due to insufficient content.")

    if not all_extracted_schemes:
        print("No new schemes were extracted. Exiting.")
        return

    output_filename = 'schemes.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_extracted_schemes, f, indent=4, ensure_ascii=False)
    
    print("-" * 50)
    print(f"Successfully saved {len(all_extracted_schemes)} schemes to {output_filename}")
    
    print("\nLoading the new data into a Pandas DataFrame:")
    df = pd.read_json(output_filename)
    print(df.info())

if __name__ == "__main__":
    main()