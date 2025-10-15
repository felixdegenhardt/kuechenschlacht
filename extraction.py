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

    def extract_show_info_chatgpt(self, transcript_text, date, api_key, metadata=None):
        """
        Extrahiert strukturierte Informationen mit ChatGPT API
        TWO-STEP APPROACH für bessere Genauigkeit
        """
        from openai import OpenAI
        import json
        from datetime import datetime
        
        client = OpenAI(api_key=api_key)
        
        # Hole Juror & Moderator aus Metadaten
        juror_from_metadata = None
        moderator_from_metadata = None
        juror_name_for_prompt = "der Juror/die Jurorin"
        
        context_info = []
        
        if metadata:
            if metadata.get('juror_name'):
                juror_from_metadata = {
                    'name': metadata['juror_name'],
                    'gender': metadata.get('juror_gender', 'm')
                }
                juror_name_for_prompt = metadata['juror_name']
                context_info.append(f"- Juror/Jurorin: {metadata['juror_name']}")
                print(f"    ✓ Juror aus Metadaten: {metadata['juror_name']}")
            
            if metadata.get('moderator_name'):
                moderator_from_metadata = {
                    'name': metadata['moderator_name'],
                    'gender': metadata.get('moderator_gender', 'm')
                }
                context_info.append(f"- Moderator: {metadata['moderator_name']}")
                print(f"    ✓ Moderator aus Metadaten: {metadata['moderator_name']}")
            
            if metadata.get('num_candidates'):
                context_info.append(f"- Erwartete Anzahl: {metadata['num_candidates']} Kandidaten")
        
        # =========================================================================
        # Berechne erwartete Kandidaten-Anzahl basierend auf Wochentag
        # =========================================================================
        expected_candidates = metadata.get('num_candidates') if metadata else None
        
        if not expected_candidates:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                day_num = date_obj.weekday()  # Montag=0, Dienstag=1, etc.
                
                candidates_by_day = {
                    0: 6,
                    1: 5,
                    2: 4,
                    3: 3,
                    4: 2,
                }
                
                expected_candidates = candidates_by_day.get(day_num, 5)
                weekday = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'][day_num] if day_num < 5 else 'Wochenende'
                print(f"    → {weekday} → Erwarte {expected_candidates} Kandidaten")
            except:
                expected_candidates = 5
        
        context_section = ""
        if context_info:
            context_section = "\n\nKONTEXT:\n" + "\n".join(context_info)
        
        # =========================================================================
        # SCHRITT 1: Extrahiere Kandidaten (Namen, Gerichte)
        # =========================================================================
        
        prompt_step1 = f"""Analysiere dieses Transkript einer "Die Küchenschlacht" Episode vom {date}.
{context_section}

AUFGABE: Finde ALLE Kandidaten mit ihren Gerichten.

═══════════════════════════════════════════════════════════════════════════════
WIE ERKENNE ICH KANDIDATEN?
═══════════════════════════════════════════════════════════════════════════════
**Nach der Rückschau** der letzten Sendung stellt der Moderator Kandidaten vor. Häufigstes Muster zum Ende der Rückschau: 

- ", an die Töpfe, fertig los."
- "35 Minuten ab jetzt."

IGNORIERE DIE RÜCKSCHAU!

Die Vorstellung kann unterschiedlich sein:

HÄUFIGSTE MUSTER:
✓ "Herzlich willkommen, lieber [NAME]" → männlicher Kandidat
✓ "Herzlich willkommen, liebe [NAME]" → weibliche Kandidatin
✓ "Ich begrüße [NAME]"
✓ "lieber/liebe [NAME]"

NACH DER BEGRÜSSUNG:
- Moderator und Kandidat sprechen kurz
- Moderator fragt: "Was gibt es bei dir?" / "Was machst du?"
- Kandidat beschreibt sein Gericht
- → Das ist das Gericht dieses Kandidaten

WICHTIG:
- Es gibt GENAU {expected_candidates} Kandidaten in dieser Sendung
- Kandidaten werden am ANFANG vorgestellt (aus Teilen 5% - 30% des Transkripts)
- {juror_name_for_prompt} ist der JUROR - das ist KEIN Kandidat!
- Der Juror kommt erst SPÄTER und verkostet

UNTERSCHEIDUNG Kandidat vs. Juror:
- Kandidaten: Werden VORGESTELLT mit "Herzlich willkommen", KOCHEN selbst
- Juror: Kommt SPÄTER, wird EINGELADEN ("Komm rein"), VERKOSTET die Gerichte

═══════════════════════════════════════════════════════════════════════════════
GENDER ERKENNUNG
═══════════════════════════════════════════════════════════════════════════════

- "lieber [NAME]" → männlich (m)
- "liebe [NAME]" → weiblich (w)
- "der [NAME]" → männlich (m)
- "die [NAME]" → weiblich (w)

═══════════════════════════════════════════════════════════════════════════════

Extrahiere für JEDEN Kandidaten:
- name: Vollständiger Vorname
- gender: "m" oder "w"
- age: null
- location: Stadt falls erwähnt (z.B. "aus Hamburg"), sonst null
- profession: Beruf falls erwähnt (z.B. "ist Koch"), sonst null
- dish: Komplettes Gericht mit allen Details

FORMAT (NUR JSON):
{{{{
  "candidates": [
    {{{{
      "name": "Max",
      "gender": "m",
      "age": null,
      "location": "Berlin",
      "profession": "Koch",
      "dish": "Rinderfilet mit Rotweinsoße und Kartoffelgratin"
    }}}}
  ]
}}}}

KRITISCH: Finde GENAU {expected_candidates} Kandidaten - nicht mehr, nicht weniger!
Erfinde KEINE Namen - nur echte Kandidaten aus dem Transkript!

Transkript (Anfang):
{transcript_text[:12000]}
"""

        try:
            print(f"    → Schritt 1: Extrahiere Kandidaten und Gerichte...")
            print(f"    → Erwarte GENAU {expected_candidates} Kandidaten")
            
            response1 = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Du extrahierst Kandidaten aus deutschen Kochshow-Transkripten.

