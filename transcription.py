"""
Modul für Video-Transkription mit Whisper
"""

import whisper
from pathlib import Path


class VideoTranscriber:
    """
    Klasse für Video-Transkription mit Whisper
    """
    
    def __init__(self, model_size="medium"):
        """
        Initialisiert den Transcriber
        
        Args:
            model_size: Whisper-Modellgröße (tiny/base/small/medium/large)
        """
        self.model_size = model_size
        self.model = None

        
    def check_model_cache(self):
        """Prüft ob Modell bereits heruntergeladen wurde"""
        from pathlib import Path
        cache_dir = Path.home() / ".cache" / "whisper"
        model_file = cache_dir / f"{self.model_size}.pt"
        return model_file.exists()
        
        
    def load_model(self):
        """Lädt das Whisper-Modell (einmalig)"""
        if self.model is None:
            # Info über Download
            if not self.check_model_cache():
                sizes = {
                    'tiny': '75 MB', 'base': '142 MB', 
                    'small': '466 MB', 'medium': '1.5 GB', 
                    'large': '2.9 GB'
                }
                size = sizes.get(self.model_size, 'unknown')
                print(f"  ⚠ Modell '{self.model_size}' wird heruntergeladen (~{size})")
                print(f"  Dies geschieht nur beim ersten Mal...")
            
            print(f"  Lade Whisper-Modell '{self.model_size}'...")
            
            # Auto-detect device wenn nicht angegeben
            if self.device is None:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self.model = whisper.load_model(
                self.model_size, 
                device=self.device
            )
            
            print(f"  ✓ Modell geladen auf {self.device.upper()}")
            
        return self.model
    
    def transcribe(self, video_path, language="de"):
        """
        Transkribiert ein einzelnes Video
        """
        from pathlib import Path
        
        # Konvertiere zu Path-Objekt (handled Leerzeichen automatisch)
        video_path = Path(video_path)
        
        # Prüfe ob existiert
        if not video_path.exists():
            raise FileNotFoundError(f"Video nicht gefunden: {video_path}")
        
        self.load_model()
        
        print(f"  Transkribiere: {video_path.name}")
        
        # ← WICHTIG: str(video_path) handled Leerzeichen korrekt!
        result = self.model.transcribe(
            str(video_path),  # ← Nutze str(), nicht video_path direkt
            language=language,
            verbose=True,
            fp16=False
        )
        
        return result
    
    def transcribe_to_file(self, video_path, output_path):
        """
        Transkribiert Video und speichert direkt in Datei
        
        Args:
            video_path: Pfad zum Video
            output_path: Pfad für Output-TXT
            
        Returns:
            str: Transkript-Text
        """
        result = self.transcribe(video_path)
        transcript_text = result['text']
        
        # Speichere Transkript
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        # Optional: Speichere auch Segments mit Zeitstempeln
        segments_path = Path(output_path).with_suffix('.segments.txt')
        with open(segments_path, 'w', encoding='utf-8') as f:
            for segment in result['segments']:
                start = segment['start']
                end = segment['end']
                text = segment['text']
                f.write(f"[{start:.2f} - {end:.2f}] {text}\n")
        
        return transcript_text
    
    def batch_transcribe(self, video_folder, output_folder, skip_existing=True):
        """
        Transkribiert alle Videos in einem Ordner
        
        Args:
            video_folder: Ordner mit MP4-Dateien
            output_folder: Ausgabe-Ordner für TXT-Dateien
            skip_existing: Überspringe bereits transkribierte Videos
            
        Returns:
            dict: {video_filename: transcript_text}
        """
        video_folder = Path(video_folder)
        output_folder = Path(output_folder)
        output_folder.mkdir(exist_ok=True, parents=True)
        
        video_files = list(video_folder.glob("*.mp4"))
        transcripts = {}
        
        print(f"\n{'='*70}")
        print(f"Transkribiere {len(video_files)} Videos")
        print(f"{'='*70}\n")
        
        for idx, video_file in enumerate(video_files, 1):
            print(f"[{idx}/{len(video_files)}] {video_file.name}")
            
            output_file = output_folder / f"{video_file.stem}.txt"
            
            # Überspringe wenn bereits vorhanden
            if skip_existing and output_file.exists():
                print(f"  ✓ Transkript existiert bereits, überspringe...")
                with open(output_file, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
            else:
                transcript_text = self.transcribe_to_file(
                    str(video_file), 
                    str(output_file)
                )
                print(f"  ✓ Gespeichert: {output_file.name}")
            
            transcripts[video_file.name] = transcript_text
            print()
        
        return transcripts


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def transcribe_video(video_path, output_path=None, model_size="medium"):
    """
    Einfache Funktion zum Transkribieren eines Videos
    
    Args:
        video_path: Pfad zum Video
        output_path: Optional, Pfad für Output
        model_size: Whisper-Modellgröße
        
    Returns:
        str: Transkript-Text
    """
    transcriber = VideoTranscriber(model_size=model_size)
    
    if output_path:
        return transcriber.transcribe_to_file(video_path, output_path)
    else:
        result = transcriber.transcribe(video_path)
        return result['text']


def transcribe_folder(video_folder, output_folder, model_size="medium", skip_existing=True):
    """
    Einfache Funktion zum Transkribieren aller Videos in einem Ordner
    
    Args:
        video_folder: Ordner mit Videos
        output_folder: Ausgabe-Ordner
        model_size: Whisper-Modellgröße
        skip_existing: Überspringe bereits transkribierte Videos
        
    Returns:
        dict: {filename: transcript}
    """
    transcriber = VideoTranscriber(model_size=model_size)
    return transcriber.batch_transcribe(video_folder, output_folder, skip_existing)