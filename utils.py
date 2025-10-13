"""
Hilfsfunktionen für das Projekt
"""

import re
import pandas as pd
from pathlib import Path


# ============================================================================
# DATUM-EXTRAKTION
# ============================================================================

def extract_date_from_filename(filename):
    """
    Extrahiert Datum aus verschiedenen Dateinamen-Formaten
    
    Args:
        filename: Dateiname (mit oder ohne Extension)
        
    Returns:
        str: Datum im Format YYYY-MM-DD oder None
    
    Beispiele:
        '251013_sendung_1415_dku.mp4' → '2025-10-13'
        'die-kuechenschlacht-vom-13-oktober-2025-100.txt' → '2025-10-13'
    """
    filename = str(filename).lower()
    
    # Pattern 1: YYMMDD Format (z.B. 251013)
    match = re.search(r'(\d{2})(\d{2})(\d{2})', filename)
    if match:
        year = '20' + match.group(1)
        month = match.group(2)
        day = match.group(3)
        return f"{year}-{month}-{day}"
    
    # Pattern 2: Text Format "13-oktober-2025"
    months = {
        'januar': '01', 'februar': '02', 'märz': '03', 'maerz': '03',
        'april': '04', 'mai': '05', 'juni': '06', 
        'juli': '07', 'august': '08', 'september': '09',
        'oktober': '10', 'november': '11', 'dezember': '12'
    }
    
    match = re.search(r'(\d{1,2})-([a-zä]+)-(\d{4})', filename)
    if match:
        day = match.group(1).zfill(2)
        month_name = match.group(2)
        year = match.group(3)
        month = months.get(month_name, '00')
        return f"{year}-{month}-{day}"
    
    # Pattern 3: "vom-DD-MM-YYYY" oder ähnlich
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', filename)
    if match:
        day = match.group(1).zfill(2)
        month = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"
    
    return None


# ============================================================================
# VALIDIERUNG & STATISTIKEN
# ============================================================================

def validate_dataframe(df):
    """
    Validiert DataFrame und zeigt Probleme
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: DataFrame mit Probleme-Markierungen
    """
    print("\n" + "="*70)
    print("DATEN-VALIDIERUNG")
    print("="*70 + "\n")
    
    # Fehlende Werte
    print("1. Fehlende Werte:")
    missing = df.isnull().sum()
    has_missing = False
    for col, count in missing.items():
        if count > 0:
            has_missing = True
            print(f"   {col}: {count} ({count/len(df)*100:.1f}%)")
    
    if not has_missing:
        print("   ✓ Keine fehlenden Werte!")
    
    # Ungültige Werte
    print("\n2. Ungültige Werte:")
    
    # Gender sollte m/w/d sein
    invalid_genders = df[~df['Candidate Gender'].isin(['m', 'w', 'd', ''])]['Candidate Gender'].unique()
    if len(invalid_genders) > 0:
        print(f"   ⚠ Ungültige Geschlechter: {invalid_genders}")
    else:
        print("   ✓ Alle Geschlechter valide")
    
    # Ranking sollte numerisch sein
    try:
        df['Ranking number'].astype(float)
        print("   ✓ Rankings numerisch")
    except:
        print("   ⚠ Rankings enthalten nicht-numerische Werte")
    
    # Order of Probing sollte numerisch sein
    try:
        df['Order of Probing'].astype(float)
        print("   ✓ Verkostungsreihenfolge numerisch")
    except:
        print("   ⚠ Verkostungsreihenfolge enthält nicht-numerische Werte")
    
    print("\n" + "="*70 + "\n")
    
    return df


def show_statistics(df):
    """
    Zeigt Statistiken über das DataFrame
    
    Args:
        df: pandas DataFrame
    """
    print("\n" + "="*70)
    print("STATISTIKEN")
    print("="*70 + "\n")
    
    # Grundlegende Stats
    print(f"Gesamt Einträge: {len(df)}")
    print(f"Anzahl Shows: {df['Date of Show'].nunique()}")
    print(f"Zeitraum: {df['Date of Show'].min()} bis {df['Date of Show'].max()}")
    
    # Moderatoren
    print(f"\nModeratoren ({df['Moderator Name'].nunique()}):")
    for mod in df['Moderator Name'].value_counts().head(10).items():
        print(f"  {mod[0]}: {mod[1]} Episoden")
    
    # Juroren
    print(f"\nTop Juroren ({df['Juror'].nunique()}):")
    for juror in df['Juror'].value_counts().head(10).items():
