import pandas as pd

HYPERTENSION_THRESHOLD = 170
HYPOTENSION_THRESHOLD = 95

def calculate_analysis(timeframes):
    analysis = {}
    current_timeframe = next((name for name in timeframes if name.startswith("Current")), None)
    prior_timeframe = next((name for name in timeframes if name.startswith("Prior")), None)

    for name, frame in timeframes.items():
        if frame.empty:
            analysis[name] = {
                'Avg Systolic BP (mmHg)': None,
                'Avg Diastolic BP (mmHg)': None,
                'Hypotensive Measurements¹': None,
                'Peak SBP² (mmHg)': None,
                'Peak DBP² (mmHg)': None,
                'Low SBP³ (mmHg)': None,
                'Low DBP³ (mmHg)': None,
                'SBP SD (mmHg)': None,
                'DBP SD (mmHg)': None,
                'SBP CV (%)': None,
                'DBP CV (%)': None
            }
            continue

        avg_systolic = round(frame['Value 1'].mean(), 2)
        avg_diastolic = round(frame['Value 2'].mean(), 2)
        hypotensive_count = len(frame[frame['Value 1'] <= HYPOTENSION_THRESHOLD + 5])
        peak_systolic = round(frame['Value 1'].nlargest(3).mean(), 2)  # Avg of 3 highest values
        peak_diastolic = round(frame['Value 2'].nlargest(3).mean(), 2)  # Avg of 3 highest values
        low_systolic = round(frame['Value 1'].min(), 2)
        low_diastolic = round(frame['Value 2'].min(), 2)
        systolic_sd = round(frame['Value 1'].std(), 2)
        diastolic_sd = round(frame['Value 2'].std(), 2)
        systolic_cv = round((systolic_sd / avg_systolic) * 100, 2) if avg_systolic else None
        diastolic_cv = round((diastolic_sd / avg_diastolic) * 100, 2) if avg_diastolic else None

        analysis[name] = {
            'Avg Systolic BP (mmHg)': avg_systolic,
            'Avg Diastolic BP (mmHg)': avg_diastolic,
            'Hypotensive Measurements¹': hypotensive_count,
            'Peak SBP² (mmHg)': peak_systolic,
            'Peak DBP² (mmHg)': peak_diastolic,
            'Low SBP³ (mmHg)': low_systolic,
            'Low DBP³ (mmHg)': low_diastolic,
            'SBP SD (mmHg)': systolic_sd,
            'DBP SD (mmHg)': diastolic_sd,
            'SBP CV (%)': systolic_cv,
            'DBP CV (%)': diastolic_cv
        }

    points = {
        'Avg Systolic BP (mmHg)': {'increase': -2, 'decrease': 2},
        'Avg Diastolic BP (mmHg)': {'increase': -2, 'decrease': 2},
        'SBP CV (%)': {'increase': -1, 'decrease': 1},
        'DBP CV (%)': {'increase': -1, 'decrease': 1},
        'SBP SD (mmHg)': {'increase': -1, 'decrease': 1},
        'DBP SD (mmHg)': {'increase': -1, 'decrease': 1},
        'Peak SBP² (mmHg)': {'above_threshold': -2, 'below_threshold': 2},
        'Peak DBP² (mmHg)': {'above_threshold': -2, 'below_threshold': 2}
    }

    thresholds = {
        'Avg Systolic BP (mmHg)': 2,
        'Avg Diastolic BP (mmHg)': 2,
        'SBP CV (%)': 1.1,
        'DBP CV (%)': 1.4,
        'SBP SD (mmHg)': 1.5,
        'DBP SD (mmHg)': 1.3,
        'Peak SBP² (mmHg)': 170,
        'Peak DBP² (mmHg)': 110
    }

    delta = 0

    if current_timeframe and prior_timeframe:
        for metric in analysis[current_timeframe]:
            current_value = analysis[current_timeframe][metric]
            prior_value = analysis[prior_timeframe].get(metric, "-")

            if current_value is not None and prior_value != "-" and isinstance(prior_value, (int, float)):
                change = current_value - prior_value
                abs_change = abs(change)

                # Handle average SBP and DBP
                if metric in ['Avg Systolic BP (mmHg)', 'Avg Diastolic BP (mmHg)']:
                    if abs_change >= thresholds[metric]:
                        if change > 0:  # Increase
                            delta += points[metric]['increase']
                            analysis[current_timeframe][metric] = f"{current_value} +"
                        elif change < 0:  # Decrease
                            delta += points[metric]['decrease']
                            analysis[current_timeframe][metric] = f"{current_value} -"

                # Handle SBP-CV, DBP-CV, SBP-SD, DBP-SD
                elif metric in ['SBP CV (%)', 'DBP CV (%)', 'SBP SD (mmHg)', 'DBP SD (mmHg)']:
                    if abs_change >= thresholds[metric]:
                        if change > 0:  # Increase
                            delta += points[metric]['increase']
                            analysis[current_timeframe][metric] = f"{current_value} +"
                        elif change < 0:  # Decrease
                            delta += points[metric]['decrease']
                            analysis[current_timeframe][metric] = f"{current_value} -"

                # Handle categorical change for Peak BP
                elif metric.startswith('Peak') and isinstance(current_value, (int, float)):
                    high_threshold = thresholds[metric]
                    if prior_value > high_threshold >= current_value:
                        delta += points[metric]['above_threshold']
                        analysis[current_timeframe][metric] = f"{current_value} +"
                    elif prior_value < high_threshold <= current_value:
                        delta += points[metric]['below_threshold']
                        analysis[current_timeframe][metric] = f"{current_value} -"

                # Handle no change
                # else:
                #     analysis[current_timeframe][metric] = f"{current_value} ="

    # Add the total delta as a new key for the extra cell
    progress = "Improving" if delta > 0 else "Worsening" if delta < 0 else "Same"
    analysis[current_timeframe]['Progress (pts)'] = f"{progress} ({delta})"

    # Ensure the Progress row has "-" in baseline and prior columns
    analysis[prior_timeframe].setdefault('Progress (pts)', '-')
    analysis[next(k for k in analysis if "Baseline" in k)]['Progress (pts)'] = '-'

    df = pd.DataFrame.from_dict(analysis, orient='index').T

    def calculate_overall(column):
        """
        Calculate the overall rating for a timeframe based on individual metrics.
        Priority: Poor > Okay > Good
        """
        # Initialize the default rating as 'Good'
        overall_rating = 'Good'

        # Iterate through each metric in the column
        for metric, value in column.items():
            if isinstance(value, str):
                # Remove trend arrows (↑/↓) and convert to numeric
                value = pd.to_numeric(value.replace('+', '').replace('-', '').strip(), errors='coerce')

            if metric == 'Avg Systolic BP (mmHg)' and value is not None:
                if value >= 140:
                    return 'Poor'  # Immediate return for highest priority
                elif 130 <= value < 140:
                    overall_rating = 'Okay'

            elif metric == 'Avg Diastolic BP (mmHg)' and value is not None:
                if value >= 90:
                    return 'Poor'
                elif 80 <= value < 90:
                    overall_rating = 'Okay'

            elif metric == 'SBP SD (mmHg)' and value is not None:
                if value >= 15:
                    return 'Poor'
                elif 7.5 <= value < 15:
                    overall_rating = 'Okay'

            elif metric == 'DBP SD (mmHg)' and value is not None:
                if value >= 11.5:
                    return 'Poor'
                elif 5 <= value < 11.5:
                    overall_rating = 'Okay'

            elif metric == 'SBP CV (%)' and value is not None:
                if value >= 11:
                    return 'Poor'
                elif 5.5 <= value < 11:
                    overall_rating = 'Okay'

            elif metric == 'DBP CV (%)' and value is not None:
                if value >= 13:
                    return 'Poor'
                elif 6 <= value < 13:
                    overall_rating = 'Okay'

            elif metric == 'Peak SBP¹ (mmHg)' and value is not None:
                if value >= 170:
                    return 'Poor'

            elif metric == 'Peak DBP¹ (mmHg)' and value is not None:
                if value >= 110:
                    return 'Poor'

        # Return the overall rating ('Okay' or 'Good')
        return overall_rating

    df.loc['Overall'] = df.apply(calculate_overall, axis=0)

    def calculate_change(row, baseline_col, current_col):
        baseline_val = pd.to_numeric(str(row[baseline_col]).replace('+', '').replace('-', '').strip(), errors='coerce')
        current_val = pd.to_numeric(str(row[current_col]).replace('+', '').replace('-', '').strip(), errors='coerce')

        if pd.notna(baseline_val) and pd.notna(current_val):
            numeric_change = round(current_val - baseline_val, 2)
            return numeric_change
        return ''

    # Add Since Inception column comparing Baseline to Current
    baseline_col = next((col for col in df.columns if 'Baseline' in col), None)
    current_col = next((col for col in df.columns if 'Current' in col), None)
    if baseline_col and current_col:
        df['Since Inception'] = df.apply(lambda row: calculate_change(row, baseline_col, current_col), axis=1)


    return df
