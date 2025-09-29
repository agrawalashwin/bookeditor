#!/usr/bin/env python3
"""
Simple script to upload text content to BookEditor
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
    print("📖 Simple Manuscript Upload Tool")
    print("=" * 40)
    
    # Get title
    title = input("Enter manuscript title: ").strip()
    if not title:
        title = "Untitled Manuscript"
    
    # Get author
    author = input("Enter author name: ").strip()
    if not author:
        author = "Unknown Author"
    
    print("\n📝 Please paste your manuscript content below.")
    print("   (Press Ctrl+D when finished, or Ctrl+C to cancel)")
    print("-" * 40)
    
    # Read content from stdin
    try:
        content_lines = []
        while True:
            try:
                line = input()
                content_lines.append(line)
            except EOFError:
                break
        
        content = '\n'.join(content_lines)
        
    except KeyboardInterrupt:
        print("\n❌ Upload cancelled.")
        return
    
    if not content.strip():
        print("❌ No content provided!")
        return
    
    print(f"\n📊 Summary:")
    print(f"   Title: {title}")
    print(f"   Author: {author}")
    print(f"   Content length: {len(content)} characters")
    print(f"   Lines: {len(content_lines)}")
    
    # Confirm upload
    confirm = input("\n🚀 Upload this manuscript? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Upload cancelled.")
        return
    
    # Upload and process
    manuscript_id = upload_manuscript(title, author, content)
    
    if manuscript_id:
        print("")
        print("🎉 Success! Your manuscript is ready for AI editing.")
        print("   🌐 Open http://localhost:3000 to start editing!")
        print("   📝 Select text and use AI suggestions")
        print("   💾 All changes are automatically versioned")

if __name__ == "__main__":
    main()
