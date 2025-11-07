# Die Küchenschlacht Analysis

## Overview

This project analyzes juror patterns in the German cooking show "Die Küchenschlacht" (The Kitchen Battle) by examining how juror and candidate gender relate to competition outcomes. Using automated transcription and AI-powered data extraction, I analyze patterns in rankings, eliminations, and tasting order across multiple seasons.

## The Show: Die Küchenschlacht

**Format**: Daily German cooking competition on ZDF, airing Monday-Friday with progressive elimination (typically starting with 6 candidates on Monday, ending with 2 in Friday's finale).

### Key Components

**Candidates**: Amateur home cooks who prepare dishes in the studio. Each introduces themselves and describes their dish.

**Juror**: Professional chef/culinary expert who tastes all dishes and decides rankings. One juror per week (same across all episodes that week).

**Moderator**: Host who guides the show and interviews candidates (not involved in judging).

**Tasting Sequence**: Juror tastes dishes one by one in a specific order, providing feedback after each. Starts with one dish, then progresses in clockwise order.

**Rankings**: At episode end, juror announces who continues and who is eliminated. Rankings: 1 (best/winner) to highest number (eliminated).

---

## Research Questions

1. **Do female jurors judge female candidates differently than male jurors?**
2. **Does tasting order predict outcomes (winner/eliminated)?**
3. **Are there gender-based patterns in judging behavior?**

---

## Data Pipeline

### Steps 1-3: Data Collection

1. **Video Download**: Episodes from ZDF Mediathek
2. **Transcription**: MLX Whisper (local, Apple Silicon)
3. **Extraction**: OpenAI GPT-4 extracts structured data

#### Install
```bash
git clone <repo-url> && cd kuechenschlacht-pipeline
python -m venv kuechenschlacht && source kuechenschlacht/bin/activate
pip install mlx-whisper openai pandas openpyxl python-dotenv
brew install ffmpeg
mkdir -p videos transcripts extractions output
```

#### Setup
```bash
echo "OPENAI_API_KEY=sk-proj-xxxxx" > .env
```

#### Get Videos
1. Download from [ZDF Mediathek](https://www.zdf.de/show/die-kuechenschlacht) or [MediathekView](https://mediathekview.de/)
2. Place `.mp4` files in `videos/` with matching `.txt` metadata

**Metadata format**:
```
Sender:      ZDF
Titel:       Episode Title (S2023/E187)
URL
https://...
Sechs Kandidaten präsentieren ihre Gerichte, die
anschließend von Juror [juror_name] verkostet werden.
```

#### Run
```bash
source kuechenschlacht/bin/activate
python main.py all
```

**Output**: `output/kuechenschlacht_data.csv` & `.xlsx`

**Config** (`config.py`):
- `WHISPER_MODEL = "large-v3"` (or tiny/medium for speed)
- `CHATGPT_MODEL = "gpt-4o-mini"` (or gpt-4o for quality)

**Cost**: ~$0.01-0.02 per episode

### Steps 4-5: Data Cleaning & Analysis
```bash
python data_cleaning.py
python analysis.py
```

**Output**: `analysis_output/` (summary tables, regressions)

---

## Sample

- **Episodes**: ~200 episodes
- **Candidates**: ~1000 contestants
- **Time Period**: 2023-2025
- **Format**: Daily elimination (Monday: 6 → Friday: 2)

---

## Key Variables

### Episode-Level
- `female_jur`: Female juror (binary)
- `female_winner`: Female candidate won (binary)
- `female_eliminated`: Female candidate eliminated (binary)
- `share_female_cand`: Proportion of female candidates
- `first_probing_winner`: First tasted won (binary)
- `last_probing_winner`: Last tasted won (binary)

### Candidate-Level
- `female_cand`: Female candidate (binary)
- `female_jur`: Female juror (binary)
- `winner`: Won episode (binary, rank=1)
- `eliminated`: Eliminated (binary, rank=max)
- `ranking`: Placement (1=best, highest=worst)
- `order_probing`: Tasting order (1, 2, 3...)

---

## Main Findings

### Candidate-Level Results (Full Sample)

**Candidate Gender**
- No significant differences in winning probability by candidate gender
- No significant differences by juror gender
- **Interpretation**: No evidence of advantages for female or male candidates

**Gender Interactions**
- Female (male) candidates with female (male) jurors: No significant difference vs. male (female) jurors
- Interaction term (female_cand × female_jur): Not significant
- **Interpretation**: Female (male) jurors do not systematically favor/penalize female (male) candidates

**Probing Order (Linear Effect)**
- Each position later in tasting order: Decreases win probability by ~5%, increases elimination probability by ~7%
- **Interpretation**: Earlier tasting positions associated with better outcomes

**Probing × Juror Interaction**
- Female jurors × probing order: Interaction coefficient suggests weaker probing order effects
- **Interpretation**: Tasting order effects appear smaller for female jurors

### Candidate-Level Results (Excluding First Probing)

**Rationale**: First position may not be random (jurors can choose starting dish), following probing is clockwise.

**Probing Order (Positions 2+)**
- Effect on winning probability diminishes
- Effect on elimination persists
- Juror gender × probing order interaction remains
- **Interpretation**: Some but not all of the probing order effect is driven by first position

---

## Statistical Specifications

### Candidate-Level Models

**Gender Interaction**:
```
DV = β₀ + β₁(female_cand) + β₂(female_jur) + β₃(female_cand × female_jur) + controls + ε
```

**Probing Order**:
```
DV = β₀ + β₁(order_probing) + β₂(female_cand) + β₃(female_jur) + controls + ε
```

**Probing × Juror Interaction**:
```
DV = β₀ + β₁(order_probing) + β₂(female_jur) + β₃(order_probing × female_jur) + β₄(female_cand) + controls + ε
```

**Controls**: `share_female_cand`, `n_cand`

---

## Interpretation

### Gender Patterns
- No evidence that female or male jurors systematically favor candidates of the same gender
- Rankings appear gender-neutral across juror/candidate combinations

### Tasting Order Effects
- Earlier tasting positions associated with better outcomes
- Effect persists (partially) even excluding first position
- Effects appear weaker for female jurors

### Possible Mechanisms
1. **Cognitive anchoring**: First dishes set reference point
2. **Comparison effects**: Later dishes compared to earlier ones
3. **Palate fatigue**: Jurors less discerning after multiple dishes
4. **Memory decay**: Earlier dishes more memorable
5. **Non-random first position**: Jurors may select preferred dish first

---

## Limitations

### 1. Data Quality
- **Transcription errors**: Whisper may misidentify names/genders
- **Extraction errors**: GPT-4 may miss candidates or misattribute rankings

### 2. Measurement
- **Candidate gender**: Inferred from pronouns/names, may have errors
- **Juror gender**: From metadata, generally accurate
- **Order of probing**: Extracted from transcript, may have sequence errors
- **Dish quality**: *Thus far* unobserved - cannot control for actual dish characteristics

### 3. External Validity
- **Single show**: Results specific to "Die Küchenschlacht"
- **German context**: May not generalize internationally
- **TV format**: Edited for entertainment

### 4. Causal Inference
- **Non-random assignment**: Tasting order (especially first position) may not be random
- **Confounders**: Dish complexity, presentation, skill, other factors not observable in the show nonrandom

### 5. Statistical
- **Sample size**: ~200 episodes, ~1000 candidates
- **Linear models**: Binary outcomes analyzed with OLS (not logit/probit)
- **Clustering**: No adjustment for episode/week/season clustering
- **Fixed effects**: No juror or candidate fixed effects

---

## Future Work
- [ ] Extract information on dish complexity using publicly available recipes
- [ ] Predict winning/elimination probability using comments of the moderator/juror -- how well does the predicted probability align with the outcome?
- [ ] Logistic regression for binary outcomes
- [ ] Clustered standard errors (by week/season)
- [ ] Weekday fixed effects
- [ ] Juror fixed effects (for repeat jurors)

---

## Files
```
├── main.py                     # Steps 1-3: Video → Extraction
├── data_cleaning.py            # Step 4: Cleaning
├── analysis.py                 # Step 5: Analysis
├── output/
│   └── kuechenschlacht_data.csv
├── analysis_output/
│   ├── summary_*.csv/tex
│   ├── regressions_*.tex
│   └── cleaned_candidate_data.csv
```

---

## Citation
```
[Felix Degenhardt] (2025). Gender Analysis in Die Küchenschlacht. 
GitHub: [https://github.com/felixdegenhardt]
```


---

## Contact

[https://felixdegenhardt.github.io/]

---

## Acknowledgments

- ZDF for "Die Küchenschlacht"
- MLX Whisper for transcription
- OpenAI for extraction
- Statsmodels contributors