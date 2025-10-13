"""
Konfigurationsdatei für das Küchenschlacht-Projekt
"""

import os

# ============================================================================
# API KEYS
# ============================================================================

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'sk-proj-...')

# ============================================================================
# ORDNER-STRUKTUR
# ============================================================================

VIDEO_FOLDER = "./Videos"
TRANSCRIPT_FOLDER = "./transcripts"
EXTRACTION_FOLDER = "./extractions"
OUTPUT_FOLDER = "./output"

# ============================================================================
# MODELL-EINSTELLUNGEN
# ============================================================================

# Whisper Model: "tiny", "base", "small", "medium", "large"
WHISPER_MODEL = "small"

# ChatGPT Model: "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
CHATGPT_MODEL = "gpt-4o"

# ChatGPT Temperatur (0.0 = deterministisch, 1.0 = kreativ)
CHATGPT_TEMPERATURE = 0

# ============================================================================
# OUTPUT-EINSTELLUNGEN
# ============================================================================

OUTPUT_CSV = "kuechenschlacht_data.csv"
OUTPUT_EXCEL = "kuechenschlacht_data.xlsx"

# ============================================================================
# VERARBEITUNGS-EINSTELLUNGEN
# ============================================================================

# Maximale Zeichen für ChatGPT-Prompt (wegen Token-Limit)
MAX_TRANSCRIPT_CHARS = 12000

# Überspringe bereits verarbeitete Videos
SKIP_EXISTING_TRANSCRIPTS = True
SKIP_EXISTING_EXTRACTIONS = True