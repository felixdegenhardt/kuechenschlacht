# analysis.py
"""
Statistical analysis for Die Küchenschlacht dataset
Run after: python data_cleaning.py
Input: cleaned_candidate_data.csv, episode_level_data.csv
Output: analysis_output/ (tables, regressions, summaries)
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.iolib.summary2 import summary_col
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path

# Create output directory
Path('analysis_output').mkdir(exist_ok=True)

# ============================================================================
# LOAD DATA
# ============================================================================

dfc = pd.read_csv('analysis_output/cleaned_candidate_data.csv')
dfe = pd.read_csv('analysis_output/episode_level_data.csv')

# Check columns
print("Episode columns:", dfe.columns.tolist())
print("Candidate columns:", dfc.columns.tolist()[:20], "...\n")

# Standardize column names
dfc = dfc.rename(columns={
    'Order of Probing': 'order_probing',
    'Ranking number': 'ranking'
})

dfe = dfe.rename(columns={
    'n_candidates': 'n_cand',
    'n_female_candidates': 'n_female_cand',
    'share_female_candidates': 'share_female_cand',
    'avg_female_ranking': 'avg_female_rank',
    'avg_female_probing': 'avg_female_prob'
})

print(f"Loaded: {len(dfc)} candidates, {len(dfe)} episodes\n")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def create_summary(df, by_var, outcome_vars, group_labels):
    """Create summary table with t-tests"""
    results = []
    
    for var in outcome_vars:
        if var not in df.columns:
            print(f"Warning: {var} not found, skipping")
            continue
            
        overall = df[var].mean()
        g0 = df[df[by_var] == 0][var].dropna()
        g1 = df[df[by_var] == 1][var].dropna()
        
        try:
            _, p = stats.ttest_ind(g1, g0, equal_var=False)
            sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        except:
            sig = ''
        
        results.append({
            'Variable': var,
            'Overall': f"{overall:.3f}",
            group_labels[0]: f"{g0.mean():.3f}",
            group_labels[1]: f"{g1.mean():.3f}",
            'Sig': sig
        })
    
    return pd.DataFrame(results)

# Episode-level summary
print("=== EPISODE-LEVEL SUMMARY ===")
ep_vars = ['n_cand', 'n_female_cand', 'share_female_cand',
           'female_moderator', 'female_winner', 'female_eliminated',
           'avg_female_rank', 'avg_female_prob',
           'first_probing_winner', 'first_probing_eliminated',
           'last_probing_winner', 'last_probing_eliminated']

ep_summary = create_summary(dfe, 'female_jur', ep_vars, ['Male Juror', 'Female Juror'])
print(ep_summary.to_string(index=False))
ep_summary.to_csv('analysis_output/summary_episode.csv', index=False)
ep_summary.to_latex('analysis_output/summary_episode.tex', index=False)

# Candidate-level summary
print("\n=== CANDIDATE-LEVEL SUMMARY ===")

# Merge episode vars to candidate level
cand_episode_merge = dfe[['year', 'Episode', 'share_female_cand', 'n_cand']].copy()
dfc = dfc.merge(cand_episode_merge, left_on=['Season', 'Episode'], right_on=['year', 'Episode'], how='left')
if 'year' in dfc.columns:
    dfc = dfc.drop('year', axis=1)

cand_vars = ['female_jur', 'share_female_cand', 'n_cand',
             'winner', 'eliminated', 'ranking', 'order_probing']

cand_summary = create_summary(dfc, 'female_cand', cand_vars, ['Male Candidate', 'Female Candidate'])
print(cand_summary.to_string(index=False))
cand_summary.to_csv('analysis_output/summary_candidate.csv', index=False)
cand_summary.to_latex('analysis_output/summary_candidate.tex', index=False)

# Female candidates only
print("\n=== FEMALE CANDIDATES BY JUROR GENDER ===")
dfc_female = dfc[dfc['female_cand'] == 1]
female_summary = create_summary(dfc_female, 'female_jur', 
                               ['winner', 'eliminated', 'ranking', 'order_probing'],
                               ['Male Juror', 'Female Juror'])
print(female_summary.to_string(index=False))
female_summary.to_csv('analysis_output/summary_female_candidates.csv', index=False)
female_summary.to_latex('analysis_output/summary_female_candidates.tex', index=False)

# ============================================================================
# EPISODE-LEVEL REGRESSIONS
# ============================================================================

print("\n=== EPISODE-LEVEL REGRESSIONS ===")

controls = 'share_female_cand + n_cand'

ep1 = ols(f'female_winner ~ female_jur + {controls}', data=dfe).fit()
ep2 = ols(f'female_eliminated ~ female_jur + {controls}', data=dfe).fit()
ep3 = ols(f'first_probing_winner ~ female_jur + {controls}', data=dfe).fit()
ep4 = ols(f'first_probing_eliminated ~ female_jur + {controls}', data=dfe).fit()
ep5 = ols(f'last_probing_winner ~ female_jur + {controls}', data=dfe).fit()
ep6 = ols(f'last_probing_eliminated ~ female_jur + {controls}', data=dfe).fit()

ep_table = summary_col(
    [ep1, ep2, ep3, ep4, ep5, ep6],
    model_names=['Fem. Winner', 'Fem. Elim', 'First→Win', 'First→Elim', 'Last→Win', 'Last→Elim'],
    stars=True,
    float_format='%.3f',
    info_dict={'N': lambda x: f"{int(x.nobs)}", 'R²': lambda x: f"{x.rsquared:.3f}"}
)

print(ep_table)
with open('analysis_output/regressions_episode.tex', 'w') as f:
    f.write(ep_table.as_latex())

# ============================================================================
# CANDIDATE-LEVEL REGRESSIONS
# ============================================================================

print("\n=== CANDIDATE-LEVEL REGRESSIONS: GENDER ===")

controls_c = 'share_female_cand + n_cand'

# Gender interactions
c1 = ols(f'winner ~ female_cand * female_jur + {controls_c}', data=dfc).fit()
c2 = ols(f'eliminated ~ female_cand * female_jur + {controls_c}', data=dfc).fit()
c3 = ols(f'ranking ~ female_cand * female_jur + {controls_c}', data=dfc).fit()

cand_gender_table = summary_col(
    [c1, c2, c3],
    model_names=['Winner', 'Elim', 'Ranking'],
    stars=True,
    float_format='%.3f',
    info_dict={'N': lambda x: f"{int(x.nobs)}", 'R²': lambda x: f"{x.rsquared:.3f}"}
)

print(cand_gender_table)
with open('analysis_output/regressions_candidate_gender.tex', 'w') as f:
    f.write(cand_gender_table.as_latex())

# Probing order (FULL SAMPLE)
print("\n=== CANDIDATE-LEVEL REGRESSIONS: PROBING ORDER (Full Sample) ===")

c4 = ols(f'winner ~ order_probing + female_cand + female_jur + {controls_c}', data=dfc).fit()
c5 = ols(f'eliminated ~ order_probing + female_cand + female_jur + {controls_c}', data=dfc).fit()
c6 = ols(f'ranking ~ order_probing + female_cand + female_jur + {controls_c}', data=dfc).fit()

cand_probing_table = summary_col(
    [c4, c5, c6],
    model_names=['Winner', 'Elim', 'Ranking'],
    stars=True,
    float_format='%.3f',
    info_dict={'N': lambda x: f"{int(x.nobs)}", 'R²': lambda x: f"{x.rsquared:.3f}"}
)

print(cand_probing_table)
with open('analysis_output/regressions_candidate_probing_full.tex', 'w') as f:
    f.write(cand_probing_table.as_latex())

# Probing × juror interaction (FULL SAMPLE)
print("\n=== CANDIDATE-LEVEL REGRESSIONS: PROBING × JUROR (Full Sample) ===")

c7 = ols(f'winner ~ order_probing * female_jur + female_cand + {controls_c}', data=dfc).fit()
c8 = ols(f'eliminated ~ order_probing * female_jur + female_cand + {controls_c}', data=dfc).fit()
c9 = ols(f'ranking ~ order_probing * female_jur + female_cand + {controls_c}', data=dfc).fit()

cand_interaction_table = summary_col(
    [c7, c8, c9],
    model_names=['Winner', 'Elim', 'Ranking'],
    stars=True,
    float_format='%.3f',
    info_dict={'N': lambda x: f"{int(x.nobs)}", 'R²': lambda x: f"{x.rsquared:.3f}"}
)

print(cand_interaction_table)
with open('analysis_output/regressions_candidate_interaction_full.tex', 'w') as f:
    f.write(cand_interaction_table.as_latex())

# ============================================================================
# CANDIDATE-LEVEL REGRESSIONS (EXCLUDING FIRST PROBING)
# ============================================================================

print("\n=== CANDIDATE-LEVEL REGRESSIONS: PROBING ORDER (Excluding First) ===")

dfc_no_first = dfc[dfc['order_probing'] != 1].copy()
print(f"Sample size (excluding first probing): {len(dfc_no_first)} candidates\n")

c10 = ols(f'winner ~ order_probing + female_cand + female_jur + {controls_c}', data=dfc_no_first).fit()
c11 = ols(f'eliminated ~ order_probing + female_cand + female_jur + {controls_c}', data=dfc_no_first).fit()
c12 = ols(f'ranking ~ order_probing + female_cand + female_jur + {controls_c}', data=dfc_no_first).fit()

cand_probing_no_first_table = summary_col(
    [c10, c11, c12],
    model_names=['Winner', 'Elim', 'Ranking'],
    stars=True,
    float_format='%.3f',
    info_dict={'N': lambda x: f"{int(x.nobs)}", 'R²': lambda x: f"{x.rsquared:.3f}"}
)

print(cand_probing_no_first_table)
with open('analysis_output/regressions_candidate_probing_no_first.tex', 'w') as f:
    f.write(cand_probing_no_first_table.as_latex())

# Probing × juror interaction (EXCLUDING FIRST PROBING)
print("\n=== CANDIDATE-LEVEL REGRESSIONS: PROBING × JUROR (Excluding First) ===")

c13 = ols(f'winner ~ order_probing * female_jur + female_cand + {controls_c}', data=dfc_no_first).fit()
c14 = ols(f'eliminated ~ order_probing * female_jur + female_cand + {controls_c}', data=dfc_no_first).fit()
c15 = ols(f'ranking ~ order_probing * female_jur + female_cand + {controls_c}', data=dfc_no_first).fit()

cand_interaction_no_first_table = summary_col(
    [c13, c14, c15],
    model_names=['Winner', 'Elim', 'Ranking'],
    stars=True,
    float_format='%.3f',
    info_dict={'N': lambda x: f"{int(x.nobs)}", 'R²': lambda x: f"{x.rsquared:.3f}"}
)

print(cand_interaction_no_first_table)
with open('analysis_output/regressions_candidate_interaction_no_first.tex', 'w') as f:
    f.write(cand_interaction_no_first_table.as_latex())

print("\n=== ANALYSIS COMPLETE ===")
print("Output: analysis_output/")
print("  - summary_*.csv/tex")
print("  - regressions_episode.tex")
print("  - regressions_candidate_gender.tex")
print("  - regressions_candidate_probing_full.tex (with first probing)")
print("  - regressions_candidate_probing_no_first.tex (excluding first)")
print("  - regressions_candidate_interaction_full.tex (with first probing)")
print("  - regressions_candidate_interaction_no_first.tex (excluding first)")
print(f"\nFull sample: N={len(dfc)} | Excluding first probing: N={len(dfc_no_first)}")