import spacy
import re
import logging

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logging.warning("Downloading spaCy model en_core_web_sm...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    """
    Cleans up the text.
    Handles symbols, converts basic emojis.
    """
    # Custom Emoji translation map
    emoji_map = {
        '✔️': 'approved',
        '❌': 'rejected',
        '✅': 'approved',
        '⭐': 'star',
        '✨': 'sparkle',
        # Handle custom symbols safely
        '₹': 'rupees ',
        '%': ' percentage '
    }
    
    for e, t in emoji_map.items():
        text = text.replace(e, f" [{t}] ")
        
    return text.strip()

def detect_sections(text):
    """
    Detects standard document sections (e.g. ABOUT, SKILLS, EDUCATION)
    """
    section_patterns = ['ABOUT', 'SKILLS', 'EDUCATION', 'EXPERIENCE', 'SUMMARY', 'PROJECTS']
    sections_found = []
    
    # Very basic section heuristic: all caps line
    lines = text.split('\n')
    for idx, line in enumerate(lines):
        clean_line = line.strip().upper()
        for pat in section_patterns:
            if clean_line == pat or clean_line.startswith(pat + ":"):
                content = "\n".join(lines[idx+1:idx+6]) # Grab next 5 lines as snippet
                sections_found.append({
                    "section": pat,
                    "content": content[:150] + "..." # Brief preview
                })
    return sections_found

def extract_nlp_info(raw_text):
    """
    Uses spaCy and RegEx to pull named entities, phones, and skills.
    Spacy extracts PERSON, ORG, LOC.
    """
    text = clean_text(raw_text)
    doc = nlp(text)
    
    # 1. Spacy Entities
    entities = []
    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'LOC', 'GPE']:
            entities.append({
                "type": ent.label_.lower(),
                "value": ent.text.strip()
            })
            
    # Remove duplicates
    seen = set()
    unique_entities = []
    for e in entities:
        if e['value'] not in seen:
            seen.add(e['value'])
            unique_entities.append(e)
            
    # 2. Key Information (Name, Phone, Emails, Skills, Education)
    phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
    phones = re.findall(phone_pattern, text)
    
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(email_pattern, text)
    
    # Extract Persons for 'name' fallback (take first PERSON)
    persons = [e['value'] for e in unique_entities if e['type'] == 'person']
    
    name = "Not Found"
    base_lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 2]
    
    if persons:
        name = persons[0]
    elif base_lines:
        # Fallback: first uppercase line (excluding common headers)
        for line in base_lines:
            if line.isupper() and line not in ['RESUME', 'CV', 'CURRICULUM VITAE', 'PROFILE']:
                name = line.title()
                break
                
    if name == "Not Found" and base_lines:
        name = base_lines[0].title() # Absolute fallback to first line
    
    # Skills heuristic (keyword matching + NLP token matching)
    skill_keywords = ['python', 'java', 'c++', 'javascript', 'react', 'flask', 'machine learning', 'sql', 'aws', 'docker', 'excel', 'power bi', 'opencv', 'pandas', 'numpy', 'iot', 'arduino']
    found_skills = []
    text_lower = text.lower()
    
    # Keyword match
    for sk in skill_keywords:
        if re.search(r'\b' + re.escape(sk) + r'\b', text_lower):
            found_skills.append(sk)
            
    # NLP token matching for generic skills (Proper Nouns)
    for token in doc:
        if token.pos_ == "PROPN" and len(token.text) > 2 and token.text.istitle():
            # Basic filter to ensure it's not the person's name
            if token.text not in [p.split()[0] for p in persons]:
                if len(found_skills) < 15 and token.text.lower() not in [s.lower() for s in found_skills]:
                    # To avoid too much noise, skip very common non-skill PROPNs but allow rest
                    if token.text.lower() not in ['university', 'college', 'b.tech', 'school']:
                        found_skills.append(token.text)
            
    # Remove duplicates preserving order
    found_skills = list(dict.fromkeys(found_skills))
    
    # Education heuristic
    edu_keywords = ['university', 'college', 'degree', 'b.tech', 'b.s.', 'master', 'phd']
    found_edu = []
    for sent in doc.sents:
        sent_text = sent.text.strip()
        for sub_line in sent_text.split('\n'):
            sub_line = sub_line.strip()
            # Include only if it hits keyword and is reasonably short (not heavily descriptive)
            if any(ek in sub_line.lower() for ek in edu_keywords) and len(sub_line) < 120:
                found_edu.append(sub_line)
                
    # 3. Sections
    sections = detect_sections(text)
    
    # 4. Summary (Intelligent Structured Summary)
    role_keywords = ['developer', 'engineer', 'manager', 'analyst', 'designer', 'scientist', 'consultant', 'architect', 'student']
    role = "Professional"
    for r in role_keywords:
        if re.search(r'\b' + r + r'\b', text_lower):
            role = r.title()
            break
            
    skills_str = ", ".join(found_skills[:4]) if found_skills else "various technical areas"
    summary = f"This document is a resume of {name}, a {role} with skills in {skills_str}."
    
    return {
        "summary": summary,
        "key_information": {
            "name": name,
            "emails": list(set(emails)),
            "phone": list(set(phones))[:2], # Take max 2
            "skills": found_skills[:12],
            "education": found_edu[:3]
        },
        "sections": sections,
        "entities": unique_entities
    }
