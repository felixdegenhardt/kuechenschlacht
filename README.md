# Die Küchenschlacht Data Pipeline

Extract structured data from ZDF's "Die Küchenschlacht" cooking show videos.

## Install
```bash
git clone <repo-url> && cd kuechenschlacht-pipeline
python -m venv kuechenschlacht && source kuechenschlacht/bin/activate
pip install mlx-whisper openai pandas openpyxl python-dotenv
brew install ffmpeg
mkdir -p videos transcripts extractions output
```

## Setup

Create `.env`:
```bash
echo "OPENAI_API_KEY=sk-proj-xxxxx" > .env
```

## Get Videos

1. Download videos from [ZDF Mediathek](https://www.zdf.de/show/die-kuechenschlacht) or [MediathekView](https://mediathekview.de/)
2. Place `.mp4` files in `videos/` folder
3. Each video MUST have matching `.txt` metadata file:
```
videos/
├── episode1.mp4
├── episode1.txt    ← Required!
├── episode2.mp4
└── episode2.txt    ← Required!
```

**Metadata format** (`episode1.txt`):
```
Sender:      ZDF
Titel:       Episode Title (S2023/E187)
URL
https://...
Sechs Kandidaten präsentieren ihre Gerichte, die
anschließend von Juror juror_name verkostet werden.
```

## Run
```bash
source kuechenschlacht/bin/activate
python main.py all
```

Output: `output/kuechenschlacht_data.csv` & `.xlsx`

## Output Columns

- Date, Season, Episode
- Moderator Name/Gender
- Candidate Name/Gender/Location/Profession
- Dish (full description)
- Juror Name/Gender
- Order of Probing (tasting order)
- Ranking (1=winner, highest=eliminated)

## Config

Edit `config.py`:
- `WHISPER_MODEL = "large-v3"` (or tiny/medium for speed)
- `CHATGPT_MODEL = "gpt-4o-mini"` (or gpt-4o for quality)

## Cost

~$0.01-0.02 per episode (OpenAI API)

## Troubleshooting

- **Missing candidates?** Check `.txt` metadata exists and contains "X Kandidaten" and "Juror NAME"
- **API error?** Verify `.env` contains `OPENAI_API_KEY`
- **Slow?** Use `WHISPER_MODEL = "medium"` in config.py

## Requirements

macOS (Apple Silicon), Python 3.11+, FFmpeg