STRIKTE REGELN:
1. Kandidaten werden am Anfang vorgestellt mit "Herzlich willkommen, lieber/liebe [NAME]"
2. Es gibt GENAU {expected_candidates} Kandidaten - nicht mehr, nicht weniger!
3. {juror_name_for_prompt} ist der Juror - das ist KEIN Kandidat!
4. Erfinde KEINE Namen - nur echte Kandidaten aus dem Transkript!
5. Gender: "lieber"=männlich(m), "liebe"=weiblich(w)

Du gibst valides JSON zurück mit GENAU {expected_candidates} Kandidaten."""
                    },
                    {
                        "role": "user",
                        "content": prompt_step1
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            candidates_data = json.loads(response1.choices[0].message.content)
            candidates = candidates_data.get('candidates', [])
            
            if not candidates:
                print(f"    ✗ Keine Kandidaten gefunden!")
                return None
            
            print(f"    ✓ {len(candidates)} Kandidaten gefunden: {[c['name'] for c in candidates]}")
            
            if len(candidates) != expected_candidates:
                print(f"    ⚠ WARNUNG: Erwartet {expected_candidates}, gefunden {len(candidates)}")
                
                if len(candidates) < expected_candidates:
                    print(f"    → Nachsuche für {expected_candidates - len(candidates)} fehlende Kandidaten...")
                    
                    found_names = ', '.join([c['name'] for c in candidates])
                    
                    retry_prompt = f"""Im Transkript wurden {len(candidates)} Kandidaten gefunden:
{found_names}

Aber es sollten GENAU {expected_candidates} Kandidaten sein!

Suche SORGFÄLTIG nach den FEHLENDEN {expected_candidates - len(candidates)} Kandidaten:
- Suche nach "Herzlich willkommen, lieber/liebe [NAME]"
- Ignoriere {juror_name_for_prompt} (Juror)
- Ignoriere bereits gefundene: {found_names}
- Ignoriere die ersten 5% des Transkripts!
- ERFINDE KEINE Namen!

Gib NUR die FEHLENDEN Kandidaten zurück (gleiche JSON-Struktur).

Transkript:
{transcript_text[:12000]}
"""
                    
                    retry_response = client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "Du suchst fehlende Kandidaten. Erfinde KEINE Namen!"},
                            {"role": "user", "content": retry_prompt}
                        ],
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    
                    retry_data = json.loads(retry_response.choices[0].message.content)
                    additional_candidates = retry_data.get('candidates', [])
                    
                    if additional_candidates:
                        existing_names = [c['name'].lower() for c in candidates]
                        new_candidates = [c for c in additional_candidates if c['name'].lower() not in existing_names]
                        
                        if new_candidates:
                            print(f"    ✓ {len(new_candidates)} zusätzliche Kandidaten gefunden:")
                            for add_cand in new_candidates:
                                print(f"       + {add_cand.get('name')}")
                            candidates.extend(new_candidates)
                            print(f"    → Total: {len(candidates)} Kandidaten")
                
                elif len(candidates) > expected_candidates:
                    print(f"    ⚠ Zu viele Kandidaten! Möglicherweise wurde {juror_name_for_prompt} fälschlicherweise als Kandidat erkannt.")
            
            candidate_names = [c['name'] for c in candidates]
            candidate_dishes = [c['dish'] for c in candidates]
            
            prompt_step2 = f"""Dies ist der END-TEIL eines "Die Küchenschlacht" Transkripts vom {date}.

