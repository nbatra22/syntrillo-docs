import re

def remove_html_tags(text: str) -> str:
    """
    Removes HTML tags from the given text.

    Args:
        text (str): The text to remove HTML tags from.

    Returns:
        text (str): The text with HTML tags removed.

    """
    clean = re.sub('<.*?>', '', text)
    return clean

