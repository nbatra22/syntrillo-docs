

def calculate_total_counts(df):
    counts = {
        'Avg Systolic BP (mmHg)': round(df['Value 1'].mean(), 2),
        'Avg Diastolic BP (mmHg)': round(df['Value 2'].mean(), 2),
        'Peak SBP² (mmHg)': round(df['Value 1'].nlargest(3).mean(), 2),
        'Peak DBP² (mmHg)': round(df['Value 2'].nlargest(3).mean(), 2),
        'Low SBP³ (mmHg)': round(df['Value 1'].min(), 2),
        'Low DBP³ (mmHg)': round(df['Value 2'].min(), 2),
        'SBP SD (mmHg)': round(df['Value 1'].std(), 2),
        'DBP SD (mmHg)': round(df['Value 2'].std(), 2),
        'SBP CV (%)': round((df['Value 1'].std() / df['Value 1'].mean()) * 100, 2) if df['Value 1'].mean() != 0 else None,
        'DBP CV (%)': round((df['Value 2'].std() / df['Value 2'].mean()) * 100, 2) if df['Value 2'].mean() != 0 else None,
        'SBP Count (>= 160)': len(df[df['Value 1'] >= 160]),
        'SBP Count (>= 165)': len(df[df['Value 1'] >= 165]),
        'SBP Count (>= 170)': len(df[df['Value 1'] >= 170]),
        'SBP Count (>= 175)': len(df[df['Value 1'] >= 175]),
        'SBP Count (<=80)': len(df[df['Value 1'] <= 80]),
        'SBP Count (<=85)': len(df[df['Value 1'] <= 85]),
        'SBP Count (<=90)': len(df[df['Value 1'] <= 90]),
        'SBP Count (<=95)': len(df[df['Value 1'] <= 95]),
        # 'Hypotensive Count³': len(df[df['Value 1'] <= 100]),
    }

    return counts
