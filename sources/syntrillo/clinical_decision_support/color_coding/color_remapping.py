# Path: ./sources/syntrillo/clinical_decision_support/color_coding/color_remapping.py

from syntrillo.system.matplotlib_setup import setup_matplotlib
setup_matplotlib()

import matplotlib.colors as mcolors

class ColorReMapping:
    """
    A class to redefine common colors for the application.

    Traffic light signals are used to indicate the status of the patient.

    Some tweaks are made to the colors to make them more visible.

    """

    color_map = {
        'green': '#00FF00',
        'yellow': '#FFFF00',
        'orange': '#FFA500',
        'red': '#FF0000',
        'dark_red': '#8B0000',
    }

    def __init__(self):
        pass

    @staticmethod
    def get_hex_code(color_name: str) -> str:
        """
        Get the hex code for a given color name.

        Args:
            color_name : str : the color name

        Returns:
            str : the hex code for the color name
        """
        # If the color name exists in the color map, return its hex code
        if color_name in ColorReMapping.color_map:
            return ColorReMapping.color_map[color_name]

        # If the color name is not found, use matplotlib to convert the name to hex
        try:
            hex_code = mcolors.to_hex(color_name)
            return hex_code
        except ValueError:
            return ''


    @staticmethod
    def get_color(color_name: str, alpha: float = 1) -> str:
        """
        Transform the color name to its hex code from the class color map.

        Add the alpha value to the hex code.

        Args:
            color_name : str : the color name
            alpha : float : the alpha value

        Returns:
            str : the hex code with the alpha value (starts with #)

        """

        # Retrieve the hex code for the color name
        if color_name in ColorReMapping.color_map:
            hex_code = ColorReMapping.color_map[color_name]
        else:
            if color_name.startswith('#'):
                hex_code = color_name
            else:
                hex_code = ColorReMapping.get_hex_code(color_name)

        # Ensure hex_code is valid
        if not hex_code or not hex_code.startswith('#') or len(hex_code) not in (7, 9):
            raise ValueError(f"Invalid color name or hex code: {color_name}")

        # Convert alpha to a value between 0 and 255, and then to a hex string
        alpha_hex = format(int(alpha * 255), '02X')

        # Append the alpha value to the hex code
        if len(hex_code) == 7:  # No alpha value present in the hex code
            hex_code_with_alpha = hex_code + alpha_hex
        else:
            hex_code_with_alpha = hex_code[:7] + alpha_hex

        return hex_code_with_alpha


if __name__ == '__main__':
    # Test the ColorCodes class
    cc = ColorReMapping()

    print(cc.get_color('green', 0.5))  # Expected: #00FF0080
    print(cc.get_color('magenta', 0.5))  # Expected: #00FF0080
