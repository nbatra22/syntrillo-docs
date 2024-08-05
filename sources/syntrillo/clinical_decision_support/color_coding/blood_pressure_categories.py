
from json import dumps as json_dumps

from syntrillo.clinical_decision_support.color_coding.color_remapping import ColorReMapping

class ColorCodingBloodPressureCategories:
    """
    A class to handle color coding categories for blood pressure values.

    Attributes:
        COLOR_CATEGORIES (list): List of dictionaries with color code configurations.
        color_category (dict): Currently selected color code.
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
    COLOR_CATEGORIES = [{
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
    color_category = None

    # default options for the get_combination_entry method
    html_highlight: str = 'underline'
    round_values: int = 0
    html_separator: str = ' / '

    # no data combination
    no_data_string = 'no data'
    no_data_color = 'White'


    def __init__(
        self,
        systolic: float = None,
        diastolic: float = None,
        color_category_name: str = 'default',
        alpha: float = 0.5,
    ):
        """
        Initializes an instance with specified systolic and diastolic blood pressure values and a color code name.

        Args:
            systolic (float): Systolic blood pressure value.
            diastolic (float): Diastolic blood pressure value.
            color_code_name (str): The name of the color code to use. Defaults to 'default'.
            alpha (float): Alpha value for the color code. Defaults to 0.5.
        """
        self.systolic = systolic
        self.diastolic = diastolic
        self.alpha = alpha

        # Select the appropriate color code based on the provided name
        for color_category in self.COLOR_CATEGORIES:
            if color_category['name'] == color_category_name:
                self.color_category = color_category
                break

        if self.color_category is None:
            raise ValueError(f'Color code {color_category_name} not found')

    def get_thresholds(self):
        """
        Retrieves the blood pressure thresholds for the current color code.

        Returns:
            dict: A dictionary with systolic and diastolic thresholds.
        """
        return {
            'systolic': self.color_category['systolic']['thresholds'],
            'diastolic': self.color_category['diastolic']['thresholds'],
        }

    def get_systolic_category(self):
        """
        Determines the category of the systolic blood pressure.

        Returns:
            int: The category index of the systolic blood pressure.
        """
        if self.systolic is None:
            return None

        thresholds = self.color_category['systolic']['thresholds']
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
            'normal': self.color_category['systolic']['normal'][category],
            'color': ColorReMapping.get_color(self.color_category['systolic']['colors'][category], self.alpha),
            'label': self.color_category['systolic']['labels'][category],
        }

    def get_diastolic_category(self):
        """
        Get the category of the diastolic blood pressure.

        Returns:
            int: The category of the diastolic blood pressure.
        """
        if self.diastolic is None:
            return None

        thresholds = self.color_category['diastolic']['thresholds']
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
            'normal': self.color_category['diastolic']['normal'][category],
            'color': ColorReMapping.get_color(self.color_category['diastolic']['colors'][category], self.alpha),
            'label': self.color_category['diastolic']['labels'][category],
        }

    def get_combination_category(self):
        """
        Get the category of the combination of systolic and diastolic blood pressure.

        Returns:
            int: The category of the combination of systolic and diastolic blood pressure.
        """

        systolic_category = self.get_systolic_category()
        diastolic_category = self.get_diastolic_category()

        logic = self.color_category['combinations']['logic']
        colors = self.color_category['combinations']['colors']

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

    def set_combination_entry_options(
        self,
        html_highlight: str = 'underline',
        round_values: int = 0,
        html_separator: str = ' / ',
        ):
        """
        Set the options for the get_combination_entry method.

        Args:
            html_highlight (str): The type of HTML highlighting to use for the values. Defaults to 'underline'.
            round_values (int): The number of decimal places to round the values to. Defaults to 0.
            html_separator (str): The separator to use between the systolic and diastolic values. Defaults to ' / '.
        """
        self.html_highlight = html_highlight
        self.round_values = round_values
        self.html_separator = html_separator


    def get_combination_entry(
        self,
        systolic: float = None,
        diastolic: float = None,
        round_values: int = None,
        ):
        """
        Get the entry for the combination of systolic and diastolic blood pressure.

        Args:
            systolic (float): The systolic blood pressure value. Defaults to the value provided during initialization.
            diastolic (float): The diastolic blood pressure value. Defaults to the value provided during initialization.

        Returns:
            dict: A dictionary containing the category, normal, color, label, and HTML representation of the combination of systolic and diastolic blood pressure.
        """

        # update the systolic and diastolic values if provided
        if systolic is not None:
            self.systolic = systolic

        if diastolic is not None:
            self.diastolic = diastolic

        # update the round_values if provided
        if round_values is not None:
            self.round_values = round_values

        # get the category of the combination
        category = self.get_combination_category()
        if category is None:
            return self.get_no_data_combination_entry()

        systolic_entry = self.get_systolic_entry()
        diastolic_entry = self.get_diastolic_entry()

        # round the values and format as needed
        systolic_entry_rounded = f"{systolic_entry['value']:.{self.round_values}f}"
        diastolic_entry_rounded = f"{diastolic_entry['value']:.{self.round_values}f}"

        if self.html_highlight == 'bold':
            systolic_html = f"<b>{systolic_entry_rounded}</b>" if not systolic_entry['normal'] else f"{systolic_entry_rounded}"
            diastolic_html = f"<b>{diastolic_entry_rounded}</b>" if not diastolic_entry['normal'] else f"{diastolic_entry_rounded}"
        elif self.html_highlight == 'underline':
            systolic_html = f"<u>{systolic_entry_rounded}</u>" if not systolic_entry['normal'] else f"{systolic_entry_rounded}"
            diastolic_html = f"<u>{diastolic_entry_rounded}</u>" if not diastolic_entry['normal'] else f"{diastolic_entry_rounded}"
        elif self.html_highlight == 'color':
            systolic_html = f"<span style='color: {systolic_entry['color']}'>{systolic_entry_rounded}</span>" if not systolic_entry['normal'] else f"{systolic_entry_rounded}"
            diastolic_html = f"<span style='color: {diastolic_entry['color']}'>{diastolic_entry_rounded}</span>" if not diastolic_entry['normal'] else f"{diastolic_entry_rounded}"
        else:
            raise ValueError(f'Invalid html_highlight {self.html_highlight}')

        html = f"{systolic_html}{self.html_separator}{diastolic_html}"

        return {
            'category': category,
            'normal': self.color_category['combinations']['normal'][category],
            'color': ColorReMapping.get_color(self.color_category['combinations']['colors'][category], self.alpha),
            'label': self.color_category['combinations']['labels'][category],
            'html': html,
        }

    def get_no_data_combination_entry(self):
        """
        Get the entry for the combination of systolic and diastolic blood pressure when no data is available.

        Returns:
            dict: A dictionary containing the category, normal, color, and label of the combination of systolic and diastolic blood pressure.
        """
        self.no_data_combination_entry = {
            'category': None,
            'normal': None,
            'color': self.no_data_color,
            'label': self.no_data_string,
            'html': self.no_data_string,
        }

        return self.no_data_combination_entry

    def get_references(self):
        """
        Get the references for the blood pressure categories.

        Returns:
            list: A list of references for the blood pressure categories.
        """
        return self.color_category['references']

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

        def test_color_coding(ccbp_class, color_category_name, test_entries):
            print(f'Testing color code: {color_category_name}')

            for sbp, dbp, expected_category in test_entries:
                ccbp = ccbp_class(systolic=sbp, diastolic=dbp, color_category_name=color_category_name)
                entry = ccbp.get_combination_entry()
                actual_category = entry['category']

                if actual_category == expected_category:
                    print(f'PASS: systolic={sbp}, diastolic={dbp}, expected={expected_category}, got={actual_category}')
                else:
                    print(f'FAIL: systolic={sbp}, diastolic={dbp}, expected={expected_category}, got={actual_category}')

        # Define expected entries for each color_category_name
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
        for color_category_name in ['american_heart_association', 'default']:

            print(f'Color code: {color_category_name}')

            ccbp = ColorCodingBloodPressureCategories(systolic=120, diastolic=80, color_category_name=color_category_name)
            print(json_dumps(ccbp.get_entries(), indent=4))

            # loop
            print(ccbp.get_thresholds())
            entries = []
            ccbp = ColorCodingBloodPressureCategories(color_category_name=color_category_name)
            for sbp in [115, 125, 135, 145, 185]:
                for dbp in [75, 85, 95, 125]:
                    entry = ccbp.get_combination_entry(systolic=sbp, diastolic=dbp)
                    entries.append({
                        'systolic': sbp,
                        'diastolic': dbp,
                        'category': entry['category'],
                        'color': entry['color'],
                        # 'label': entry['label'],
                        'html': entry['html'],
                    })

            df = pd.DataFrame(entries)
            print(f'Color code: {color_category_name}')
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
