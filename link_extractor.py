import re
import urllib.parse
import requests
import logging

def clean_url(url):
    """Removes query parameters and extra trailing slashes from URLs."""
    try:
        parsed = urllib.parse.urlparse(url)
        clean = f"{parsed.netloc}{parsed.path}".rstrip('/')
        if not clean:
            return url
        return clean
    except Exception:
        return url

def validate_url(url):
    """Check if link is active or broken."""
    if "mailto:" in url or "@" in url:
        return "active"
    try:
        response = requests.head(url, allow_redirects=True, timeout=2.5)
        if response.status_code < 400:
            return "active"
        else:
            return "broken"
    except Exception:
        return "broken"

def classify_and_format_link(raw_url):
    """Classifies link and prepares display properties."""
    url_lower = raw_url.lower()
    
    if 'mailto:' in url_lower or '@' in url_lower:
        email = raw_url.replace('mailto:', '')
        return 'email', email, f"mailto:{email}", ""
        
    display_text = clean_url(raw_url)
    
    if 'linkedin.com' in url_lower:
        return 'social', display_text, raw_url, 'LinkedIn'
    if 'github.com' in url_lower:
        return 'social', display_text, raw_url, 'GitHub'
    if 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'social', display_text, raw_url, 'Twitter'
        
    return 'website', display_text, raw_url, ""

def process_links(digital_text, ocr_text, embedded_links):
    """
    Extracts, cleans, deduplicates, and classifies links. Returns list of dicts.
    """
    all_text = digital_text + " " + ocr_text
    
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    
    raw_links_list = list(set(re.findall(url_pattern, all_text))) + embedded_links
    raw_links_list.extend([f"mailto:{e}" for e in set(re.findall(email_pattern, all_text))])
    
    final_links = []
    seen_display_texts = set()
    
    for raw_url in raw_links_list:
        raw_url = raw_url.rstrip('.')
        
        category, display, full_url, platform = classify_and_format_link(raw_url)
        
        # Deduplication using lowercase display text (e.g., matching github.com/user)
        dedup_key = display.lower()
        if dedup_key in seen_display_texts:
            continue
            
        seen_display_texts.add(dedup_key)
        
        status = validate_url(full_url)
        
        final_links.append({
            'url': full_url,
            'type': category,
            'display': display,
            'platform': platform,
            'status': status
        })
        
    return final_links
