# data_cleaning.py
"""
Data cleaning and variable creation for Die Küchenschlacht dataset
Run after: python main.py all
Input: output/kuechenschlacht_data.csv
Output: cleaned_candidate_data.csv, episode_level_data.csv
"""

import pandas as pd
import numpy as np

# ============================================================================
# LOAD & PREPARE
# ============================================================================

df = pd.read_csv('output/kuechenschlacht_data.csv')
df['Date of Show'] = pd.to_datetime(df['Date of Show'])

# Date variables
df['day_of_week'] = df['Date of Show'].dt.dayofweek
df['day_of_week_name'] = df['Date of Show'].dt.day_name()
df['week_of_year'] = df['Date of Show'].dt.isocalendar().week
df['year_week'] = df['Date of Show'].dt.strftime('%Y-%W')

# ============================================================================
# MODERATOR IMPUTATION (forward/backward fill within week)
# ============================================================================

df['Moderator Name'] = df.groupby('year_week')['Moderator Name'].transform(
    lambda x: x.fillna(method='ffill').fillna(method='bfill')
)
df['Moderator Gender'] = df.groupby('year_week')['Moderator Gender'].transform(
    lambda x: x.fillna(method='ffill').fillna(method='bfill')
)

print("✓ Moderator data imputed")

# ============================================================================
# CHECK & DROP DUPLICATE RANKINGS/ORDERS
# ============================================================================

print("\n=== CHECKING FOR DUPLICATES ===")

# Check Order of Probing
order_check = df.groupby(['Season', 'Episode'])['Order of Probing'].agg([
    ('distinct', 'nunique'),
    ('total', 'count')
]).reset_index()
order_check['has_duplicates'] = order_check['distinct'] < order_check['total']

# Check Ranking
ranking_check = df.groupby(['Season', 'Episode'])['Ranking number'].agg([
    ('distinct', 'nunique'),
    ('total', 'count')
]).reset_index()
ranking_check['has_duplicates'] = ranking_check['distinct'] < ranking_check['total']

# Find problematic episodes
problematic_order = order_check[order_check['has_duplicates']]
problematic_ranking = ranking_check[ranking_check['has_duplicates']]

episodes_to_drop = pd.concat([
    problematic_order[['Season', 'Episode']],
    problematic_ranking[['Season', 'Episode']]
]).drop_duplicates()

# Drop episodes with duplicates
if len(episodes_to_drop) > 0:
    print(f"⚠ Dropping {len(episodes_to_drop)} episodes with duplicate values")
    df = df.merge(
        episodes_to_drop.assign(drop=True),
        on=['Season', 'Episode'],
        how='left'
    )
    df = df[df['drop'].isna()].drop('drop', axis=1)
else:
    print("✓ No duplicates found")

print(f"✓ Final dataset: {len(df)} rows, {df.groupby(['Season', 'Episode']).ngroups} episodes")

# ============================================================================
# CREATE VARIABLES
# ============================================================================

# Max ranking per episode (for eliminated variable)
df['max_ranking'] = df.groupby(['Season', 'Episode'])['Ranking number'].transform('max')

# Binary outcomes
df['winner'] = (df['Ranking number'] == 1).astype(int)
df['eliminated'] = (df['Ranking number'] == df['max_ranking']).astype(int)
df['female_cand'] = (df['Candidate Gender'].str.lower() == 'w').astype(int)
df['female_jur'] = (df['Juror Gender'].str.lower() == 'w').astype(int)

print(f"\n✓ Variables created: {df['winner'].sum()} winners, {df['eliminated'].sum()} eliminated")

# Save candidate-level data
df.to_csv('analysis_output/cleaned_candidate_data.csv', index=False)
print("✓ Saved: cleaned_candidate_data.csv")

# ============================================================================
# EPISODE-LEVEL AGGREGATION
# ============================================================================

print("\n=== CREATING EPISODE-LEVEL DATA ===")