print(f"  {juror[0]}: {juror[1]} Auftritte")
    
    # Kandidaten
    print(f"\nKandidaten:")
    print(f"  Gesamt: {df['Candidate Name'].nunique()}")
    print(f"  Durchschnitt pro Show: {len(df) / df['Date of Show'].nunique():.1f}")
    
    # Geschlechterverteilung
    print(f"\nGeschlechterverteilung Kandidaten:")
    gender_counts = df['Candidate Gender'].value_counts()
    for gender, count in gender_counts.items():
        percentage = count / len(df) * 100
        gender_label = {'m': 'Männlich', 'w': 'Weiblich', 'd': 'Divers'}.get(gender, gender)
        print(f"  {gender_label}: {count} ({percentage:.1f}%)")
    
    # Gerichte-Analyse
    print(f"\nGerichte:")
    print(f"  Gesamt: {df['Dish'].nunique()}")
    
    # Häufigste Begriffe in Gerichten
    all_dishes = ' '.join(df['Dish'].dropna()).lower()
    common_words = ['mit', 'und', 'im', 'auf', 'an', 'in', 'zu', 'von']
    dish_words = [w for w in all_dishes.split() if len(w) > 4 and w not in common_words]
    from collections import Counter
    top_ingredients = Counter(dish_words).most_common(10)
    print(f"  Häufigste Begriffe in Gerichten:")
    for word, count in top_ingredients:
        print(f"    {word}: {count}x")
    
    print("\n" + "="*70 + "\n")


def export_problematic_entries(df, output_path="problematic_entries.csv"):
    """
    Exportiert problematische Einträge für manuelle Überprüfung
    
    Args:
        df: pandas DataFrame
        output_path: Ausgabe-Pfad
        
    Returns:
        pd.DataFrame: DataFrame mit problematischen Einträgen
    """
    problematic = df[df.isnull().any(axis=1)]
    
    if len(problematic) > 0:
        problematic.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"⚠ {len(problematic)} problematische Einträge exportiert → {output_path}")
        return problematic
    else:
        print("✓ Keine problematischen Einträge gefunden!")
        return pd.DataFrame()


# ============================================================================
# DATEN-CLEANING
# ============================================================================

def clean_dataframe(df):
    """
    Bereinigt DataFrame (entfernt Duplikate, korrigiert Formatierung, etc.)
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: Bereinigtes DataFrame
    """
    print("\n" + "="*70)
    print("DATEN-BEREINIGUNG")
    print("="*70 + "\n")
    
    original_len = len(df)
    
    # 1. Entferne Duplikate
    df = df.drop_duplicates()
    duplicates_removed = original_len - len(df)
    if duplicates_removed > 0:
        print(f"✓ {duplicates_removed} Duplikate entfernt")
    
    # 2. Trim Whitespace
    string_columns = df.select_dtypes(include=['object']).columns
    for col in string_columns:
        df[col] = df[col].str.strip()
    print(f"✓ Whitespace entfernt aus {len(string_columns)} Spalten")
    
    # 3. Konvertiere numerische Spalten
    df['Order of Probing'] = pd.to_numeric(df['Order of Probing'], errors='coerce')
    df['Ranking number'] = pd.to_numeric(df['Ranking number'], errors='coerce')
    print(f"✓ Numerische Spalten konvertiert")
    
    # 4. Standardisiere Gender
    gender_mapping = {
        'männlich': 'm', 'male': 'm', 'man': 'm',
        'weiblich': 'w', 'female': 'w', 'woman': 'w',
        'divers': 'd', 'diverse': 'd', 'other': 'd'
    }
    
    for col in ['Moderator Gender', 'Candidate Gender', 'Juror Gender']:
        df[col] = df[col].str.lower().map(gender_mapping).fillna(df[col])
    print(f"✓ Geschlechter standardisiert")
    
    # 5. Sortiere nach Datum
    df['Date of Show'] = pd.to_datetime(df['Date of Show'], errors='coerce')
    df = df.sort_values('Date of Show').reset_index(drop=True)
    print(f"✓ Nach Datum sortiert")
    
    print(f"\n✓ Bereinigung abgeschlossen: {len(df)} Einträge")
    print("="*70 + "\n")
    
    return df


# ============================================================================
# ANALYSE-FUNKTIONEN
# ============================================================================

def analyze_show_format(df):
    """
    Analysiert Format der Show (Anzahl Kandidaten pro Show, etc.)
    
    Args:
        df: pandas DataFrame
    """
    print("\n" + "="*70)
    print("SHOW-FORMAT ANALYSE")
    print("="*70 + "\n")
    
    candidates_per_show = df.groupby('Date of Show').size()
    
    print(f"Kandidaten pro Show:")
    print(f"  Durchschnitt: {candidates_per_show.mean():.1f}")
    print(f"  Minimum: {candidates_per_show.min()}")
    print(f"  Maximum: {candidates_per_show.max()}")
    print(f"  Median: {candidates_per_show.median():.0f}")
    
    print(f"\nVerteilung:")
    for count, freq in candidates_per_show.value_counts().sort_index().items():
        print(f"  {count} Kandidaten: {freq} Shows")
    
    print("\n" + "="*70 + "\n")


