# Path: ./sources/syntrillo/helper_functions/plotly.py
import json
import plotly.utils as pu
from plotly.graph_objs import Figure

def plotly_fig_to_dict(fig: Figure) -> dict:
    """
    Convert a Plotly figure to a JSON-compatible dictionary.

    This function serializes a Plotly figure to a JSON string using the
    PlotlyJSONEncoder, and then deserializes it back to a Python dictionary.

    Args:
        fig (Figure): The Plotly figure to convert.

    Returns:
        dict: The JSON-compatible dictionary representation of the Plotly figure.
    """
    # Serialize the Plotly figure to a JSON string
    fig_json_str = json.dumps(fig, cls=pu.PlotlyJSONEncoder)

    # Deserialize the JSON string back into a Python dictionary
    fig_dict = json.loads(fig_json_str)

    return fig_dict