KANDIDATEN (bereits identifiziert):
{', '.join(candidate_names)}

GERICHTE:
{chr(10).join([f"- {name}: {dish}" for name, dish in zip(candidate_names, candidate_dishes)])}

AUFGABE: Bestimme probing_order und ranking für JEDEN Kandidaten.

═══════════════════════════════════════════════════════════════════════════════
VERKOSTUNGSREIHENFOLGE (probing_order)
═══════════════════════════════════════════════════════════════════════════════

{juror_name_for_prompt} verkostet die Gerichte in einer bestimmten Reihenfolge.

VERKOSTUNG beginnt NACHDEM {juror_name_for_prompt} kommt:
- "Kommt rein zu uns, {juror_name_for_prompt}"
- "Herzlich willkommen, {juror_name_for_prompt}"

WICHTIGE MARKER:
✓ "Dann fange ich doch direkt mal an" → ERSTES Gericht (probing_order: 1)
✓ "Es geht weiter" → NÄCHSTES Gericht
✓ "Jetzt wird es interessant" → NÄCHSTES Gericht
✓ Jedes Mal wenn {juror_name_for_prompt} ein NEUES Gericht beschreibt → nächste Nummer

Zähle die Gerichte IN DER REIHENFOLGE wie {juror_name_for_prompt} sie verkostet!

═══════════════════════════════════════════════════════════════════════════════
RANKING (Platzierung)
═══════════════════════════════════════════════════════════════════════════════

Am ENDE entscheidet {juror_name_for_prompt} wer weiterkommt.

RANKING-SYSTEM:
- ranking: 1 = GEWINNER (als ERSTES weitergeschickt)
- ranking: 2 = zweiter Platz (als ZWEITES weitergeschickt)
- ranking: 3 = dritter Platz
- ranking: 4 = vierter Platz
- ranking: {len(candidates)} = VERLIERER (NICHT weitergeschickt, scheidet aus)

{juror_name_for_prompt} sagt:
1. "[Gericht A] ist eine Runde weiter" → ranking 1 (GEWINNER!)
2. "Das nächste Gericht... [Gericht B]" → ranking 2
3. "[Gericht C] hat es verdient" → ranking 3
4. "Ich kann [Gericht X] nicht weiter schicken" → ranking {len(candidates)} (VERLIERER!)

WICHTIG:
- Wer als ERSTES weitergeschickt wird = ranking 1 (BESTE Platzierung!)
- Wer GAR NICHT weitergeschickt wird = ranking {len(candidates)} (SCHLECHTESTE Platzierung!)

