# staging/get_organization_status.py

import sys
import os
import json

from syntrillo.healthie.utils import HealthieAPIUtils

def main():

    # Load environment variables from .env file
    dotenv_path = ".env.staging"

    try:
        # Create an instance of HealthieAPI with the provided API key and organization
        utils_api = HealthieAPIUtils(dotenv_path=dotenv_path)

        # Example: Get organization details
        organization_details = utils_api.get_organization_details()

        # Print the organization details
        print("Organization Details:")
        print(json.dumps(organization_details, indent=4))

        # Example: List patients
        patients = utils_api.list_patients()

        # Print the organization details
        print("Patients:")
        print(json.dumps(patients, indent=4))


    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Call the main function
    main()
