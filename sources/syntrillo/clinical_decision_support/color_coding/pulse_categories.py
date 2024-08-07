from json import dumps as json_dumps

from syntrillo.clinical_decision_support.color_coding.color_remapping import ColorReMapping

class ColorCodingPulseCategories:
    """
    Definiftion of categories for pulse rate values from BMP device. Likely at rest.

    """

    # Predefined color code configurations
    COLOR_CATEGORIES = [{
                        'name': 'internal1',
                        'pulse': {
                            'thresholds': (60, 80, 90),
                            'colors': ('lightblue', 'green', 'yellow', 'red'),
                            'labels': ('Low', 'Normal', 'Slightly Elevated', 'Elevated'),
                            'normal' : ( True, True, False, False),
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
        for color_category in ColorCodingPulseCategories.COLOR_CATEGORIES:
            if color_category['name'] == color_category_name:
                information = color_category['description'] + '<br>'

                # add references if any
                if color_category['references'] is not None:
                    information += 'References:<br>'
                    for reference in color_category['references']:
                        information += f'<a href="{reference}">{reference}</a><br>'

                # add thresholds
                information += '<br>'
                information += 'Thresholds:' + ', '.join(map(str, color_category['pulse']['thresholds'])) + '<br>'

                # add combination colors
                information += '<br>'
                information += 'Colors: ' + ', '.join(color_category['pulse']['colors']) + '<br>'

                information += '<br>'

                return information

        return None


    def __init__(
        self,
        pulse: float = None,
        color_category_name: str = 'internal1',
        alpha: float = 0.5,
    ):
        """
        Initializes an instance with specified systolic and diastolic blood pressure values and a color code name.

        Args:
            pulse (float): Pulse value.
            color_code_name (str): The name of the color code to use. Defaults to 'default'.
            alpha (float): Alpha value for the color code. Defaults to 0.5.
        """
        self.pulse = pulse
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
        Retrieves the pulse thresholds for the current color code.

        Returns:
            dict: A dictionary with pulse thresholds.
        """
        return {
            'pulse': self.color_category['pulse']['thresholds'],
        }

    def get_pulse_category(self):
        """
        Determines the category of the pulse value.

        Returns:
            int: The category index of the pulse value.
        """
        if self.pulse is None:
            return None

        thresholds = self.color_category['pulse']['thresholds']
        for i, threshold in enumerate(thresholds):
            if self.pulse < threshold:
                return i
        return len(thresholds)

    def get_pulse_entry(self, pulse: float = None):
        """
        Get the entry for the pulse value.

        Args:
            pulse (float): Pulse value. Defaults to None.

        Returns:
            dict: A dictionary containing the value, category, normal, color, and label of the pulse value.
        """

        if pulse is not None:
            self.pulse = pulse

        category = self.get_pulse_category()
        if category is None:
            return None

        html = f"{self.pulse:.{self.round_values}f}"

        return {
            'value': self.pulse,
            'category': category,
            'normal': self.color_category['pulse']['normal'][category],
            'color': ColorReMapping.get_color(self.color_category['pulse']['colors'][category], self.alpha),
            'label': self.color_category['pulse']['labels'][category],
            'html': html,
        }

    def get_no_data_entry(self):
        """
        Get the entry for pulse value when no data is available.

        Returns:
            dict: A dictionary containing the category, normal, color, and label of pulse value.
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

