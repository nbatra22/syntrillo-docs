# Path: ./sources/syntrillo/api_healthie/misc.py

import re  # Import regular expression module
from datetime import datetime
import json

# conda install bleach markdown
import bleach
import markdown
from markupsafe import Markup

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

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


def log_this(
    message : any,
    filepath : str = None
):
    """
    Stores some logs locally. Default is verbose file.
    """

    # Do not log in AWS Lambda as it is not possible to access the file system
    if LocalEnvironmentAndSecrets().is_lambda() :
        return

    if filepath is None:
        filepath = 'ignore_healthie_log_verbose.txt'

    # Check if message is a dictionary
    if isinstance(message, dict):
        message = json.dumps(message, indent=4)

    # Get the current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format the log entry with the current date and time
    log_entry = f"\n---- {current_datetime}\n\n{message}\n\n"

    # Write the log entry to the file
    with open(filepath, 'a') as f:
        f.write(log_entry)

