from typing import Optional

def clean_text(text: Optional[str]) -> str:
    """
    Cleans text by removing leading/trailing whitespace and handling None values.

    Args:
        text: The text to clean, can be None

    Returns:
        str: The cleaned text, empty string if input was None
    """
    if text is None:
        return ""
    return str(text).strip()