
from json import dumps as json_dumps

class ColorCodingBloodPressureCategories:
    """
    A class to handle color coding categories for blood pressure values.

    Attributes:
        COLOR_CODES (list): List of dictionaries with color code configurations.
        color_code (dict): Currently selected color code.
        systolic (float): Systolic blood pressure value.
        diastolic (float): Diastolic blood pressure value.

    Methods:
        __init__(self, systolic: float, diastolic: float, color_code_name: str):
            Initializes an instance of the class with specified blood pressure values and color code.

        get_thresholds(self) -> dict:
            Retrieves the blood pressure thresholds for the current color code.

        get_systolic_category(self) -> int:
            Determines the category of the systolic blood pressure.

        get_systolic_entry(self) -> dict:
            Provides details about the systolic blood pressure including value, category, normal status, color, and label.

        get_diastolic_category(self) -> int:
            Determines the category of the diastolic blood pressure.

        get_diastolic_entry(self) -> dict:
            Provides details about the diastolic blood pressure including value, category, normal status, color, and label.

        get_combination_category(self) -> int:
            Determines the category of the combination of systolic and diastolic blood pressure.

        get_combination_entry(self, html_highlight: str, round_values: int, html_separator: str) -> dict:
            Provides details about the combination of systolic and diastolic blood pressure including category, normal status, color, label, and HTML representation.

        get_references(self) -> list:
            Retrieves references for the blood pressure categories.

        get_entries(self) -> dict:
            Provides entries for the systolic, diastolic, and combined blood pressure values.
    """

    # Predefined color code configurations
    COLOR_CODES = [{
                        'name': 'default',
                        'systolic': {
                            'thresholds': (120, 140),
                            'colors': ('green', 'orange', 'red'),
                            'labels': ('Within range', 'Close to being out of range', 'Out of range'),
                            'normal' : ( True, False, False),
                            },
                        'diastolic': {
                            'thresholds': (80, 90),
                            'colors': ('green', 'orange', 'red'),
                            'labels': ('Within range', 'Close to being out of range', 'Out of range'),
                            'normal' : ( True, False, False),
                            },
                        'combinations': {
                            'logic': ('and', 'or', 'or'),
                            'colors': ('green', 'orange', 'red'),
                            'labels': ('Within range', 'Close to being out of range', 'Out of range'),
                            'normal' : ( True, False, False),
                            },
                        'references': ['internal']
                    },
                   {
                        'name': 'american_heart_association',
                        'systolic': {
                            'thresholds': (120, 130, 140, 180),
                            'colors': ('green', 'yellow', 'orange', 'red', 'dark_red'),
                            'labels': ('Normal', 'Elevated', 'High blood pressure stage 1', 'High blood pressure stage 2', 'Hypertensive crisis'),
                            'normal' : ( True, False, False, False, False),
                            },
                        'diastolic': {
                            'thresholds': ( 80, 80, 90, 120),
                            'colors': ( 'green', 'green', 'orange', 'red', 'dark_red'),
                            'labels': ( 'Normal', 'Normal', 'High blood pressure stage 1', 'High blood pressure stage 2', 'Hypertensive crisis'),
                            'normal' : ( True, True, False, False, False),
                            },
                        'combinations': {
                            'logic': ('and-max', 'and-max', 'or', 'or', 'or'),
                            'colors': ('green', 'yellow', 'orange', 'red', 'dark_red'),
                            'labels': ('Normal', 'Elevated', 'High blood pressure stage 1', 'High blood pressure stage 2', 'Hypertensive crisis'),
                            'normal' : ( True, False, False, False, False),
                            },
                        'references': [
                            'https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings',
                            'https://www.mayoclinic.org/diseases-conditions/high-blood-pressure/in-depth/blood-pressure/art-20050982'
                            ],
                   },
                   ]

    # current color code selected
    color_code = None

    def __init__(
        self,
        systolic: float = None,
        diastolic: float = None,
        color_code_name: str = 'default',
    ):
        """
        Initializes an instance with specified systolic and diastolic blood pressure values and a color code name.

        Args:
            systolic (float): Systolic blood pressure value.
            diastolic (float): Diastolic blood pressure value.
            color_code_name (str): The name of the color code to use. Defaults to 'default'.
        """
        self.systolic = systolic
        self.diastolic = diastolic

        # Select the appropriate color code based on the provided name
        for color_code in self.COLOR_CODES:
            if color_code['name'] == color_code_name:
                self.color_code = color_code
                break

        if self.color_code is None:
            raise ValueError(f'Color code {color_code_name} not found')

    def get_thresholds(self):
        """
        Retrieves the blood pressure thresholds for the current color code.

        Returns:
            dict: A dictionary with systolic and diastolic thresholds.
        """
        return {
            'systolic': self.color_code['systolic']['thresholds'],
            'diastolic': self.color_code['diastolic']['thresholds'],
        }

    def get_systolic_category(self):
        """
        Determines the category of the systolic blood pressure.

        Returns:
            int: The category index of the systolic blood pressure.
        """
        if self.systolic is None:
            return None

        thresholds = self.color_code['systolic']['thresholds']
        for i, threshold in enumerate(thresholds):
            if self.systolic < threshold:
                return i
        return len(thresholds)

    def get_systolic_entry(self):
        """
        Get the entry for the systolic blood pressure.

        Returns:
            dict: A dictionary containing the value, category, normal, color, and label of the systolic blood pressure.
        """
        category = self.get_systolic_category()
        if category is None:
            return None

        return {
            'value': self.systolic,
            'category': category,
            'normal': self.color_code['systolic']['normal'][category],
            'color': self.color_code['systolic']['colors'][category],
            'label': self.color_code['systolic']['labels'][category],
        }

    def get_diastolic_category(self):
        """
        Get the category of the diastolic blood pressure.

        Returns:
            int: The category of the diastolic blood pressure.
        """
        if self.diastolic is None:
            return None

        thresholds = self.color_code['diastolic']['thresholds']
        for i, threshold in enumerate(thresholds):
            if self.diastolic < threshold:
                return i
        return len(thresholds)

    def get_diastolic_entry(self):
        """
        Get the entry for the diastolic blood pressure.

        Returns:
            dict: A dictionary containing the value, category, normal, color, and label of the diastolic blood pressure.
        """
        category = self.get_diastolic_category()
        if category is None:
            return None

        return {
            'value': self.diastolic,
            'category': category,
            'normal': self.color_code['diastolic']['normal'][category],
            'color': self.color_code['diastolic']['colors'][category],
            'label': self.color_code['diastolic']['labels'][category],
        }

    def get_combination_category(self):
        """
        Get the category of the combination of systolic and diastolic blood pressure.

        Returns:
            int: The category of the combination of systolic and diastolic blood pressure.
        """

        systolic_category = self.get_systolic_category()
        diastolic_category = self.get_diastolic_category()

        logic = self.color_code['combinations']['logic']
        colors = self.color_code['combinations']['colors']

        # logic and colors should have the same length
        if len(logic) != len(colors):
            raise ValueError('Logic and colors should have the same length')

        # loop through the logic to determine the category
        # reverse iteration to select the worst category (needed for and-max logic)
        for i in range(len(logic) - 1, -1, -1):
            l = logic[i]
            if l == 'and':
                if systolic_category == i and diastolic_category == i:
                    return i
            elif l == 'or':
                if systolic_category == i or diastolic_category == i:
                    return i
            elif l == 'and-max': # special logic for american_heart_association
                if systolic_category <= i and diastolic_category <= i:
                    return max(systolic_category, diastolic_category)
            else:
                raise ValueError(f'Invalid logic {l}')

        return len(logic) - 1

    def get_combination_entry(
        self,
        html_highlight: str = 'underline',
        round_values: int = 0,
        html_separator: str = ' / ',
        ):
        """
        Get the entry for the combination of systolic and diastolic blood pressure.

        Args:
            html_highlight (str): The type of HTML highlighting to use for the values. Defaults to 'underline'.
            round_values (int): The number of decimal places to round the values to. Defaults to 0.
            html_separator (str): The separator to use between the systolic and diastolic values. Defaults to ' / '.

        Returns:
            dict: A dictionary containing the category, normal, color, label, and HTML representation of the combination of systolic and diastolic blood pressure.
        """

        category = self.get_combination_category()
        if category is None:
            return None

        systolic_entry = self.get_systolic_entry()
        diastolic_entry = self.get_diastolic_entry()

        systolic_entry_rounded = round(systolic_entry['value'], round_values)
        diastolic_entry_rounded = round(diastolic_entry['value'], round_values)

        if html_highlight == 'bold':
            systolic_html = f"<b>{systolic_entry_rounded}</b>" if not systolic_entry['normal'] else f"{systolic_entry_rounded}"
            diastolic_html = f"<b>{diastolic_entry_rounded}</b>" if not diastolic_entry['normal'] else f"{diastolic_entry_rounded}"
        elif html_highlight == 'underline':
            systolic_html = f"<u>{systolic_entry_rounded}</u>" if not systolic_entry['normal'] else f"{systolic_entry_rounded}"
            diastolic_html = f"<u>{diastolic_entry_rounded}</u>" if not diastolic_entry['normal'] else f"{diastolic_entry_rounded}"
        elif html_highlight == 'color':
            systolic_html = f"<span style='color: {systolic_entry['color']}'>{systolic_entry_rounded}</span>" if not systolic_entry['normal'] else f"{systolic_entry_rounded}"
            diastolic_html = f"<span style='color: {diastolic_entry['color']}'>{diastolic_entry_rounded}</span>" if not diastolic_entry['normal'] else f"{diastolic_entry_rounded}"
        else:
            raise ValueError(f'Invalid html_highlight {html_highlight}')

        html = f"{systolic_html}{html_separator}{diastolic_html}"

        return {
            'category': category,
            'normal': self.color_code['combinations']['normal'][category],
            'color': self.color_code['combinations']['colors'][category],
            'label': self.color_code['combinations']['labels'][category],
            'html': html,
        }

    def get_references(self):
        """
        Get the references for the blood pressure categories.

        Returns:
            list: A list of references for the blood pressure categories.
        """
        return self.color_code['references']

    def get_entries(self):
        """
        Get the entries for the systolic, diastolic, and combination of systolic and diastolic blood pressure.

        Returns:
            dict: A dictionary containing the entries for the systolic, diastolic, and combination of systolic and diastolic blood pressure.
        """
        return {
            'systolic': self.get_systolic_entry(),
            'diastolic': self.get_diastolic_entry(),
            'combination': self.get_combination_entry(),
        }


