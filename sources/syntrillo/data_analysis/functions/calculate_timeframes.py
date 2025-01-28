import pandas as pd

def calculate_timeframes(df):
    latest_date = df['Time stamp'].max()
    current_start = latest_date - pd.Timedelta(weeks=2) + pd.Timedelta(days=1)

    baseline_start = df['Time stamp'].min()
    baseline_end = df['Time stamp'].min() + pd.Timedelta(weeks=1, days=6)

    prior_end = current_start - pd.Timedelta(days=1)
    prior_start = prior_end - pd.Timedelta(weeks=1, days=6)

    timeframes = {
        f"Baseline ({baseline_start.strftime('%m/%d/%y')}-{baseline_end.strftime('%m/%d/%y')})": df[(df['Time stamp'] >= baseline_start) & (df['Time stamp'] < baseline_end)],
        f"Prior ({prior_start.strftime('%m/%d/%y')}-{prior_end.strftime('%m/%d/%y')})": df[(df['Time stamp'] >= prior_start) & (df['Time stamp'] < prior_end)],
        # f"Current ({prior_end.strftime('%m/%d/%y')}-{latest_date.strftime('%m/%d/%y')})": df[df['Time stamp'] >= prior_end]
        f"Current ({current_start.strftime('%m/%d/%y')}-{latest_date.strftime('%m/%d/%y')})": df[df['Time stamp'] >= current_start]
    }
    return timeframes
