"""
Modul für Information Extraction mit ChatGPT
"""

from openai import OpenAI
from pathlib import Path
import json


class InformationExtractor:
    """
    Klasse für Information Extraction mit ChatGPT API
    """
    
    def __init__(self, api_key, model="gpt-4o", temperature=0):
        """
        Initialisiert den Extractor
        
        Args:
            api_key: OpenAI API Key
            model: ChatGPT-Modell
            temperature: Temperatur (0.0-1.0)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    def create_prompt(self, transcript_text, date):
        """
        Erstellt den Extraction-Prompt
        """
        prompt = f"""Analysiere dieses Transkript einer "Die Küchenschlacht" Episode vom {date}.

    Extrahiere folgende Informationen und gib sie als strukturiertes JSON zurück:

    - Moderator Name und Geschlecht (m/w/d)
    - Juror Name und Geschlecht (m/w/d)
    - Für jeden Kandidaten:
      - Name und Geschlecht (m/w/d)
      - Alter (WICHTIG: Wird meist NUR visuell eingeblendet, NICHT gesprochen! Wenn nicht im Audio erwähnt → null)
      - Wohnort (Stadt, falls erwähnt, sonst null)
      - Beruf (falls erwähnt, sonst null)
      - Gericht/Dish (das komplette Gericht mit allen Details)
      - Reihenfolge der Verkostung durch den Juror (Order of Probing: 1, 2, 3, etc.). DAS FINDET RELATIV AM ENDE STATT.
      - Ranking/Platzierung (Ranking number: 1=gewonnen, 2=zweiter Platz, etc.)

    WICHTIG:
    - Das Probieren beginnt nachdem der Juror angekündigt wird (gegen Ende!). Es ist nicht die Vorstellung der Kandidaten
    - Achte auf Hinweise wie "zuerst probieren wir", "als nächstes", "zum Schluss"
    - Wenn ein Kandidat ausscheidet: höheres Ranking (schlechter)
    - Wenn Geschlecht nicht eindeutig: schätze anhand des Namens oder Pronomen
    - Moderatoren und Juroren: https://de.wikipedia.org/wiki/Die_K%C3%BCchenschlacht

    - Erfinde nichts!

    Format (NUR JSON, kein zusätzlicher Text). Nur Beispiel!
    {{{{
      "moderator": {{{{"name": "Name", "gender": "m"}}}},
      "juror": {{{{"name": "Juror Name", "gender": "w"}}}},
      "candidates": [
        {{{{
          "name": "Julius Kuschel",
          "gender": "m",
          "age": null,
          "location": "Berlin",
          "profession": "Koch",
          "dish": "Dim Sum mit Hackfleischfüllung im Pilz-Wild-Sud",
          "probing_order": 1,
          "ranking": 1
        }}}},
        {{{{
          "name": "Johannes Hamackers",
          "gender": "m",
          "age": null,
          "location": "München",
          "profession": "Ingenieur",
          "dish": "Pilz-Maultaschen mit Röstzwiebeln im Kartoffelsud",
          "probing_order": 2,
          "ranking": 2
        }}}}
      ]
    }}}}

    Transkript:
    {transcript_text}
    """
        return prompt
    
    def extract(self, transcript_text, date, max_chars=12000):
        """
        Extrahiert Informationen aus Transkript
        
        Args:
            transcript_text: Transkript
            date: Datum (YYYY-MM-DD)
            max_chars: Maximale Zeichen (wegen Token-Limit)
            
        Returns:
            str: JSON-String mit extrahierten Daten
        """
        # Begrenze Transkript-Länge
        transcript_excerpt = transcript_text[:max_chars]
        
        prompt = self.create_prompt(transcript_excerpt, date)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Du bist ein Experte für die Analyse von deutschen Kochshow-Transkripten. Du extrahierst strukturierte Daten und gibst sie als valides JSON zurück."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"  ✗ API-Fehler: {e}")
            return None
    
    def extract_to_file(self, transcript_text, date, output_path, max_chars=12000):
        """
        Extrahiert und speichert direkt in JSON-Datei
        
        Args:
            transcript_text: Transkript
            date: Datum
            output_path: Pfad für Output-JSON
            max_chars: Max. Zeichen
            
        Returns:
            dict: Geparste JSON-Daten oder None
        """
        extraction_json = self.extract(transcript_text, date, max_chars)
        
        if extraction_json:
            # Speichere JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extraction_json)
            
            # Parse und validiere
            try:
                data = json.loads(extraction_json)
                return data
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON Parse Error: {e}")
                return None
        
        return None
    
    def batch_extract(self, transcript_folder, output_folder, date_extractor_func, 
                     skip_existing=True, max_chars=12000):
        """
        Extrahiert Informationen aus allen Transkripten
        
        Args:
            transcript_folder: Ordner mit TXT-Transkripten
            output_folder: Ausgabe-Ordner für JSON-Dateien
            date_extractor_func: Funktion zum Extrahieren des Datums aus Dateinamen
            skip_existing: Überspringe bereits extrahierte Dateien
            max_chars: Max. Zeichen
            
        Returns:
            dict: {filename: extracted_data}
        """
        transcript_folder = Path(transcript_folder)
        output_folder = Path(output_folder)
        output_folder.mkdir(exist_ok=True, parents=True)
        
        transcript_files = list(transcript_folder.glob("*.txt"))
        # Ignoriere .segments.txt Dateien
        transcript_files = [f for f in transcript_files if not f.stem.endswith('.segments')]
        
        extractions = {}
        
        print(f"\n{'='*70}")
        print(f"Extrahiere Informationen aus {len(transcript_files)} Transkripten")
        print(f"{'='*70}\n")
        
        for idx, transcript_file in enumerate(transcript_files, 1):
            print(f"[{idx}/{len(transcript_files)}] {transcript_file.name}")
            
            output_file = output_folder / f"{transcript_file.stem}.json"
            
            # Datum extrahieren
            date = date_extractor_func(transcript_file.name)
            if not date:
                print(f"  ⚠ Konnte Datum nicht extrahieren, überspringe...")
                continue
            print(f"  Datum: {date}")
            
            # Überspringe wenn bereits vorhanden
            if skip_existing and output_file.exists():
                print(f"  ✓ Extraktion existiert bereits, überspringe...")
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # Lade Transkript
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
                
                # Extrahiere
                print(f"  → Extrahiere mit ChatGPT...")
                data = self.extract_to_file(
                    transcript_text, 
                    date, 
                    str(output_file),
                    max_chars
                )
                
                if data:
                    print(f"  ✓ Gespeichert: {output_file.name}")
                else:
                    print(f"  ✗ Extraktion fehlgeschlagen")
                    continue
            
            extractions[transcript_file.name] = data
            print()
        
        return extractions


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def extract_from_transcript(transcript_text, date, api_key, model="gpt-4o"):
    """
    Einfache Funktion zur Information Extraction
    
    Args:
        transcript_text: Transkript
        date: Datum (YYYY-MM-DD)
        api_key: OpenAI API Key
        model: ChatGPT-Modell
        
    Returns:
        dict: Extrahierte Daten
    """
    extractor = InformationExtractor(api_key=api_key, model=model)
    extraction_json = extractor.extract(transcript_text, date)
    
    if extraction_json:
        return json.loads(extraction_json)
    return None


def extract_from_folder(transcript_folder, output_folder, date_extractor_func,
                       api_key, model="gpt-4o", skip_existing=True):
    """
    Einfache Funktion zur Batch-Extraction
    
    Args:
        transcript_folder: Ordner mit Transkripten
        output_folder: Ausgabe-Ordner
        date_extractor_func: Funktion zur Datum-Extraktion
        api_key: OpenAI API Key
        model: ChatGPT-Modell
        skip_existing: Überspringe existierende
        
    Returns:
        dict: {filename: data}
    """
    extractor = InformationExtractor(api_key=api_key, model=model)
    return extractor.batch_extract(
        transcript_folder, 
        output_folder, 
        date_extractor_func,
        skip_existing
    )