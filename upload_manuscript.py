#!/usr/bin/env python3
"""
Script to upload your manuscript to BookEditor and trigger chunking/embedding
"""
import requests
import json
import sys
import os

API_BASE = "http://localhost:8000"

def upload_manuscript(title, author, content):
    """Upload a manuscript and trigger processing"""
    
    # Create manuscript
    print(f"Creating manuscript: {title}")
    response = requests.post(f"{API_BASE}/manuscripts/", json={
        "title": title,
        "author": author,
        "content": content
    })
    
    if response.status_code != 200:
        print(f"Error creating manuscript: {response.text}")
        return None
    
    manuscript = response.json()
    manuscript_id = manuscript["id"]
    print(f"✅ Manuscript created with ID: {manuscript_id}")
    
    # Trigger chunking and embedding
    print("🔄 Processing chunks and embeddings...")
    response = requests.post(f"{API_BASE}/manuscripts/{manuscript_id}/ingest")
    
    if response.status_code == 200:
        print("✅ Chunking and embedding completed!")
        print(f"🌐 View in browser: http://localhost:3000")
        print(f"📝 Manuscript ID: {manuscript_id}")
        
        # Save manuscript ID for the web UI
        with open("current_manuscript_id.txt", "w") as f:
            f.write(manuscript_id)
        print("💾 Manuscript ID saved to current_manuscript_id.txt")
        
        return manuscript_id
    else:
        print(f"❌ Error processing embeddings: {response.text}")
        return manuscript_id

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python upload_manuscript.py <file.txt> [title] [author]")
        print("  python upload_manuscript.py 'My Title' 'My Name' < manuscript.txt")
        print("")
        print("Examples:")
        print("  python upload_manuscript.py my_book.txt")
        print("  python upload_manuscript.py my_book.txt 'The Great Novel' 'Jane Doe'")
        return
    
    # Check if first argument is a file
    if os.path.isfile(sys.argv[1]):
        # Reading from file
        filename = sys.argv[1]
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title and author from arguments or filename
        title = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(filename))[0]
        author = sys.argv[3] if len(sys.argv) > 3 else "Unknown Author"
        
    else:
        # Arguments are title, author, and content from stdin
        title = sys.argv[1]
        author = sys.argv[2] if len(sys.argv) > 2 else "Unknown Author"
        content = sys.stdin.read()
    
    if not content.strip():
        print("❌ No content provided!")
        return
    
    print(f"📖 Title: {title}")
    print(f"✍️  Author: {author}")
    print(f"📄 Content length: {len(content)} characters")
    print("")
    
    # Upload and process
    manuscript_id = upload_manuscript(title, author, content)
    
    if manuscript_id:
        print("")
        print("🎉 Success! Your manuscript is ready for AI editing.")
        print("   Open http://localhost:3000 to start editing!")

if __name__ == "__main__":
    main()
