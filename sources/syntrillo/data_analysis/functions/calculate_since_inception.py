import pandas as pd

def calculate_since_inception(counts_dict, analysis_table):
    def calculate_change(row, baseline_col, current_col):
        baseline_val = pd.to_numeric(str(row[baseline_col]).replace('+', '').replace('-', '').strip(), errors='coerce')
        current_val = pd.to_numeric(str(row[current_col]).replace('+', '').replace('-', '').strip(), errors='coerce')

        if pd.notna(baseline_val) and pd.notna(current_val):
            numeric_change = round(current_val - baseline_val, 2)
            return numeric_change
        return ''

    # Identify the Baseline and Current columns dynamically
    baseline_col = next((col for col in analysis_table.columns if 'Baseline' in col), None)
    current_col = next((col for col in analysis_table.columns if 'Current' in col), None)

    if baseline_col and current_col:
        analysis_table['Since Inception (Unit Change)'] = analysis_table.apply(lambda row: calculate_change(row, baseline_col, current_col), axis=1)

    # Add the "Total" column from counts_dict, matching index labels
    analysis_table['Since Inception (Total)'] = analysis_table.index.map(lambda idx: counts_dict.get(idx, ''))

    return analysis_table
