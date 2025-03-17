import requests
from bs4 import BeautifulSoup
import html2text

from urllib.parse import urljoin

def get_links(base_url):
    """Get All links on the main doc page"""
    main_page = urljoin(base_url, "index.html")
    response = requests.get(main_page)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = set([main_page])
    for a in soup.find_all('a'):
        href = a.get("href")
        if href and not href.startswith("http"):
            full_url = urljoin(base_url, href)
            links.append(full_url)
    
    return links


def extract_text(url):
    """Fetch a URL and extract its text content."""
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Remove navigation, footers, and unnecessary elements
    for tag in soup(["nav", "header", "footer", "script", "style", "aside"]):
        tag.extract()

    # Convert HTML to readable text
    converter = html2text.HTML2Text()
    converter.ignore_links = True  # Remove links
    converter.ignore_images = True  # Remove images

    text = converter.handle(str(soup))
    return text.strip()


def fetch_top_level_documentation(base_url, seen_links=None):
    """Scrape and save all documentation into a single file."""
    if seen_links is None:
        seen_links = set()
    page_links = get_links(base_url)  
    page_links = page_links.difference(seen_links)
    docs = {}

    for link in page_links:
        try:
            text = extract_text(link)
            docs[link] = text
        except Exception as e:
            continue

    seen_links.update(page_links)
    return docs