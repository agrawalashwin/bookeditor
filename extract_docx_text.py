#!/usr/bin/env python3
"""
Extract text from DOCX using zipfile (no external dependencies)
"""
import zipfile
import xml.etree.ElementTree as ET
import sys
import os
import re

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file using built-in libraries"""
    try:
        with zipfile.ZipFile(docx_path, 'r') as docx:
            # Read the main document
            document_xml = docx.read('word/document.xml')
            
            # Parse XML
            root = ET.fromstring(document_xml)
            
            # Define namespaces
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            
            # Extract text from paragraphs
            paragraphs = []
            for para in root.findall('.//w:p', namespaces):
                para_text = ""
                for text_elem in para.findall('.//w:t', namespaces):
                    if text_elem.text:
                        para_text += text_elem.text
                
                # Check if this is a heading by looking at style
                style_elem = para.find('.//w:pStyle', namespaces)
                if style_elem is not None:
                    style_val = style_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
                    if 'Heading' in style_val or 'Title' in style_val:
                        # Convert to markdown heading
                        if 'Heading1' in style_val or 'Title' in style_val:
                            para_text = f"# {para_text}"
                        elif 'Heading2' in style_val:
                            para_text = f"## {para_text}"
                        elif 'Heading3' in style_val:
                            para_text = f"### {para_text}"
                        elif 'Heading4' in style_val:
                            para_text = f"#### {para_text}"
                        elif 'Heading5' in style_val:
                            para_text = f"##### {para_text}"
                        elif 'Heading6' in style_val:
                            para_text = f"###### {para_text}"
                
                if para_text.strip():
                    paragraphs.append(para_text.strip())
            
            return '\n\n'.join(paragraphs)
            
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

def extract_metadata_from_docx(docx_path):
    """Extract title and author from DOCX core properties"""
    try:
        with zipfile.ZipFile(docx_path, 'r') as docx:
            # Try to read core properties
            try:
                core_props_xml = docx.read('docProps/core.xml')
                root = ET.fromstring(core_props_xml)
                
                # Define namespaces for core properties
                namespaces = {
                    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    'dcterms': 'http://purl.org/dc/terms/'
                }
                
                title_elem = root.find('.//dc:title', namespaces)
                author_elem = root.find('.//dc:creator', namespaces)
                
                title = title_elem.text if title_elem is not None and title_elem.text else None
                author = author_elem.text if author_elem is not None and author_elem.text else None
                
                return title, author
                
            except KeyError:
                # No core properties file
                return None, None
                
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_docx_text.py <file.docx>")
        print("This will extract the text and save it as a .txt file")
        return
    
    docx_path = sys.argv[1]
    
    if not os.path.isfile(docx_path):
        print(f"❌ File not found: {docx_path}")
        return
    
    if not docx_path.lower().endswith('.docx'):
        print(f"❌ File must be a .docx file")
        return
    
    print(f"📖 Extracting text from: {docx_path}")
    
    # Extract text
    content = extract_text_from_docx(docx_path)
    if not content:
        print("❌ Failed to extract text from DOCX")
        return
    
    # Extract metadata
    title, author = extract_metadata_from_docx(docx_path)
    if not title:
        title = os.path.splitext(os.path.basename(docx_path))[0]
    if not author:
        author = "Unknown Author"
    
    # Create output filename
    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    output_path = f"{base_name}_extracted.txt"
    
    # Add metadata header
    full_content = f"""Title: {title}
Author: {author}
Extracted from: {docx_path}
Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'-' * 50}

{content}"""
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"✅ Text extracted successfully!")
    print(f"📄 Title: {title}")
    print(f"✍️  Author: {author}")
    print(f"📊 Content length: {len(content)} characters")
    print(f"💾 Saved to: {output_path}")
    print("")
    print("🚀 Now you can upload this text file:")
    print(f"   python3 upload_manuscript.py '{output_path}' '{title}' '{author}'")

if __name__ == "__main__":
    main()
