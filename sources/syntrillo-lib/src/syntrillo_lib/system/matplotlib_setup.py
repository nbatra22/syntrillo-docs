# Path: ./sources/syntrillo/system/matplotlib_setup.py

import os
from syntrillo_lib.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

def setup_matplotlib():
    """
    Set up the Matplotlib configuration directory for AWS Lambda.
    """

    if LocalEnvironmentAndSecrets().is_lambda():
        # Define the path for the Matplotlib configuration directory
        mpl_config_dir = '/tmp/matplotlib'

        # Create the directory if it doesn't exist
        os.makedirs(mpl_config_dir, exist_ok=True)

        # Set the MPLCONFIGDIR environment variable to the created directory
        os.environ['MPLCONFIGDIR'] = mpl_config_dir
