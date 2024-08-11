import re
import bleach
import markdown
from markupsafe import Markup


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

def transform_to_safe_html(response : str) -> str:
    """
    Transform a given response to safe HTML.

    This function checks if the response contains HTML or Markdown content
    and sanitizes it to ensure safe rendering in the browser.

    Parameters:
    - response (str): The input response to transform.

    Returns:
    - Markup: The transformed response as safe HTML.
    """
    # Define regular expressions for HTML and Markdown patterns
    html_pattern = re.compile(r'<[^>]+>')
    markdown_pattern = re.compile(r'^\s*#.*|^[\*\-_]\s')

    # Define your own allowed tags and attributes
    my_allowed_tags = ['h3', 'h4', 'h5', 'p', 'a', 'strong', 'b', 'u', 'i', 'em', 'sub', 'sup',
                       'ul', 'ol', 'li',
                       'img',
                       'table', 'tr', 'td', 'th', 'tbody',
                       'span', 'div',
                       'br',
                       ]
    my_allowed_attributes = {'a': ['href', 'title'],
                             'p': ['class'],  # for bootstrap
                             'img': ['src', 'alt'],
                             'table': ['border', 'cellpadding', 'cellspacing'],
                             'td': ['colspan', 'rowspan'],
                             'span' : ['style'], # for LaTex
                             'div' : ['style'],  # for LaTex
                             }

    # Use bleach with custom allowed tags and attributes
    cleaned_html = bleach.clean(response, tags=my_allowed_tags, attributes=my_allowed_attributes)

    html_output = bleach.clean(markdown.markdown(response), tags=my_allowed_tags, attributes=my_allowed_attributes)

    return Markup(html_output)

