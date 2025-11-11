#!/usr/bin/env python3
"""
Web scraping script to extract text content from Google Cloud Vertex AI documentation pages.
Extracts content from the main page and all linked pages, saving each as both .txt and .json files.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin, urlparse, unquote
import re
from pathlib import Path

# Configuration
BASE_URL = "https://docs.cloud.google.com"
MAIN_PAGE_URL = "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash-live-api"
OUTPUT_DIR = "extracted_content"
TEXT_DIR = os.path.join(OUTPUT_DIR, "text_files")
JSON_DIR = os.path.join(OUTPUT_DIR, "json_files")

# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# Delay between requests to be respectful
REQUEST_DELAY = 1.0


def sanitize_filename(url):
    """Convert URL to a safe filename."""
    # Extract path from URL
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Replace slashes and special characters
    filename = path.replace('/', '_').replace('\\', '_')
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    filename = unquote(filename)
    
    # Remove hash fragments
    if parsed.fragment:
        filename = filename.replace('#' + parsed.fragment, '')
    
    # Limit filename length
    if len(filename) > 200:
        filename = filename[:200]
    
    # Ensure it's not empty
    if not filename:
        filename = "index"
    
    return filename


def extract_text_from_soup(soup):
    """Extract clean text content from BeautifulSoup object."""
    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()
    
    # Try to find main content area
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article', re.I))
    
    if main_content:
        text = main_content.get_text(separator='\n', strip=True)
    else:
        text = soup.get_text(separator='\n', strip=True)
    
    # Clean up excessive whitespace
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:  # Only add non-empty lines
            lines.append(line)
    
    return '\n'.join(lines)


def extract_links_from_soup(soup, base_url):
    """Extract all relevant links from the page body."""
    links = set()
    
    # Find main content area
    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article', re.I))
    search_area = main_content if main_content else soup
    
    # Find all links in the content area
    for a_tag in search_area.find_all('a', href=True):
        href = a_tag['href']
        
        # Skip anchor-only links
        if href.startswith('#'):
            continue
        
        # Convert relative URLs to absolute
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        # Only include docs.cloud.google.com links
        if 'docs.cloud.google.com' in parsed.netloc:
            # Remove fragments
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"
            links.add(clean_url)
    
    return links


def fetch_page(url):
    """Fetch a page and return BeautifulSoup object."""
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Check if it's HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            print(f"  Skipping non-HTML content: {content_type}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error fetching {url}: {e}")
        return None


def save_content(url, text_content, metadata=None):
    """Save content as both .txt and .json files."""
    filename = sanitize_filename(url)
    
    # Save as text file
    txt_path = os.path.join(TEXT_DIR, f"{filename}.txt")
    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write("=" * 80 + "\n\n")
            f.write(text_content)
        print(f"  Saved text: {txt_path}")
    except Exception as e:
        print(f"  Error saving text file: {e}")
    
    # Save as JSON file
    json_path = os.path.join(JSON_DIR, f"{filename}.json")
    try:
        json_data = {
            "url": url,
            "title": metadata.get("title", "") if metadata else "",
            "text_content": text_content,
            "metadata": metadata or {}
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved JSON: {json_path}")
    except Exception as e:
        print(f"  Error saving JSON file: {e}")


def extract_title(soup):
    """Extract page title from soup."""
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    
    h1_tag = soup.find('h1')
    if h1_tag:
        return h1_tag.get_text(strip=True)
    
    return ""


def scrape_page(url, visited_urls=None):
    """Scrape a single page and return its links."""
    if visited_urls is None:
        visited_urls = set()
    
    if url in visited_urls:
        return set()
    
    visited_urls.add(url)
    
    # Fetch the page
    soup = fetch_page(url)
    if not soup:
        return set()
    
    # Extract content
    text_content = extract_text_from_soup(soup)
    title = extract_title(soup)
    
    # Save content
    metadata = {
        "title": title,
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_content(url, text_content, metadata)
    
    # Extract links
    links = extract_links_from_soup(soup, url)
    
    # Be respectful - delay between requests
    time.sleep(REQUEST_DELAY)
    
    return links


def main():
    """Main scraping function."""
    print("Starting documentation scraping...")
    print(f"Main page: {MAIN_PAGE_URL}")
    print(f"Output directory: {OUTPUT_DIR}\n")
    
    # Create output directories
    os.makedirs(TEXT_DIR, exist_ok=True)
    os.makedirs(JSON_DIR, exist_ok=True)
    
    # Track visited URLs
    visited_urls = set()
    urls_to_visit = {MAIN_PAGE_URL}
    
    # Known linked pages from the main page
    known_links = [
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/data-residency",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/security-controls",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models",
        "https://cloud.google.com/vertex-ai/generative-ai/pricing",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api/tools",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api/streamed-conversations",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-live",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api/best-practices",
        "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/code-execution-api",
    ]
    
    # Add known links to visit list
    urls_to_visit.update(known_links)
    
    # Scrape pages
    page_count = 0
    while urls_to_visit:
        current_url = urls_to_visit.pop()
        
        if current_url in visited_urls:
            continue
        
        print(f"\n[{page_count + 1}] Processing: {current_url}")
        new_links = scrape_page(current_url, visited_urls)
        
        # Add new links to visit list (only if they're relevant documentation pages)
        for link in new_links:
            if link not in visited_urls and 'vertex-ai/generative-ai' in link:
                # Limit to reasonable number of pages
                if len(visited_urls) < 50:  # Safety limit
                    urls_to_visit.add(link)
        
        page_count += 1
        
        # Safety limit
        if page_count >= 50:
            print("\nReached maximum page limit (50). Stopping.")
            break
    
    # Create summary file
    summary = {
        "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "main_page_url": MAIN_PAGE_URL,
        "total_pages_scraped": len(visited_urls),
        "pages": []
    }
    
    for url in sorted(visited_urls):
        filename = sanitize_filename(url)
        summary["pages"].append({
            "url": url,
            "text_file": f"text_files/{filename}.txt",
            "json_file": f"json_files/{filename}.json"
        })
    
    summary_path = os.path.join(OUTPUT_DIR, "scraping_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Scraping complete!")
    print(f"Total pages scraped: {len(visited_urls)}")
    print(f"Text files saved to: {TEXT_DIR}")
    print(f"JSON files saved to: {JSON_DIR}")
    print(f"Summary saved to: {summary_path}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