def analyze_winners(df):
    """
    Analysiert Gewinner-Statistiken
    
    Args:
        df: pandas DataFrame
        
    Returns:
        pd.DataFrame: Gewinner-DataFrame
    """
    winners = df[df['Ranking number'] == 1].copy()
    
    print("\n" + "="*70)
    print("GEWINNER-ANALYSE")
    print("="*70 + "\n")
    
    print(f"Gesamt Gewinner: {len(winners)}")
    
    # Geschlechterverteilung der Gewinner
    print(f"\nGeschlechterverteilung:")
    gender_dist = winners['Candidate Gender'].value_counts()
    for gender, count in gender_dist.items():
        percentage = count / len(winners) * 100
        gender_label = {'m': 'Männlich', 'w': 'Weiblich', 'd': 'Divers'}.get(gender, gender)
        print(f"  {gender_label}: {count} ({percentage:.1f}%)")
    
    # Mehrfach-Gewinner
    multi_winners = winners['Candidate Name'].value_counts()
    multi_winners = multi_winners[multi_winners > 1]
    
    if len(multi_winners) > 0:
        print(f"\nMehrfach-Gewinner:")
        for name, wins in multi_winners.head(10).items():
            print(f"  {name}: {wins} Siege")
    else:
        print(f"\n✓ Keine Mehrfach-Gewinner (jeder gewinnt nur einmal)")
    
    print("\n" + "="*70 + "\n")
    
    return winners


# ============================================================================
# EXPORT-FUNKTIONEN
# ============================================================================

def create_summary_report(df, output_path="summary_report.txt"):
    """
    Erstellt einen zusammenfassenden Text-Report
    
    Args:
        df: pandas DataFrame
        output_path: Ausgabe-Pfad
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("KÜCHENSCHLACHT - DATEN-ZUSAMMENFASSUNG\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Generiert am: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"GRUNDLEGENDE STATISTIKEN\n")
        f.write(f"-"*70 + "\n")
        f.write(f"Gesamt Einträge: {len(df)}\n")
        f.write(f"Anzahl Shows: {df['Date of Show'].nunique()}\n")
        f.write(f"Zeitraum: {df['Date of Show'].min()} bis {df['Date of Show'].max()}\n\n")
        
        f.write(f"MODERATOREN\n")
        f.write(f"-"*70 + "\n")
        for mod, count in df['Moderator Name'].value_counts().items():
            f.write(f"{mod}: {count} Episoden\n")
        
        f.write(f"\nJUROREN (Top 10)\n")
        f.write(f"-"*70 + "\n")
        for juror, count in df['Juror'].value_counts().head(10).items():
            f.write(f"{juror}: {count} Auftritte\n")
        
        f.write(f"\nKANDIDATEN\n")
        f.write(f"-"*70 + "\n")
        f.write(f"Gesamt: {df['Candidate Name'].nunique()}\n")
        
        gender_counts = df['Candidate Gender'].value_counts()
        f.write(f"\nGeschlechterverteilung:\n")
        for gender, count in gender_counts.items():
            percentage = count / len(df) * 100
            gender_label = {'m': 'Männlich', 'w': 'Weiblich', 'd': 'Divers'}.get(gender, gender)
            f.write(f"  {gender_label}: {count} ({percentage:.1f}%)\n")
    
    print(f"✓ Summary Report erstellt: {output_path}")


def export_pivot_tables(df, output_folder="pivot_tables"):
    """
    Erstellt verschiedene Pivot-Tabellen für Analyse
    
    Args:
        df: pandas DataFrame
        output_folder: Ausgabe-Ordner
    """
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)
    
    # 1. Moderator vs Juror
    pivot1 = pd.crosstab(df['Moderator Name'], df['Juror'])
    pivot1.to_csv(output_folder / "moderator_juror.csv", encoding='utf-8-sig')
    
    # 2. Datum vs Moderator
    pivot2 = df.pivot_table(
        values='Candidate Name', 
        index='Date of Show', 
        columns='Moderator Name', 
        aggfunc='count',
        fill_value=0
    )
    pivot2.to_csv(output_folder / "date_moderator.csv", encoding='utf-8-sig')
    
    # 3. Gender Distribution über Zeit
    pivot3 = df.pivot_table(
        values='Candidate Name',
        index='Date of Show',
        columns='Candidate Gender',
        aggfunc='count',
        fill_value=0
    )
    pivot3.to_csv(output_folder / "date_gender.csv", encoding='utf-8-sig')
    
    print(f"✓ Pivot-Tabellen erstellt in: {output_folder}/")