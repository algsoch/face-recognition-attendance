#!/usr/bin/env python3
"""
Test Google Drive URL Conversion
This script tests the conversion of Google Drive share URLs to direct image URLs
"""

import re

def convert_google_drive_url(url):
    """Convert Google Drive share URL to direct image URL"""
    if not url or not isinstance(url, str):
        return None
    
    if 'drive.google.com' in url and '/file/d/' in url:
        # Extract file ID from Google Drive URL
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            # Convert to direct access URL
            direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            return direct_url
    
    return url

def test_url_conversion():
    """Test URL conversion with sample URLs"""
    test_urls = [
        "https://drive.google.com/file/d/1AZ40GsrBrb6Z6iI3yi1UDjSVDlnp1dch/view?usp=sharing",
        "https://drive.google.com/file/d/1BZ40GsrBrb6Z6iI3yi1UDjSVDlnp1xyz/view?usp=drive_link",
        "https://example.com/image.jpg",
        "",
        None
    ]
    
    print("🔗 Testing Google Drive URL Conversion")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nTest {i}:")
        print(f"  Original: {url}")
        converted = convert_google_drive_url(url)
        print(f"  Converted: {converted}")
        
        if url and 'drive.google.com' in str(url):
            if converted and 'uc?export=view&id=' in converted:
                print("  ✅ Conversion successful")
            else:
                print("  ❌ Conversion failed")
        else:
            print("  ℹ️  No conversion needed")

if __name__ == "__main__":
    test_url_conversion()
