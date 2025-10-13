"""
Hauptprogramm für Küchenschlacht-Datenextraktion

Pipeline:
1. Videos → Transkripte (Whisper)
2. Transkripte → JSON (ChatGPT)
3. JSON → DataFrame (pandas)
4. DataFrame → CSV/Excel
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validiere Key
if not OPENAI_API_KEY:
    print("\n❌ OPENAI_API_KEY nicht in .env gefunden!")
    print("Erstelle .env Datei mit: OPENAI_API_KEY=sk-proj-...")
    sys.exit(1)

if not OPENAI_API_KEY.startswith('sk-'):
    print("\n❌ Ungültiger OPENAI_API_KEY!")
    sys.exit(1)

print(f"✓ API Key geladen: {OPENAI_API_KEY[:7]}...")


# Importiere Module
from config import *
from transcription import VideoTranscriber
from extraction import InformationExtractor
from dataframe_conversion import DataFrameConverter
from utils import (
    extract_date_from_filename,
    validate_dataframe,
    show_statistics,
    export_problematic_entries,
    clean_dataframe,
    analyze_show_format,
    analyze_winners,
    create_summary_report,
    export_pivot_tables
)
from transcription_mlx import MLXVideoTranscriber  # ← Neu



def setup_folders():
    """Erstellt notwendige Ordner"""
    for folder in [VIDEO_FOLDER, TRANSCRIPT_FOLDER, EXTRACTION_FOLDER, OUTPUT_FOLDER]:
        Path(folder).mkdir(exist_ok=True, parents=True)


def step1_transcribe_videos():
    """
    Schritt 1: Transkribiere alle Videos
    """
    print("\n" + "="*70)
    print("SCHRITT 1: VIDEO-TRANSKRIPTION (MLX)")
    print("="*70)
    
    # Nutze MLX statt standard Whisper
    transcriber = MLXVideoTranscriber(model_size=WHISPER_MODEL)
    
    try:
        transcripts = transcriber.batch_transcribe(
            video_folder=VIDEO_FOLDER,
            output_folder=TRANSCRIPT_FOLDER,
            skip_existing=SKIP_EXISTING_TRANSCRIPTS
        )
        
        print(f"\n✓ Transkription abgeschlossen: {len(transcripts)} Videos")
        return True
        
    except Exception as e:
        print(f"\n✗ Fehler bei Transkription: {e}")
        return False


def step2_extract_information():
    """
    Schritt 2: Extrahiere Informationen aus Transkripten
    
    Returns:
        bool: True wenn erfolgreich
    """
    print("\n" + "="*70)
    print("SCHRITT 2: INFORMATION EXTRACTION")
    print("="*70)
    
    extractor = InformationExtractor(
        api_key=OPENAI_API_KEY,
        model=CHATGPT_MODEL,
        temperature=CHATGPT_TEMPERATURE
    )
    
    try:
        extractions = extractor.batch_extract(
            transcript_folder=TRANSCRIPT_FOLDER,
            output_folder=EXTRACTION_FOLDER,
            date_extractor_func=extract_date_from_filename,
            skip_existing=SKIP_EXISTING_EXTRACTIONS,
            max_chars=MAX_TRANSCRIPT_CHARS
        )
        
        print(f"\n✓ Extraktion abgeschlossen: {len(extractions)} Transkripte")
        return True
        
    except Exception as e:
        print(f"\n✗ Fehler bei Extraktion: {e}")
        return False


def step3_create_dataframe():
    """
    Schritt 3: Erstelle DataFrame aus JSON-Dateien
    
    Returns:
        pd.DataFrame oder None
    """
    print("\n" + "="*70)
    print("SCHRITT 3: DATAFRAME ERSTELLUNG")
    print("="*70)
    
    converter = DataFrameConverter()
    
    try:
        df = converter.folder_to_dataframe(
            extraction_folder=EXTRACTION_FOLDER,
            date_extractor_func=extract_date_from_filename
        )
        
        if len(df) == 0:
            print("\n⚠ DataFrame ist leer! Keine Daten gefunden.")
            return None
        
        print(f"\n✓ DataFrame erstellt: {len(df)} Einträge")
        return df
        
    except Exception as e:
        print(f"\n✗ Fehler bei DataFrame-Erstellung: {e}")
        return None


def step4_save_and_analyze(df):
    """
    Schritt 4: Speichere DataFrame und führe Analysen durch
    
    Args:
        df: pandas DataFrame
        
    Returns:
        bool: True wenn erfolgreich
    """
    print("\n" + "="*70)
    print("SCHRITT 4: SPEICHERN & ANALYSE")
    print("="*70 + "\n")
    
    converter = DataFrameConverter()
    
    try:
        # Bereinige Daten
        df = clean_dataframe(df)
        
        # Speichere CSV
        output_csv = Path(OUTPUT_FOLDER) / OUTPUT_CSV
        converter.save_dataframe(df, output_csv, format='csv')
        
        # Optional: Speichere Excel
        if OUTPUT_EXCEL:
            output_excel = Path(OUTPUT_FOLDER) / OUTPUT_EXCEL
            converter.save_dataframe(df, output_excel, format='excel')
        
        # Validierung
        validate_dataframe(df)
        
        # Statistiken
        show_statistics(df)
        
        # Format-Analyse
        analyze_show_format(df)
        
        # Gewinner-Analyse
        analyze_winners(df)
        
        # Exportiere problematische Einträge
        export_problematic_entries(
            df, 
            output_path=str(Path(OUTPUT_FOLDER) / "problematic_entries.csv")
        )
        
        # Erstelle Summary Report
        create_summary_report(
            df,
            output_path=str(Path(OUTPUT_FOLDER) / "summary_report.txt")
        )
        
        # Erstelle Pivot-Tabellen
        export_pivot_tables(
            df,
            output_folder=str(Path(OUTPUT_FOLDER) / "pivot_tables")
        )
        
        print(f"\n✓ Alle Outputs gespeichert in: {OUTPUT_FOLDER}/")
        return True
        
    except Exception as e:
        print(f"\n✗ Fehler beim Speichern/Analysieren: {e}")
        return False

def step5_cleanup_videos():
    """
    Schritt 5: Lösche Videos nach erfolgreicher Verarbeitung
    """
    from pathlib import Path
    
    print("\n" + "="*70)
    print("SCHRITT 5: CLEANUP - LÖSCHE VIDEOS")
    print("="*70)
    
    video_folder = Path(VIDEO_FOLDER)
    transcript_folder = Path(TRANSCRIPT_FOLDER)
    extraction_folder = Path(EXTRACTION_FOLDER)
    
    video_files = list(video_folder.glob("*.mp4"))
    
    if not video_files:
        print("\n✓ Keine Videos zum Löschen vorhanden")
        return True
    
    print(f"\nGefunden: {len(video_files)} Videos\n")
    
    deleted_count = 0
    kept_count = 0
    
    for video_file in video_files:
        # Prüfe ob Transkript UND Extraktion existieren
        transcript_file = transcript_folder / f"{video_file.stem}.txt"
        extraction_file = extraction_folder / f"{video_file.stem}.json"
        
        if transcript_file.exists() and extraction_file.exists():
            # Beide Files existieren → Sicher zu löschen
            try:
                file_size_mb = video_file.stat().st_size / (1024 * 1024)
                video_file.unlink()
                print(f"✓ Gelöscht: {video_file.name} ({file_size_mb:.1f} MB)")
                deleted_count += 1
            except Exception as e:
                print(f"✗ Fehler beim Löschen {video_file.name}: {e}")
                kept_count += 1
        else:
            # Noch nicht vollständig verarbeitet → Behalten
            print(f"⚠ Behalten: {video_file.name} (noch nicht vollständig verarbeitet)")
            kept_count += 1
    
    print(f"\n{'='*70}")
    print(f"CLEANUP ZUSAMMENFASSUNG")
    print(f"{'='*70}")
    print(f"Gelöscht: {deleted_count} Videos")
    print(f"Behalten: {kept_count} Videos")
    
    if deleted_count > 0:
        # Berechne gesparten Speicherplatz
        print(f"\n✓ Speicherplatz freigegeben")
    
    print(f"{'='*70}\n")
    
    return True


def run_full_pipeline():
    """
    Führt die komplette Pipeline aus
    """
    print("\n" + "="*70)
    print("KÜCHENSCHLACHT - DATEN-EXTRAKTION PIPELINE")
    print("="*70)
    print(f"\nKonfiguration:")
    print(f"  Video-Ordner: {VIDEO_FOLDER}")
    print(f"  Whisper-Modell: {WHISPER_MODEL}")
    print(f"  ChatGPT-Modell: {CHATGPT_MODEL}")
    print(f"  Output: {OUTPUT_FOLDER}")
    print("="*70)
    
    # Setup
    setup_folders()
    
    # Schritt 1: Transkription
    if not step1_transcribe_videos():
        print("\n✗ Pipeline abgebrochen nach Schritt 1")
        return False
    
    # Schritt 2: Extraktion
    if not step2_extract_information():
        print("\n✗ Pipeline abgebrochen nach Schritt 2")
        return False
    
    # Schritt 3: DataFrame
    df = step3_create_dataframe()
    if df is None:
        print("\n✗ Pipeline abgebrochen nach Schritt 3")
        return False
    
    # Schritt 4: Speichern & Analysieren
    if not step4_save_and_analyze(df):
        print("\n✗ Pipeline abgebrochen nach Schritt 4")
        return False
    
    # Schritt 5: Cleanup (Videos löschen)
    if not step5_cleanup_videos():
        print("\n✗ Pipeline abgebrochen nach Schritt 5")
        return False
    
    # Erfolg!
    print("\n" + "="*70)
    print("✓ PIPELINE ERFOLGREICH ABGESCHLOSSEN!")
    print("="*70)
    print(f"\nErgebnisse:")
    print(f"  - CSV: {OUTPUT_FOLDER}/{OUTPUT_CSV}")
    if OUTPUT_EXCEL:
        print(f"  - Excel: {OUTPUT_FOLDER}/{OUTPUT_EXCEL}")
    print(f"  - Summary Report: {OUTPUT_FOLDER}/summary_report.txt")
    print(f"  - Pivot-Tabellen: {OUTPUT_FOLDER}/pivot_tables/")
    print("="*70 + "\n")
    
    return True


def run_single_step(step_number):
    """
    Führt nur einen einzelnen Schritt aus
    """
    setup_folders()
    
    if step_number == 1:
        step1_transcribe_videos()
    elif step_number == 2:
        step2_extract_information()
    elif step_number == 3:
        df = step3_create_dataframe()
        if df is not None:
            print("\nErste 5 Zeilen:")
            print(df.head())
    elif step_number == 4:
        df = step3_create_dataframe()
        if df is not None:
            step4_save_and_analyze(df)
    elif step_number == 5:  # ← NEU
        step5_cleanup_videos()
    else:
        print(f"✗ Ungültiger Schritt: {step_number} (muss 1-5 sein)")

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

if __name__ == "__main__":
    
    # Kommandozeilen-Argumente
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "full":
            # Komplette Pipeline
            run_full_pipeline()
            
        elif command == "step":
            # Einzelner Schritt
            if len(sys.argv) > 2:
                try:
                    step = int(sys.argv[2])
                    run_single_step(step)
                except ValueError:
                    print("✗ Schritt muss eine Zahl zwischen 1-4 sein")
            else:
                print("✗ Bitte Schritt-Nummer angeben: python main.py step 1")
                
        elif command == "help":
            print("\nVerwendung:")
            print("  python main.py full          # Komplette Pipeline")
            print("  python main.py step 1        # Nur Transkription")
            print("  python main.py step 2        # Nur Extraktion")
            print("  python main.py step 3        # Nur DataFrame")
            print("  python main.py step 4        # Nur Speichern/Analyse")
            print("  python main.py help          # Diese Hilfe")
            print()
            
        else:
            print(f"✗ Unbekannter Befehl: {command}")
            print("  Verwende 'python main.py help' für Hilfe")
    
    else:
        # Keine Argumente: Standardmäßig komplette Pipeline
        run_full_pipeline()