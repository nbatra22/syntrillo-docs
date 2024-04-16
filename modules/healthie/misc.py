
import re  # Import regular expression module

def extract_user_id_from_url(url):
    """
    Extracts user ID from the referrer URL.
     : referrer_url: https://securestaging.gethealthie.com/users/1035117  # that's the patient ID

    Args:
        url (str): Referrer URL containing the user ID.

    Returns:
        str: Extracted user ID.
    """
    # Use regular expression to extract digits (user ID) from the URL
    match = re.search(r'/users/(\d+)', url)
    if match:
        return match.group(1)  # Return the extracted user ID
    else:
        return None  # Return None if user ID is not found


