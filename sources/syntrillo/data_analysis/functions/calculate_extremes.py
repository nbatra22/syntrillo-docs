# Define constants for thresholds
BLOOD_PRESSURE_LOW = 90
BLOOD_PRESSURE_HIGH_VALUE1 = 170
BLOOD_PRESSURE_HIGH_VALUE2 = 110

def calculate_extremes(df):
    extremes = df[(df['Value 1'] < BLOOD_PRESSURE_LOW) |
                  (df['Value 1'] > BLOOD_PRESSURE_HIGH_VALUE1) |
                  (df['Value 2'] > BLOOD_PRESSURE_HIGH_VALUE2)]
    return extremes[['Time stamp', 'Value 1', 'Value 2']]
