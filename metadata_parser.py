"""
Parser für Video-Metadaten aus .txt Dateien
"""
import re
from pathlib import Path


def parse_metadata_file(txt_path):
    """
    Parst Metadaten aus .txt Datei
    
    Args:
        txt_path: Pfad zur .txt Metadaten-Datei
        
    Returns:
        dict: Metadaten mit num_candidates, juror_name, moderator_name, etc.
    """
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = {}
    
    # Beschreibung extrahieren (alles nach URL)
    lines = content.split('\n')
    description_started = False
    description_lines = []
    
    for line in lines:
        if 'URL' in line or 'http' in line:
            description_started = True
            continue
        
        if description_started and line.strip():
            description_lines.append(line.strip())
    
    description = ' '.join(description_lines)
    metadata['beschreibung'] = description
    
    # ========================================================================
    # Anzahl Kandidaten extrahieren
    # ========================================================================
    num_mapping = {
        'ein': 1, 'eine': 1,
        'zwei': 2,
        'drei': 3,
        'vier': 4,
        'fünf': 5, 'fuenf': 5,
        'sechs': 6,
        'sieben': 7,
        'acht': 8,
        'neun': 9,
        'zehn': 10
    }
    
    num_candidates = None
    
    
    # Pattern 1: "Sechs Kandidaten"
    match = re.search(r'(ein|eine|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn)\s+kandidat', description.lower())
    if match:
        num_word = match.group(1)
        num_candidates = num_mapping.get(num_word)

    # Pattern 2: "5 Kandidaten"
    if not num_candidates:
        match = re.search(r'(\d+)\s+kandidat', description.lower())
        if match:
            num_candidates = int(match.group(1))

    # Pattern 3: "Sechs Champions" (NEU)
    if not num_candidates:
        match = re.search(r'(ein|eine|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn)\s+champion', description.lower())
        if match:
            num_word = match.group(1)
            num_candidates = num_mapping.get(num_word)

    # Pattern 4: "5 Champions" (NEU)
    if not num_candidates:
        match = re.search(r'(\d+)\s+champion', description.lower())
        if match:
            num_candidates = int(match.group(1))

    
    metadata['num_candidates'] = num_candidates
    
    # ========================================================================
    # Juror Name extrahieren
    # ========================================================================
    juror_name = None
    juror_gender = None
    
    match = re.search(r'(Juror(?:in)?)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß-]+)*)', description)
    if match:
        juror_title = match.group(1)
        juror_name = match.group(2)
        juror_gender = 'w' if juror_title == 'Jurorin' else 'm'
    
    metadata['juror_name'] = juror_name
    metadata['juror_gender'] = juror_gender
    
    # ========================================================================
    # Moderator Name extrahieren (ANDERER Name als Juror!)
    # ========================================================================
    moderator_name = None
    moderator_gender = None
    
    # Entferne Juror-Name aus Beschreibung für Moderator-Suche
    description_for_moderator = description
    if juror_name:
        for name_part in juror_name.split():
            if len(name_part) > 3:
                pattern = re.compile(re.escape(name_part), re.IGNORECASE)
                description_for_moderator = pattern.sub('[JUROR]', description_for_moderator)
    
    # Suche nach anderen Namen (Format: Vorname Nachname mit Großbuchstaben)
    all_names = re.findall(r'\b([A-ZÄÖÜ][a-zäöüß]+)\s+([A-ZÄÖÜ][a-zäöüß-]+)\b', description_for_moderator)
    
    # Blacklist: Wörter die KEINE Namen sind
    blacklist_words = {
        'kandidaten', 'kandidat', 'sechs', 'fünf', 'fuenf', 'vier', 'drei',
        'sieben', 'acht', 'neun', 'zehn', 'ein', 'eine', 'zwei',
        'ihre', 'anschließend', 'von', 'die', 'der', 'das',
        'juror', 'jurorin', 'moderator', 'küchenschlacht', 'verkostet',
        'bewertet', 'werden', 'präsentieren', 'tagesmotto', 'smørrebrød',
        'deluxe', 'graubrot', 'bauernbrot', 'scotch', 'eggs'
    }
    
    if all_names:
        for first, last in all_names:
            # Skip [JUROR]
            if first == '[JUROR]' or last == '[JUROR]':
                continue
            
            # Skip Blacklist
            if first.lower() in blacklist_words or last.lower() in blacklist_words:
                continue
            
            # Gefunden!
            moderator_name = f"{first} {last}"
            moderator_gender = 'm'  # Default
            break
    
    # Wenn nichts gefunden: leer lassen (None)
    metadata['moderator_name'] = moderator_name
    metadata['moderator_gender'] = moderator_gender if moderator_name else None
    
    # ========================================================================
    # Season & Episode
    # ========================================================================
    match = re.search(r'Titel:\s*(.+)', content)
    if match:
        metadata['titel'] = match.group(1).strip()
    
    if 'titel' in metadata:
        se_match = re.search(r'\(S(\d{4})[/_]E(\d+)\)', metadata['titel'])
        if se_match:
            metadata['season'] = se_match.group(1)
            metadata['episode'] = se_match.group(2)
    
    return metadata


def get_metadata_for_video(video_path):
    """
    Lädt Metadaten für ein Video (falls .txt existiert)
    """
    video_path = Path(video_path)
    txt_path = video_path.with_suffix('.txt')
    
    if txt_path.exists():
        return parse_metadata_file(txt_path)
    
    return None


# Test
if __name__ == "__main__":
    from pathlib import Path
    
    print("\nTeste Metadaten-Parser:\n")
    print("="*70)
    
    for txt_file in Path("videos").glob("*.txt"):
        print(f"\nDatei: {txt_file.name}")
        print("-"*70)
        
        metadata = parse_metadata_file(txt_file)
        
        print(f"Anzahl Kandidaten: {metadata.get('num_candidates', 'N/A')}")
        print(f"Juror: {metadata.get('juror_name', 'N/A')} ({metadata.get('juror_gender', 'N/A')})")
        print(f"Moderator: {metadata.get('moderator_name', 'N/A')} ({metadata.get('moderator_gender', 'N/A')})")
        print(f"Season: {metadata.get('season', 'N/A')}")
        print(f"Episode: {metadata.get('episode', 'N/A')}")
        print(f"Beschreibung: {metadata.get('beschreibung', 'N/A')[:150]}...")
        print()