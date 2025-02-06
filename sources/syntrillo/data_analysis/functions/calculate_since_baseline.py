import pandas as pd

def calculate_since_baseline(counts_dict, analysis_table):
    def calculate_unit_change(row, baseline_col, current_col):
        baseline_val = pd.to_numeric(str(row[baseline_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')
        current_val = pd.to_numeric(str(row[current_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')

        if pd.notna(baseline_val) and pd.notna(current_val):
            numeric_change = round(current_val - baseline_val, 2)
            return numeric_change
        return ''

    def calculate_percent_change(row, baseline_col, current_col):
        baseline_val = pd.to_numeric(str(row[baseline_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')
        current_val = pd.to_numeric(str(row[current_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')

        if pd.notna(baseline_val) and pd.notna(current_val):
            if baseline_val == 0:
                return 100.0 if current_val > 0 else (0.0 if current_val == 0 else -100.0)  # Handles 0 baseline cases
            percent_change = round((current_val - baseline_val) / abs(baseline_val) * 100, 1)
            return percent_change
        return ''


    # Identify the Baseline and Current columns dynamically
    baseline_col = next((col for col in analysis_table.columns if 'Baseline' in col), None)
    current_col = next((col for col in analysis_table.columns if 'Current' in col), None)

    if baseline_col and current_col:
        # Add the "Δ Unit" column from analysis_table, matching index labels
        analysis_table['Since Baseline (Δ Unit)'] = analysis_table.apply(lambda row: calculate_unit_change(row, baseline_col, current_col), axis=1)
        # Add the "Δ Percent" column from analysis_table, matching index labels
        analysis_table['Since Baseline (Δ Percent)'] = analysis_table.apply(lambda row: f"{calculate_percent_change(row, baseline_col, current_col)}%", axis=1)

    # Add the "Total" column from counts_dict, matching index labels
    analysis_table['Since Baseline (Total)'] = analysis_table.index.map(lambda idx: counts_dict.get(idx, ''))

    return analysis_table
