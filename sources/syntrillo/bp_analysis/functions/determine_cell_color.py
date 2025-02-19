import pandas as pd

def determine_cell_color(metric, value):
    if metric and value is not None:
        color = 'white'
        if isinstance(value, str):
            # Remove trend arrows and convert to numeric
            value = pd.to_numeric(value.replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')

        if metric == 'Avg SBP (mmHg)' and value is not None:
            if value < 130:
                color = 'lightgreen'
            elif 130 <= value <= 139:
                color = 'yellow'
            else:
                color = 'red'
        elif metric == 'Avg DBP (mmHg)' and value is not None:
            if value < 80:
                color = 'lightgreen'
            elif 80 <= value <= 89:
                color = 'yellow'
            else:
                color = 'red'
        elif metric == 'SBP SD (mmHg)' and value is not None:
            if value < 7.5:
                color = 'lightgreen'
            elif value < 15:
                color = 'yellow'
            else:
                color = 'red'
        elif metric == 'DBP SD (mmHg)' and value is not None:
            if value < 5:
                color = 'lightgreen'
            elif value < 11.5:
                color = 'yellow'
            else:
                color = 'red'
        elif metric == 'SBP CV (%)' and value is not None:
            if value < 5.5:
                color = 'lightgreen'
            elif value < 11:
                color = 'yellow'
            else:
                color = 'red'
        elif metric == 'DBP CV (%)' and value is not None:
            if value < 6:
                color = 'lightgreen'
            elif value < 13:
                color = 'yellow'
            else:
                color = 'red'
        elif metric == 'Peak SBP² (mmHg)' and value is not None:
            if value < 170:
                color = 'lightgreen'
            else:
                color = 'red'
        elif metric == 'Peak DBP² (mmHg)' and value is not None:
            if value < 110:
                color = 'lightgreen'
            else:
                color = 'red'

        return color

    return 'white'
