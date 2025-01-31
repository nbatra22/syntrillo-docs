import pandas as pd

HYPERTENSION_SBP_THRESHOLD = 170
HYPERTENSION_DBP_THRESHOLD = 110
HYPOTENSION_SBP_THRESHOLD = 95

def calculate_analysis(timeframes):
    analysis = {}
    current_timeframe = next((name for name in timeframes if name.startswith("Current")), None)
    prior_timeframe = next((name for name in timeframes if name.startswith("Prior")), None)
    baseline_timeframe = next((name for name in timeframes if name.startswith("Baseline")), None)

    for name, frame in timeframes.items():
        if frame.empty:
            analysis[name] = {
                'Avg Systolic BP (mmHg)': None,
                'Avg Diastolic BP (mmHg)': None,
                'Peak SBP² (mmHg)': None,
                'Peak DBP² (mmHg)': None,
                'Low SBP³ (mmHg)': None,
                'Low DBP³ (mmHg)': None,
                'SBP SD (mmHg)': None,
                'DBP SD (mmHg)': None,
                'SBP CV (%)': None,
                'DBP CV (%)': None,
                'SBP Count (>= 160)': None,
                'SBP Count (>= 165)': None,
                'SBP Count (>= 170)': None,
                'SBP Count (>= 175)': None,
                'SBP Count (<=80)': None,
                'SBP Count (<=85)': None,
                'SBP Count (<=90)': None,
                'SBP Count (<=95)': None,
                # 'Hypotensive Count³': None,
            }
            continue

        avg_systolic = round(frame['Value 1'].mean(), 2)
        avg_diastolic = round(frame['Value 2'].mean(), 2)
        peak_systolic = round(frame['Value 1'].nlargest(3).mean(), 2)  # Avg of 3 highest values
        peak_diastolic = round(frame['Value 2'].nlargest(3).mean(), 2)  # Avg of 3 highest values
        low_systolic = round(frame['Value 1'].min(), 2)
        low_diastolic = round(frame['Value 2'].min(), 2)
        systolic_sd = round(frame['Value 1'].std(), 2)
        diastolic_sd = round(frame['Value 2'].std(), 2)
        systolic_cv = round((systolic_sd / avg_systolic) * 100, 2) if avg_systolic else None
        diastolic_cv = round((diastolic_sd / avg_diastolic) * 100, 2) if avg_diastolic else None
        sbp_count_160 = len(frame[frame['Value 1'] >= 160])
        sbp_count_165 = len(frame[frame['Value 1'] >= 165])
        sbp_count_170 = len(frame[frame['Value 1'] >= 170])
        sbp_count_175 = len(frame[frame['Value 1'] >= 175])
        sbp_count_80 = len(frame[frame['Value 1'] <= 80])
        sbp_count_85 = len(frame[frame['Value 1'] <= 85])
        sbp_count_90 = len(frame[frame['Value 1'] <= 90])
        sbp_count_95 = len(frame[frame['Value 1'] <= 95])
        hypertensive_dbp_count = len(frame[frame['Value 2'] >= HYPERTENSION_DBP_THRESHOLD])
        hypotensive_count = len(frame[frame['Value 1'] <= HYPOTENSION_SBP_THRESHOLD + 5])


        analysis[name] = {
            'Avg Systolic BP (mmHg)': avg_systolic,
            'Avg Diastolic BP (mmHg)': avg_diastolic,
            'Peak SBP² (mmHg)': peak_systolic,
            'Peak DBP² (mmHg)': peak_diastolic,
            'Low SBP³ (mmHg)': low_systolic,
            'Low DBP³ (mmHg)': low_diastolic,
            'SBP SD (mmHg)': systolic_sd,
            'DBP SD (mmHg)': diastolic_sd,
            'SBP CV (%)': systolic_cv,
            'DBP CV (%)': diastolic_cv,
            'SBP Count (>= 160)': sbp_count_160,
            'SBP Count (>= 165)': sbp_count_165,
            'SBP Count (>= 170)': sbp_count_170,
            'SBP Count (>= 175)': sbp_count_175,
            'SBP Count (<=80)': sbp_count_80,
            'SBP Count (<=85)': sbp_count_85,
            'SBP Count (<=90)': sbp_count_90,
            'SBP Count (<=95)': sbp_count_95,
            # 'Hypotensive Count³': hypotensive_count,
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
    baseline_delta = 0

    if current_timeframe and prior_timeframe and baseline_timeframe:
        for metric in analysis[current_timeframe]:
            current_value = analysis[current_timeframe][metric]
            prior_value = analysis[prior_timeframe].get(metric, "-")
            baseline_value = analysis[baseline_timeframe].get(metric, "-")

            if current_value is not None and prior_value != "-" and baseline_value != "-" and isinstance(prior_value, (int, float)) and isinstance(baseline_value, (int, float)):
                change = current_value - prior_value
                percent_change = (
                    (current_value - prior_value) / prior_value * 100
                    if prior_value != 0
                    else 0
                )
                abs_change = abs(change)
                abs_percent_change = abs(percent_change)

                baseline_change = current_value - baseline_value
                baseline_percent_change = (
                    (current_value - baseline_value) / baseline_value * 100
                    if baseline_value != 0
                    else 0
                )
                baseline_abs_change = abs(baseline_change)
                baseline_abs_percent_change = abs(baseline_percent_change)

                default_progress = "=/="

                # Handle average SBP and DBP
                if metric in ['Avg Systolic BP (mmHg)', 'Avg Diastolic BP (mmHg)']:

                    if current_value >= thresholds[metric]:
                        curr_progress = "="  # Default for current change
                        base_progress = "="  # Default for baseline change

                        if change > 0:  # Increase in current change
                            delta += points[metric]['increase']
                            curr_progress = "-"  # Indicates a decrease is needed
                        elif change < 0:  # Decrease in current change
                            delta += points[metric]['decrease']
                            curr_progress = "+"  # Indicates an increase is needed

                        if baseline_change > 0:  # Increase in baseline change
                            baseline_delta += points[metric]['increase']
                            base_progress = "-"  # Indicates a decrease is needed
                        elif baseline_change < 0:  # Decrease in baseline change
                            baseline_delta += points[metric]['decrease']
                            base_progress = "+"  # Indicates an increase is needed

                    # Update progress format as "(current change sign) / (baseline change sign)"
                    progress = f"{curr_progress}/{base_progress}"

                    # Keep the last f-string with the updated progress
                    analysis[current_timeframe][metric] = f"{current_value} {progress}"

                # Handle SBP-SD and DBP-SD
                elif metric in ['SBP SD (mmHg)', 'DBP SD (mmHg)']:
                    curr_progress = "="  # Default for current change
                    base_progress = "="  # Default for baseline change
                    if abs_change >= thresholds[metric]:
                        if change > 0:  # Increase in current change
                            delta += points[metric]['increase']
                            curr_progress = "-"  # Indicates a decrease is needed
                        elif change < 0:  # Decrease in current change
                            delta += points[metric]['decrease']
                            curr_progress = "+"  # Indicates an increase is needed
                    if baseline_abs_change >= thresholds[metric]:
                        if baseline_change > 0:  # Increase in baseline change
                            baseline_delta += points[metric]['increase']
                            base_progress = "-"  # Indicates a decrease is needed
                        elif baseline_change < 0:  # Decrease in baseline change
                            baseline_delta += points[metric]['decrease']
                            base_progress = "+"  # Indicates an increase is needed

                    progress = f"{curr_progress}/{base_progress}"
                    analysis[current_timeframe][metric] = f"{current_value} {progress}"

                # Handle SBP-CV and DBP-CV
                elif metric in ['SBP CV (%)', 'DBP CV (%)']:
                    if abs_percent_change >= thresholds[metric]:
                        curr_progress = "="  # Default for current change
                        base_progress = "="  # Default for baseline change

                        if percent_change > 0:  # Increase in current change
                            delta += points[metric]['increase']
                            curr_progress = "-"  # Indicates a decrease is needed
                        elif percent_change < 0:  # Decrease in current change
                            delta += points[metric]['decrease']
                            curr_progress = "+"  # Indicates an increase is needed

                    if baseline_abs_percent_change >= thresholds[metric]:
                        if baseline_percent_change > 0:  # Increase in baseline change
                            baseline_delta += points[metric]['increase']
                            base_progress = "-"  # Indicates a decrease is needed
                        elif baseline_percent_change < 0:  # Decrease in baseline change
                            baseline_delta += points[metric]['decrease']
                            base_progress = "+"  # Indicates an increase is needed

                    progress = f"{curr_progress}/{base_progress}"
                    analysis[current_timeframe][metric] = f"{current_value} {progress}"

                # Handle categorical change for Peak BP
                elif metric.startswith('Peak') and isinstance(current_value, (int, float)):
                    high_threshold = thresholds[metric]
                    curr_progress = "="  # Default for current change
                    base_progress = "="  # Default for baseline change

                    # Current change logic
                    if prior_value < high_threshold < current_value:  # Crossed above threshold
                        delta += points[metric]['above_threshold']
                        curr_progress = "-"  # Indicates a decrease is needed
                    elif prior_value > high_threshold >= current_value:  # Crossed below threshold
                        delta += points[metric]['below_threshold']
                        curr_progress = "+"  # Indicates an increase is needed

                    # Baseline change logic
                    if baseline_value < high_threshold < current_value:  # Crossed above threshold
                        baseline_delta += points[metric]['above_threshold']
                        base_progress = "-"  # Indicates a decrease is needed
                    elif baseline_value > high_threshold >= current_value:  # Crossed below threshold
                        baseline_delta += points[metric]['below_threshold']
                        base_progress = "+"  # Indicates an increase is needed

                    progress = f"{curr_progress}/{base_progress}"
                    analysis[current_timeframe][metric] = f"{current_value} {progress}"


                # Handle no change
                # else:
                #     analysis[current_timeframe][metric] = f"{current_value} ="

    # Add the total delta as a new key for the extra cell
    progress = "Improving" if delta > 0 else "Worsening" if delta < 0 else "Same"
    baseline_progress = "Improving" if baseline_delta > 0 else "Worsening" if baseline_delta < 0 else "Same"
    analysis[current_timeframe]['Progress (pts)'] = f"{progress} ({delta})"
    analysis[current_timeframe]['Baseline Progress (pts)'] = f"{baseline_progress} ({baseline_delta})"

    # Ensure the Progress row has "-" in baseline and prior columns
    analysis[prior_timeframe].setdefault('Progress (pts)', '-')
    analysis[next(k for k in analysis if "Baseline" in k)]['Progress (pts)'] = '-'
    analysis[prior_timeframe].setdefault('Baseline Progress (pts)', '-')
    analysis[next(k for k in analysis if "Baseline" in k)]['Baseline Progress (pts)'] = '-'

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

            elif metric == 'Peak SBP² (mmHg)' and value is not None:
                if value >= 170:
                    return 'Poor'

            elif metric == 'Peak DBP² (mmHg)' and value is not None:
                if value >= 110:
                    return 'Poor'

        # Return the overall rating ('Okay' or 'Good')
        return overall_rating

    df.loc['Overall'] = df.apply(calculate_overall, axis=0)

    return df
