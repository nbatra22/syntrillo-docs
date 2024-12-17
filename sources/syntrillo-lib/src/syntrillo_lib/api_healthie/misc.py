# Path: ./sources/syntrillo/api_healthie/misc.py

import re  # Import regular expression module
from datetime import datetime
import json

# conda install bleach markdown
import bleach
import markdown
from markupsafe import Markup

from syntrillo_lib.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

def extract_healthie_user_id_from_url(url):
    """
    Extracts user ID from the referrer URL.
     : referrer_url: https://securestaging.gethealthie.com/users/1035117  # that's the patient ID

    Args:
        url (str): Referrer URL containing the user ID.

    Returns:
        str: Extracted user ID.
    """
    # Use regular expression to extract digits (user ID) from the URL
    if url is not None:
        match = re.search(r'/users/(\d+)', url)
        if match:
            return match.group(1)  # Return the extracted user ID
        else:
            return None  # Return None if user ID is not found
    else:
        return None   # Return None if url is None

