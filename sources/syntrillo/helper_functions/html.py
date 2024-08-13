import re
import markdown
from bleach.css_sanitizer import CSSSanitizer
from bleach.sanitizer import Cleaner


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


def transform_to_safe_html(input_str: str) -> str:
    """
    Transform a given input to safe HTML.

    This function checks if the response contains HTML or Markdown content
    and sanitizes it to ensure safe rendering in the browser. If the response
    does not contain HTML or Markdown, it is returned as-is.

    Parameters:
    - input (str): The input string to transform.

    Returns:
    - str: The transformed input as safe HTML.
    """
    # Define allowed tags and attributes
    my_allowed_tags = [
        'h3', 'h4', 'h5', 'p', 'a', 'strong', 'b', 'u', 'i', 'em', 'sub', 'sup',
        'ul', 'ol', 'li', 'img', 'table', 'tr', 'td', 'th', 'tbody', 'span', 'div', 'br'
    ]
    my_allowed_attributes = {
        'a': ['href', 'title'],
        'p': ['class'],  # for Bootstrap
        'img': ['src', 'alt'],
        'table': ['border', 'cellpadding', 'cellspacing'],
        'td': ['colspan', 'rowspan'],
        'span': ['style'],  # for LaTeX
        'div': ['style'],  # for LaTeX
    }

    # Initialize a CSSSanitizer to allow specific CSS properties
    css_sanitizer = CSSSanitizer(allowed_css_properties=["color", "font-size", "background-color"])

    # Initialize a bleach Cleaner with the CSS sanitizer
    cleaner = Cleaner(tags=my_allowed_tags, attributes=my_allowed_attributes, css_sanitizer=css_sanitizer, strip=True)

    # Regex pattern to detect HTML tags
    html_tag_pattern = re.compile(r'<[^>]+>')

    # Regex pattern to detect Markdown (simple heuristic)
    # More specific Markdown pattern detection (only matches at start of line)
    markdown_pattern = re.compile(r'^\s*(#{1,6}\s|[*_~`]{1,2}|[>\-+]\s)', re.MULTILINE)

    # Check if the response contains HTML or Markdown
    if html_tag_pattern.search(input_str):
        # If HTML is found, clean it
        cleaned_html = cleaner.clean(input_str)
        return cleaned_html

    elif markdown_pattern.search(input_str):
        # If Markdown is found, convert to HTML and clean it
        html_output = markdown.markdown(input_str)
        cleaned_html = cleaner.clean(html_output)
        return cleaned_html

    else:
        # If no HTML or Markdown is detected, return the response as-is
        return input_str

if __name__ == '__main__':
    # Test the helper functions
    test_html = '<p><b>Hello</b> <a href="https://example.com">World</a></p>'
    test_markdown = '**Hello** [World](https://example.com)'
    test_plain_text = 'Hello World'

    print(remove_html_tags(test_html))
    print(transform_to_safe_html(test_html))
    print(transform_to_safe_html(test_markdown))
    print(transform_to_safe_html(test_plain_text))