# test the class
if __name__ == '__main__':

    import pandas as pd

    if True:

        def test_color_coding(ccbp_class, color_code_name, test_entries):
            print(f'Testing color code: {color_code_name}')

            for sbp, dbp, expected_category in test_entries:
                ccbp = ccbp_class(systolic=sbp, diastolic=dbp, color_code_name=color_code_name)
                entry = ccbp.get_combination_entry()
                actual_category = entry['category']

                if actual_category == expected_category:
                    print(f'PASS: systolic={sbp}, diastolic={dbp}, expected={expected_category}, got={actual_category}')
                else:
                    print(f'FAIL: systolic={sbp}, diastolic={dbp}, expected={expected_category}, got={actual_category}')

        # Define expected entries for each color_code_name
        expected_entries_default = [
            (115, 75, 0), (115, 85, 1), (115, 95, 2), (115, 125, 2),
            (125, 75, 1), (125, 85, 1), (125, 95, 2), (125, 125, 2),
            (135, 75, 1), (135, 85, 1), (135, 95, 2), (135, 125, 2),
            (145, 75, 2), (145, 85, 2), (145, 95, 2), (145, 125, 2),
            (185, 75, 2), (185, 85, 2), (185, 95, 2), (185, 125, 2),
        ]

        expected_entries_american_heart_association = [
            (115, 75, 0), (115, 85, 2), (115, 95, 3), (115, 125, 4),
            (125, 75, 1), (125, 85, 2), (125, 95, 3), (125, 125, 4),
            (135, 75, 2), (135, 85, 2), (135, 95, 3), (135, 125, 4),
            (145, 75, 3), (145, 85, 3), (145, 95, 3), (145, 125, 4),
            (185, 75, 4), (185, 85, 4), (185, 95, 4), (185, 125, 4),
        ]

        # Test cases
        test_color_coding(ColorCodingBloodPressureCategories, 'default', expected_entries_default)
        print('\n')
        test_color_coding(ColorCodingBloodPressureCategories, 'american_heart_association', expected_entries_american_heart_association)

    if True:
        print('\n\n')
        for color_code_name in ['american_heart_association', 'default']:

            print(f'Color code: {color_code_name}')

            ccbp = ColorCodingBloodPressureCategories(systolic=120, diastolic=80, color_code_name=color_code_name)
            print(json_dumps(ccbp.get_entries(), indent=4))

            # loop
            print(ccbp.get_thresholds())
            entries = []
            for sbp in [115, 125, 135, 145, 185]:
                for dbp in [75, 85, 95, 125]:
                    ccbp = ColorCodingBloodPressureCategories(systolic=sbp, diastolic=dbp, color_code_name=color_code_name)
                    entry = ccbp.get_combination_entry()
                    entries.append({
                        'systolic': sbp,
                        'diastolic': dbp,
                        'category': entry['category'],
                        'color': entry['color'],
                        # 'label': entry['label'],
                        'html': entry['html'],
                    })

            df = pd.DataFrame(entries)
            print(f'Color code: {color_code_name}')
            print(df.to_string(index=False))
            print('\n\n')


"""
Expected categories by blood pressure values and color_code_name

    Color code: default
    systolic  diastolic  category
        115         75         0
        115         85         1
        115         95         2
        115        125         2
        125         75         1
        125         85         1
        125         95         2
        125        125         2
        135         75         1
        135         85         1
        135         95         2
        135        125         2
        145         75         2
        145         85         2
        145         95         2
        145        125         2
        185         75         2
        185         85         2
        185         95         2
        185        125         2

    Color code: american_heart_association
    systolic  diastolic  category
        115         75         0
        115         85         2
        115         95         3
        115        125         4
        125         75         1
        125         85         2
        125         95         3
        125        125         4
        135         75         2
        135         85         2
        135         95         3
        135        125         4
        145         75         3
        145         85         3
        145         95         3
        145        125         4
        185         75         4
        185         85         4
        185         95         4
        185        125         4

"""
