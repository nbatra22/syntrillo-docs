import pandas as pd

# Read a single CSV file
def read_csv_file(filepath):
    return pd.read_csv(filepath)

def preprocess_data(df):
    df['Time stamp'] = pd.to_datetime(df['Time stamp'], format='%m/%d/%y, %I:%M:%S %p')
    df = df[df['Metric'] == 'blood_pressure']  # Only consider blood_pressure metrics
    df = df.dropna(subset=['Value 1', 'Value 2'])  # Ensure both values are populated
    return df.sort_values(by='Time stamp')
