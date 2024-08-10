# Path: ./sources/syntrillo/clinical_decision_support/color_coding/blood_pressure_rainbow.py
# get rainbow color for blood pressure

from matplotlib import colors as mcolors

class ColorCodingBloodPressureRainbows:

    # class variables
    systolic: float = None
    diastolic: float = None
    alpha: float = 0.5

    z = 0.1

    def __init__(
        self,
        systolic: float = None,
        diastolic: float = None,
        alpha: float = 0.5,
    ):
        """
        Initializes an instance with specified systolic and diastolic blood pressure values and a color code name.

        Args:
            systolic (float): Systolic blood pressure value.
            diastolic (float): Diastolic blood pressure value.
            alpha (float): Alpha value for the color code.
        """
        self.systolic = systolic
        self.diastolic = diastolic
        self.alpha = alpha

    def set_values(
        self,
        systolic: float = None,
        diastolic: float = None,
        alpha: float = None,
        ):
        """
        Set the systolic and diastolic blood pressure values and the alpha value for the color code.

        Args:
            systolic (float): Systolic blood pressure value.
            diastolic (float): Diastolic blood pressure value.
            alpha (float): Alpha value for the color code.
        """
        if systolic is not None:
            self.systolic = systolic
        if diastolic is not None:
            self.diastolic = diastolic
        if alpha is not None:
            self.alpha = alpha


    def get_color_for_systolic(self) -> str:
        """
        Function to get color for systolic blood pressure value using a colormap

        Args:
            systolic: float, the systolic blood pressure value

        Returns:
            color: str, the color corresponding to the systolic value
        """
        # Normalize the systolic values to the range of the colormap
        norm_red = mcolors.Normalize(vmin=130, vmax=200)
        norm_green = mcolors.Normalize(vmin=100, vmax=130)

        systolic_norm_red = norm_red(self.systolic)/4
        systolic_norm_green = norm_green(self.systolic)/4

        # Map the systolic value to a color, with a reversed colormap
        z = self.z
        if self.systolic >= 130:
            color = (1 - systolic_norm_red, z, z)
        elif 100 <= self.systolic < 130:
            color = (z, 1-systolic_norm_green/4, z)
        else:
            # blue
            color = (z, z, 1)

        # Add the alpha transparency
        color_with_alpha = (color[0], color[1], color[2], self.alpha)

        # Convert the RGBA color to a hexadecimal string with alpha
        color_hex = mcolors.to_hex(color_with_alpha, keep_alpha=True)

        # save normalized values for systolic
        self.systolic_norm_red = systolic_norm_red
        self.systolic_norm_green = systolic_norm_green

        return color_hex


    def get_color_for_diastolic(self) -> str:
        """
        Function to get color for diastolic blood pressure value using a colormap

        Args:
            diastolic: float, the diastolic blood pressure value

        Returns:
            color: str, the color corresponding to the diastolic value
        """
        norm_red = mcolors.Normalize(vmin=90, vmax=120)
        norm_green = mcolors.Normalize(vmin=50, vmax=90)

        diastolic_norm_red = norm_red(self.diastolic) / 4
        diastolic_norm_green = norm_green(self.diastolic) / 4

        # Map the systolic value to a color, with a reversed colormap
        z = self.z
        if self.diastolic >= 90:
            color = (1 - diastolic_norm_red, z, z)
        elif 50 <= self.diastolic < 90:
            color = (z, 1 - diastolic_norm_green, z)
        else:
            # blue
            color = (z, z, 1)

        # Add the alpha transparency
        color_with_alpha = (color[0], color[1], color[2], self.alpha)

        # Convert the RGBA color to a hexadecimal string with alpha
        color_hex = mcolors.to_hex(color_with_alpha, keep_alpha=True)

        # save normalized values for diastolic
        self.diastolic_norm_red = diastolic_norm_red
        self.diastolic_norm_green = diastolic_norm_green

        return color_hex


    def get_color_for_blood_pressure(self) -> str:
        """
        Function to get color for blood pressure value using a colormap

        Args:
            systolic: float, the systolic blood pressure value
            diastolic: float, the diastolic blood pressure value

        Returns:
            color: str, the color corresponding to the blood pressure value
        """

        # get normalized values for systolic and diastolic in the class
        _ = self.get_color_for_systolic()
        _ = self.get_color_for_diastolic()

        z = self.z
        if self.diastolic >= 90 or self.systolic >= 130:
            color = ( 1 - max(self.systolic_norm_red, self.diastolic_norm_red), z, z)
        elif 50 <= self.diastolic < 90 and 100 <= self.systolic < 130:
            color = (z, 1 - max(self.systolic_norm_green, self.diastolic_norm_green), z)
        else:
            # blue
            color = (z, z, 1)

        # Add the alpha transparency
        color_with_alpha = (color[0], color[1], color[2], self.alpha)

        # Convert the RGBA color to a hexadecimal string with alpha
        color_hex = mcolors.to_hex(color_with_alpha, keep_alpha=True)

        return color_hex

