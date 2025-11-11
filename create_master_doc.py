#!/usr/bin/env python3
"""
Script to combine all corrected documentation text files into a single master JSON document.
"""

import json
import os
from pathlib import Path
from datetime import datetime

TEXT_DIR = "extracted_content/text_files"
OUTPUT_FILE = "extracted_content/master.doc"

def read_text_file(filepath):
    """Read a text file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def extract_url_from_content(content):
    """Extract URL from the first line of content if present."""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('URL: '):
            return line.replace('URL: ', '').strip()
    return None

def extract_title_from_content(content):
    """Try to extract a title from the content."""
    lines = content.split('\n')
    # Look for title-like lines (usually after URL and separator)
    for i, line in enumerate(lines):
        if line.startswith('URL:'):
            # Title is usually a few lines after URL
            for j in range(i+1, min(i+15, len(lines))):
                if lines[j].strip() and not lines[j].startswith('=') and len(lines[j].strip()) < 200:
                    potential_title = lines[j].strip()
                    if potential_title and not potential_title.startswith('Home'):
                        return potential_title
    return None

def main():
    """Create master JSON document from all text files."""
    print("Creating master documentation JSON...")
    
    master_doc = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "source": "Gemini 2.5 Flash Live API Documentation",
            "main_page": "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash-live-api",
            "total_pages": 0,
            "corrections_applied": {
                "concurrent_sessions": "Corrected from 5,000 to 1,000",
                "code_execution": "Removed (not supported)",
                "rag_engine": "Removed (not supported)"
            }
        },
        "pages": []
    }
    
    # Get all text files
    text_files_dir = Path(TEXT_DIR)
    if not text_files_dir.exists():
        print(f"Error: Directory {TEXT_DIR} does not exist")
        return
    
    # Get all .txt files
    text_files = sorted(text_files_dir.glob("*.txt"))
    
    print(f"Found {len(text_files)} text files")
    
    for text_file in text_files:
        filename = text_file.name
        print(f"Processing: {filename}")
        
        content = read_text_file(text_file)
        if content is None:
            continue
        
        # Extract URL and title
        url = extract_url_from_content(content)
        title = extract_title_from_content(content)
        
        # Create page entry
        page_entry = {
            "filename": filename,
            "url": url,
            "title": title,
            "content": content,
            "content_length": len(content),
            "line_count": len(content.split('\n'))
        }
        
        master_doc["pages"].append(page_entry)
    
    master_doc["metadata"]["total_pages"] = len(master_doc["pages"])
    
    # Write to JSON file
    print(f"\nWriting master document to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_doc, f, ensure_ascii=False, indent=2)
    
    print("Master document created successfully!")
    print(f"   Total pages: {master_doc['metadata']['total_pages']}")
    print(f"   Output file: {OUTPUT_FILE}")
    print(f"   File size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()

