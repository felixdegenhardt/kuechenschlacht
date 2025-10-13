"""
MLX-basierte Transkription für Apple Silicon
Viel schneller und stabiler als PyTorch auf M1!
"""
import mlx_whisper
from pathlib import Path


class MLXVideoTranscriber:
    """
    Whisper Transcriber mit MLX für M1/M2 Macs
    """
    
    def __init__(self, model_size="medium"):
        """
        Args:
            model_size: tiny, base, small, medium, large
        """
        self.model_size = model_size
        
        # MLX Model Namen
        model_mapping = {
            'tiny': 'mlx-community/whisper-tiny-mlx',
            'base': 'mlx-community/whisper-base-mlx', 
            'small': 'mlx-community/whisper-small-mlx',
            'medium': 'mlx-community/whisper-medium-mlx',
            'large': 'mlx-community/whisper-large-v3-mlx'
        }
        
        self.model_path = model_mapping.get(model_size, model_mapping['medium'])
        print(f"✓ MLX Whisper (optimiert für Apple Silicon)")
        print(f"  Model: {model_size}")
    
    def transcribe(self, video_path, language="de"):
        """
        Transkribiert ein Video mit MLX
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video nicht gefunden: {video_path}")
        
        print(f"  Transkribiere: {video_path.name}")
        
        # MLX Whisper transkribiert direkt
        result = mlx_whisper.transcribe(
            str(video_path),
            path_or_hf_repo=self.model_path,
            language=language,
            verbose=True
        )
        
        return result
    
    def transcribe_to_file(self, video_path, output_path):
        """
        Transkribiert und speichert direkt
        """
        result = self.transcribe(video_path)
        transcript_text = result['text']
        
        # Speichere Transkript
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        # Optional: Speichere auch Segments
        segments_path = Path(output_path).with_suffix('.segments.txt')
        with open(segments_path, 'w', encoding='utf-8') as f:
            for segment in result.get('segments', []):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '')
                f.write(f"[{start:.2f} - {end:.2f}] {text}\n")
        
        return transcript_text
    
    def batch_transcribe(self, video_folder, output_folder, skip_existing=True):
        """
        Transkribiert alle Videos in einem Ordner
        """
        video_folder = Path(video_folder)
        output_folder = Path(output_folder)
        output_folder.mkdir(exist_ok=True, parents=True)
        
        video_files = list(video_folder.glob("*.mp4"))
        transcripts = {}
        
        print(f"\n{'='*70}")
        print(f"MLX Transkription: {len(video_files)} Videos")
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
                try:
                    transcript_text = self.transcribe_to_file(
                        str(video_file), 
                        str(output_file)
                    )
                    print(f"  ✓ Gespeichert: {output_file.name}")
                except Exception as e:
                    print(f"  ✗ Fehler: {e}")
                    continue
            
            transcripts[video_file.name] = transcript_text
            print()
        
        return transcripts