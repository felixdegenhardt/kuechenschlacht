"""
Modul für Konvertierung von JSON zu pandas DataFrame
"""

import pandas as pd
import json
from pathlib import Path


class DataFrameConverter:
    """
    Klasse für Konvertierung von Extraction-JSON zu DataFrame
    """
    
    def __init__(self):
        self.columns = [
            'Date of Show',
            'Season',
            'Episode',
            'Moderator Name',
            'Moderator Gender',
            'Candidate Name',
            'Candidate Gender',
            'Candidate Age',           # ← WIEDER HINZUGEFÜGT
            'Candidate Location',
            'Candidate Profession',
            'Dish',
            'Juror',
            'Juror Gender',
            'Order of Probing',
            'Ranking number'
        ]
    
    def json_to_rows(self, extraction_data, date, season=None, episode=None):
        """
        Konvertiert ein Extraction-JSON zu DataFrame-Rows
        """
        rows = []
        
        moderator = extraction_data.get('moderator', {})
        juror = extraction_data.get('juror', {})
        
        for candidate in extraction_data.get('candidates', []):
            row = {
                'Date of Show': date,
                'Season': season,
                'Episode': episode,
                'Moderator Name': moderator.get('name', ''),
                'Moderator Gender': moderator.get('gender', ''),
                'Candidate Name': candidate.get('name', ''),
                'Candidate Gender': candidate.get('gender', ''),
                'Candidate Age': candidate.get('age', None),  # ← WIEDER HINZUGEFÜGT
                'Candidate Location': candidate.get('location', ''),
                'Candidate Profession': candidate.get('profession', ''),
                'Dish': candidate.get('dish', ''),
                'Juror': juror.get('name', ''),
                'Juror Gender': juror.get('gender', ''),
                'Order of Probing': candidate.get('probing_order', ''),
                'Ranking number': candidate.get('ranking', '')
            }
            rows.append(row)
        
        return rows
            
    def json_file_to_rows(self, json_path, date, season=None, episode=None):
        """
        Lädt JSON-Datei und konvertiert zu Rows
        
        Args:
            json_path: Pfad zur JSON-Datei
            date: Datum der Show
            season: Season (Jahr)
            episode: Episode Nummer
            
        Returns:
            list: Liste von Row-Dicts
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.json_to_rows(data, date, season, episode)
        except Exception as e:
            print(f"  ✗ Fehler beim Laden von {json_path}: {e}")
            return []
    
    def folder_to_dataframe(self, extraction_folder, date_extractor_func):
        """
        Konvertiert alle JSON-Dateien in einem Ordner zu DataFrame
        
        Args:
            extraction_folder: Ordner mit JSON-Extraction-Dateien
            date_extractor_func: Funktion zur Datum-Extraktion aus Dateinamen
            
        Returns:
            pd.DataFrame
        """
        from utils import extract_season_episode_from_filename  # ← Import hinzufügen
        
        extraction_folder = Path(extraction_folder)
        json_files = list(extraction_folder.glob("*.json"))
        
        all_rows = []
        
        print(f"\n{'='*70}")
        print(f"Konvertiere {len(json_files)} JSON-Dateien zu DataFrame")
        print(f"{'='*70}\n")
        
        for idx, json_file in enumerate(json_files, 1):
            print(f"[{idx}/{len(json_files)}] {json_file.name}")
            
            # Datum extrahieren
            date = date_extractor_func(json_file.name)
            if not date:
                print(f"  ⚠ Konnte Datum nicht extrahieren, überspringe...")
                continue
            
            print(f"  Datum: {date}")
            
            # Season & Episode extrahieren
            season, episode = extract_season_episode_from_filename(json_file.name)
            if season and episode:
                print(f"  Season: {season}, Episode: {episode}")
            else:
                print(f"  ⚠ Konnte Season/Episode nicht extrahieren")
            
            # Konvertiere zu Rows
            rows = self.json_file_to_rows(json_file, date, season, episode)
            if rows:
                all_rows.extend(rows)
                print(f"  ✓ {len(rows)} Kandidaten hinzugefügt")
            else:
                print(f"  ✗ Keine Daten gefunden")
        
        print(f"\n{'='*70}")
        print(f"✓ Gesamt: {len(all_rows)} Einträge")
        print(f"{'='*70}\n")
        
        # Erstelle DataFrame
        df = pd.DataFrame(all_rows, columns=self.columns)
        return df
    
    def save_dataframe(self, df, output_path, format='csv'):
        """
        Speichert DataFrame in verschiedenen Formaten
        
        Args:
            df: pandas DataFrame
            output_path: Ausgabe-Pfad
            format: 'csv', 'excel', oder 'both'
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        if format in ['csv', 'both']:
            csv_path = output_path.with_suffix('.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✓ CSV gespeichert: {csv_path}")
        
        if format in ['excel', 'both']:
            excel_path = output_path.with_suffix('.xlsx')
            df.to_excel(excel_path, index=False, engine='openpyxl')
            print(f"✓ Excel gespeichert: {excel_path}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def convert_json_to_dataframe(extraction_folder, date_extractor_func):
    """
    Einfache Funktion zur Konvertierung von JSON-Ordner zu DataFrame
    
    Args:
        extraction_folder: Ordner mit JSON-Dateien
        date_extractor_func: Funktion zur Datum-Extraktion
        
    Returns:
        pd.DataFrame
    """
    converter = DataFrameConverter()
    return converter.folder_to_dataframe(extraction_folder, date_extractor_func)


def save_to_csv(df, output_path):
    """
    Speichert DataFrame als CSV
    
    Args:
        df: pandas DataFrame
        output_path: Ausgabe-Pfad
    """
    converter = DataFrameConverter()
    converter.save_dataframe(df, output_path, format='csv')


def save_to_excel(df, output_path):
    """
    Speichert DataFrame als Excel
    
    Args:
        df: pandas DataFrame
        output_path: Ausgabe-Pfad
    """
    converter = DataFrameConverter()
    converter.save_dataframe(df, output_path, format='excel')