# Basic aggregation
episode_df = df.groupby(['Season', 'Episode']).agg({
    'Date of Show': 'first',
    'day_of_week': 'first',
    'day_of_week_name': 'first',
    'week_of_year': 'first',
    'Candidate Name': 'count',
    'female_cand': 'sum',
    'female_jur': 'first',
    'Moderator Gender': 'first'
}).reset_index()

episode_df.rename(columns={
    'Season': 'year',
    'Candidate Name': 'n_candidates',
    'female_cand': 'n_female_candidates',
    'day_of_week_name': 'day_of_week'
}, inplace=True)

# Share and gender variables
episode_df['share_female_candidates'] = episode_df['n_female_candidates'] / episode_df['n_candidates']
episode_df['female_moderator'] = (episode_df['Moderator Gender'].str.lower() == 'w').astype(int)
episode_df = episode_df.drop('Moderator Gender', axis=1)

# Winner/eliminated (merge)
female_winner = df[df['winner'] == 1].groupby(['Season', 'Episode'])['female_cand'].first().reset_index()
female_winner.rename(columns={'Season': 'year', 'female_cand': 'female_winner'}, inplace=True)

female_eliminated = df[df['eliminated'] == 1].groupby(['Season', 'Episode'])['female_cand'].first().reset_index()
female_eliminated.rename(columns={'Season': 'year', 'female_cand': 'female_eliminated'}, inplace=True)

episode_df = episode_df.merge(female_winner, on=['year', 'Episode'], how='left')
episode_df = episode_df.merge(female_eliminated, on=['year', 'Episode'], how='left')

# Average rankings for female candidates
female_avg = df[df['female_cand'] == 1].groupby(['Season', 'Episode']).agg({
    'Ranking number': 'mean',
    'Order of Probing': 'mean'
}).reset_index()
female_avg.rename(columns={
    'Season': 'year',
    'Ranking number': 'avg_female_ranking',
    'Order of Probing': 'avg_female_probing'
}, inplace=True)

episode_df = episode_df.merge(female_avg, on=['year', 'Episode'], how='left')

# Probing position variables
max_probing = df.groupby(['Season', 'Episode'])['Order of Probing'].max().reset_index()
max_probing.rename(columns={'Order of Probing': 'max_probing'}, inplace=True)
df_with_max = df.merge(max_probing, on=['Season', 'Episode'])

# First/last probing outcomes
first_probing = df[df['Order of Probing'] == 1].groupby(['Season', 'Episode']).agg({
    'winner': 'first',
    'eliminated': 'first'
}).reset_index()
first_probing.rename(columns={
    'Season': 'year',
    'winner': 'first_probing_winner',
    'eliminated': 'first_probing_eliminated'
}, inplace=True)

last_probing = df_with_max[
    df_with_max['Order of Probing'] == df_with_max['max_probing']
].groupby(['Season', 'Episode']).agg({
    'winner': 'first',
    'eliminated': 'first'
}).reset_index()
last_probing.rename(columns={
    'Season': 'year',
    'winner': 'last_probing_winner',
    'eliminated': 'last_probing_eliminated'
}, inplace=True)

episode_df = episode_df.merge(first_probing, on=['year', 'Episode'], how='left')
episode_df = episode_df.merge(last_probing, on=['year', 'Episode'], how='left')

# Fill NaN with 0 for binary variables
binary_cols = [
    'female_winner', 'female_eliminated', 'female_moderator',
    'first_probing_winner', 'first_probing_eliminated',
    'last_probing_winner', 'last_probing_eliminated'
]
for col in binary_cols:
    if col in episode_df.columns:
        episode_df[col] = episode_df[col].fillna(0).astype(int)

# Save
episode_df.to_csv('analysis_output/episode_level_data.csv', index=False)
print(f"✓ Saved: episode_level_data.csv ({len(episode_df)} episodes)")

print("\n=== DATA CLEANING COMPLETE ===")