═══════════════════════════════════════════════════════════════════════════════

    Gib für JEDEN Kandidaten probing_order und ranking zurück:

    FORMAT (NUR JSON):
    {{{{
      "results": [
        {{{{"name": "Max", "probing_order": 1, "ranking": 3}}}},
        {{{{"name": "Lisa", "probing_order": 2, "ranking": 1}}}}
      ]
    }}}}

    Transkript (END-TEIL mit Verkostung und Bewertung):
    {transcript_text[-10000:]}
    """

            print(f"    → Schritt 2: Extrahiere probing_order und ranking...")
            response2 = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Du analysierst Kochshow-Verkostungen und Bewertungen.

    WICHTIG:
    - probing_order = Reihenfolge wie {juror_name_for_prompt} die Gerichte verkostet (1, 2, 3...)
    - ranking 1 = GEWINNER (als erstes weitergeschickt)
    - ranking {len(candidates)} = VERLIERER (nicht weitergeschickt, ausgeschieden)
    - Wer als ERSTES weitergeschickt wird hat ranking 1, nicht ranking {len(candidates)}!"""
                    },
                    {
                        "role": "user",
                        "content": prompt_step2
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            order_ranking_data = json.loads(response2.choices[0].message.content)
            results = order_ranking_data.get('results', [])
            
            # =====================================================================
            # SCHRITT 3: Kombiniere beide Ergebnisse
            # =====================================================================
            
            if not results:
                print(f"    ⚠ Schritt 2 lieferte keine Results!")
                for candidate in candidates:
                    candidate['probing_order'] = None
                    candidate['ranking'] = None
            else:
                print(f"    ✓ {len(results)} Results von Schritt 2 erhalten")
                print(f"    → Schritt 3: Kombiniere Ergebnisse...")
                
                # Merge results
                for candidate in candidates:
                    candidate_name = candidate.get('name', '').strip().lower()
                    
                    if not candidate_name:
                        candidate['probing_order'] = None
                        candidate['ranking'] = None
                        continue
                    
                    # Finde matching result
                    matching_result = None
                    
                    for result in results:
                        if not isinstance(result, dict):
                            continue
                        
                        result_name = result.get('name', '').strip().lower()
                        
                        if not result_name:
                            continue
                        
                        # Matching
                        if (result_name == candidate_name or 
                            result_name in candidate_name or 
                            candidate_name in result_name or
                            (result_name.split()[0] == candidate_name.split()[0] if ' ' in candidate_name else False)):
                            matching_result = result
                            break
                    
                    if matching_result:
                        candidate['probing_order'] = matching_result.get('probing_order', None)
                        candidate['ranking'] = matching_result.get('ranking', None)
                        print(f"    ✓ {candidate['name']}: order={candidate['probing_order']}, rank={candidate['ranking']}")
                    else:
                        candidate['probing_order'] = None
                        candidate['ranking'] = None
                        print(f"    ⚠ Keine Zuordnung für '{candidate['name']}'")
                                    
                print(f"    ✓ Merge abgeschlossen")
            
            final_data = {
                'candidates': candidates
            }
            
            if juror_from_metadata:
                final_data['juror'] = juror_from_metadata
            else:
                final_data['juror'] = None
            
            if moderator_from_metadata:
                final_data['moderator'] = moderator_from_metadata
            else:
                final_data['moderator'] = None
            
            print(f"    → Finale Daten: {len(candidates)} Kandidaten, Juror: {final_data.get('juror', {}).get('name', 'None')}")
            
            if not candidates or len(candidates) == 0:
                print(f"    ✗ WARNUNG: Keine Kandidaten in finalen Daten!")
                return None
            
            final_json = json.dumps(final_data, ensure_ascii=False, indent=2)
            return final_json
            
        except json.JSONDecodeError as e:
            print(f"    ✗ JSON Parse Error: {e}")
            return None
        except Exception as e:
            print(f"    ✗ Unerwarteter Fehler: {e}")
            import traceback
            traceback.print_exc()
            return None  

    def batch_extract(self, transcript_folder, output_folder, date_extractor_func, 
                     skip_existing=True, max_chars=12000, video_folder=None):
        """
        Extrahiert Informationen aus allen Transkripten
        """
        from pathlib import Path
        from metadata_parser import get_metadata_for_video
        import json
        
        transcript_folder = Path(transcript_folder)
        output_folder = Path(output_folder)
        output_folder.mkdir(exist_ok=True, parents=True)
        
        transcript_files = list(transcript_folder.glob("*.txt"))
        transcript_files = [f for f in transcript_files if not f.stem.endswith('.segments')]
        
        extractions = {}
        
        print(f"\n{'='*70}")
        print(f"Extrahiere Informationen aus {len(transcript_files)} Transkripten")
        print(f"{'='*70}\n")
        
        for idx, transcript_file in enumerate(transcript_files, 1):
            print(f"[{idx}/{len(transcript_files)}] {transcript_file.name}")
            
            output_file = output_folder / f"{transcript_file.stem}.json"
            
            date = date_extractor_func(transcript_file.name)
            if not date:
                print(f"  ⚠ Konnte Datum nicht extrahieren, überspringe...")
                continue
            print(f"  Datum: {date}")
            
            metadata = None
            if video_folder:
                video_path = Path(video_folder) / f"{transcript_file.stem}.mp4"
                metadata = get_metadata_for_video(video_path)
                
                if metadata:
                    print(f"  ✓ Metadaten gefunden:")
                    if metadata.get('num_candidates'):
                        print(f"    - {metadata['num_candidates']} Kandidaten")
                    if metadata.get('juror_name'):
                        print(f"    - Juror: {metadata['juror_name']}")
                    if metadata.get('moderator_name'):
                        print(f"    - Moderator: {metadata['moderator_name']}")
            
            if skip_existing and output_file.exists():
                print(f"  ✓ Extraktion existiert bereits, überspringe...")
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
                
                print(f"  → Extrahiere mit ChatGPT...")
                extraction_json = self.extract_show_info_chatgpt(
                    transcript_text, 
                    date,
                    self.client.api_key,
                    metadata=metadata
                )
                
                if extraction_json:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(extraction_json)
                    
                    try:
                        data = json.loads(extraction_json)
                        
                        if not data.get('candidates'):
                            print(f"  ⚠ WARNUNG: JSON hat keine Kandidaten!")
                        else:
                            print(f"  ✓ Gespeichert: {output_file.name} ({len(data['candidates'])} Kandidaten)")
                    
                    except json.JSONDecodeError as e:
                        print(f"  ✗ JSON Parse Error: {e}")
                        continue
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