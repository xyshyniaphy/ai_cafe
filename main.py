
import os
import sys
import hashlib
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
SEARXNG_INSTANCE_URL = os.getenv("SEARXNG_INSTANCE_URL", "http://localhost:8888")
MAX_CAFES_TO_SEARCH = int(os.getenv("MAX_CAFES_TO_SEARCH", 10))
DATA_DIR = "data"

def get_search_results(query: str) -> list[str]:
    """
    Queries the SearxNG instance and returns a list of result URLs.
    """
    urls = []
    try:
        response = requests.get(
            SEARXNG_INSTANCE_URL,
            params={"q": query, "format": "json"}
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        for result in results:
            if len(urls) < MAX_CAFES_TO_SEARCH:
                urls.append(result.get("url"))
    except requests.exceptions.RequestException as e:
        print(f"Error querying SearxNG: {e}", file=sys.stderr)
    return urls

def scrape_and_parse_url(url: str) -> str:
    """
    Scrapes a URL using headless Chrome and parses its text content with BeautifulSoup.
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        # It's good practice to wait for the page to load, but for simplicity, we'll just get the source.
        # In a real-world scenario, you might need WebDriverWait.
        page_source = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(page_source, '''html.parser''')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
            
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        
        # Remove duplicate lines and links (simple version)
        seen = set()
        cleaned_lines = []
        for line in lines:
            if line and line not in seen:
                seen.add(line)
                cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)
        
    except Exception as e:
        print(f"Error scraping {url}: {e}", file=sys.stderr)
        return ""

def save_data(url: str, content: str):
    """
    Saves the cleaned content to a file in the data directory.
    The filename is a hash of the URL to avoid issues with special characters.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # Create a stable filename from the URL
    url_hash = hashlib.md5(url.encode('''utf-8''')).hexdigest()
    file_path = os.path.join(DATA_DIR, f"{url_hash}.md")
    
    try:
        with open(file_path, '''w''', encoding='''utf-8''') as f:
            f.write(f"# Scraped Content from {url}\n\n")
            f.write(content)
        print(f"Successfully saved data from {url} to {file_path}")
    except IOError as e:
        print(f"Error saving data for {url}: {e}", file=sys.stderr)


def main():
    """
    Main function to run the scraping process.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<train_station_name>\"", file=sys.stderr)
        sys.exit(1)
        
    train_station_name = sys.argv[1]
    query = f'{train_station_name}駅 ネットカフェ'
    
    print(f"Searching for: {query}")
    urls = get_search_results(query)
    
    if not urls:
        print("No search results found.")
        return
        
    print(f"Found {len(urls)} URLs to scrape.")
    
    for url in urls:
        if url:
            print(f"Scraping: {url}")
            content = scrape_and_parse_url(url)
            if content:
                save_data(url, content)

if __name__ == "__main__":
    main()
