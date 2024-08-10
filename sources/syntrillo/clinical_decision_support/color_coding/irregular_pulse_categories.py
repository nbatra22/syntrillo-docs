# Path: ./sources/syntrillo/clinical_decision_support/color_coding/irregular_pulse_categories.py
from json import dumps as json_dumps

from syntrillo.clinical_decision_support.color_coding.color_remapping import ColorReMapping

class ColorCodingIrregularPulseCategories:
    """
    Definiftion of categories for irregular_pulse rate values from BMP device. Likely at rest.

    """

    # Predefined color code configurations
    COLOR_CATEGORIES = [{
                        'name': 'internal1',
                        'irregular_pulse': {
                            'thresholds': (1, ),
                            'colors': ('green', 'red'),
                            'labels': ('Normal', 'Irregular pulse detected'),
                            'normal' : ( True, False),
                            },
                        'description' : 'Internal color scheme',
                        'references': None
                    },
                        ]

    # current color code selected
    color_category = None

    # default number of decimal places to round to
    round_values : int = 0

    # no data combination
    no_data_string = 'no data'
    no_data_color = 'White'

    @staticmethod
    def get_html_information(color_category_name: str):
        """
        Get the information of the color code.

        Args:
            color_category_name (str): The name of the color code.

        Returns:
            str: The information of the color code.
        """
        for color_category in ColorCodingIrregularPulseCategories.COLOR_CATEGORIES:
            if color_category['name'] == color_category_name:
                information = color_category['description'] + '<br>'

                # add references if any
                if color_category['references'] is not None:
                    information += 'References:<br>'
                    for reference in color_category['references']:
                        information += f'<a href="{reference}">{reference}</a><br>'

                # add thresholds
                information += '<br>'
                information += 'Thresholds: ' + ', '.join(map(str, color_category['irregular_pulse']['thresholds'])) + '<br>'

                # add combination colors
                information += '<br>'
                information += 'Colors: ' + ', '.join(color_category['irregular_pulse']['colors']) + '<br>'

                information += '<br>'

                return information

        return None


    def __init__(
        self,
        irregular_pulse: float = None,
        color_category_name: str = 'internal1',
        alpha: float = 0.5,
    ):
        """
        Initializes an instance with specified systolic and diastolic blood pressure values and a color code name.

        Args:
            irregular_pulse (float): Pulse value.
            color_code_name (str): The name of the color code to use. Defaults to 'default'.
            alpha (float): Alpha value for the color code. Defaults to 0.5.
        """
        self.irregular_pulse = irregular_pulse
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
        Retrieves the irregular_pulse thresholds for the current color code.

        Returns:
            dict: A dictionary with irregular_pulse thresholds.
        """
        return {
            'irregular_pulse': self.color_category['irregular_pulse']['thresholds'],
        }

    def get_irregular_pulse_category(self):
        """
        Determines the category of the irregular_pulse value.

        Returns:
            int: The category index of the irregular_pulse value.
        """
        if self.irregular_pulse is None:
            return None

        thresholds = self.color_category['irregular_pulse']['thresholds']
        for i, threshold in enumerate(thresholds):
            if self.irregular_pulse < threshold:
                return i
        return len(thresholds)

    def get_irregular_pulse_entry(self, irregular_pulse: float = None):
        """
        Get the entry for the irregular_pulse value.

        Args:
            irregular_pulse (float): Pulse value. Defaults to None.

        Returns:
            dict: A dictionary containing the value, category, normal, color, and label of the irregular_pulse value.
        """

        if irregular_pulse is not None:
            self.irregular_pulse = irregular_pulse

        category = self.get_irregular_pulse_category()
        if category is None:
            return None

        html = f"{self.irregular_pulse:.{self.round_values}f}"

        return {
            'value': self.irregular_pulse,
            'category': category,
            'normal': self.color_category['irregular_pulse']['normal'][category],
            'color': ColorReMapping.get_color(self.color_category['irregular_pulse']['colors'][category], self.alpha),
            'label': self.color_category['irregular_pulse']['labels'][category],
            'html': html,
        }

    def get_no_data_entry(self):
        """
        Get the entry for irregular_pulse value when no data is available.

        Returns:
            dict: A dictionary containing the category, normal, color, and label of irregular_pulse value.
        """
        self.no_data_combination_entry = {
            'value': None,
            'category': None,
            'normal': None,
            'color': self.no_data_color,
            'label': self.no_data_string,
            'html': self.no_data_string,
        }

        return self.no_data_combination_entry


if __name__ == '__main__':
    # Test the ColorCodingIrregularPulseCategories class

    if True:
        irregular_pulse = 10
        color_code_name = 'internal1'
        alpha = 0.5

        color_coding_irregular_pulse = ColorCodingIrregularPulseCategories(irregular_pulse, color_code_name, alpha)

        print(f'irregular_pulse: {irregular_pulse}')
        print(f'color_code_name: {color_code_name}')
        print(f'alpha: {alpha}')

        print(f'irregular_pulse thresholds: {color_coding_irregular_pulse.get_thresholds()}')
        print(f'irregular_pulse category: {color_coding_irregular_pulse.get_irregular_pulse_category()}')
        print(f'irregular_pulse entry: {color_coding_irregular_pulse.get_irregular_pulse_entry()}')
        print(f'no data entry: {color_coding_irregular_pulse.get_no_data_entry()}')
        print(json_dumps(color_coding_irregular_pulse.get_irregular_pulse_entry(), indent=4))
        print(json_dumps(color_coding_irregular_pulse.get_no_data_entry(), indent=4))

    print('--------------------------------')

    if True:
        irregular_pulse = 0
        color_code_name = 'internal1'
        alpha = 0.5

        color_coding_irregular_pulse = ColorCodingIrregularPulseCategories(irregular_pulse, color_code_name, alpha)

        print(f'irregular_pulse: {irregular_pulse}')
        print(f'color_code_name: {color_code_name}')
        print(f'alpha: {alpha}')

        print(f'irregular_pulse thresholds: {color_coding_irregular_pulse.get_thresholds()}')
        print(f'irregular_pulse category: {color_coding_irregular_pulse.get_irregular_pulse_category()}')
        print(f'irregular_pulse entry: {color_coding_irregular_pulse.get_irregular_pulse_entry()}')
        print(f'no data entry: {color_coding_irregular_pulse.get_no_data_entry()}')
        print(json_dumps(color_coding_irregular_pulse.get_irregular_pulse_entry(), indent=4))
        print(json_dumps(color_coding_irregular_pulse.get_no_data_entry(), indent=4))



