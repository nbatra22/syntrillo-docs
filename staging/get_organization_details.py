# staging/get_organization_details.py

import sys
import os
import json

# Add the modules root directory to sys.path
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)


from modules.healthie.utils import HealthieAPI

def main():

    # Load environment variables from .env file
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")

    try:
        # Create an instance of HealthieAPI with the provided API key and organization
        healthie_api = HealthieAPI(dotenv_path=dotenv_path)

        # Example: Get organization details
        organization_details = healthie_api.get_organization_details()

        # Print the organization details
        print("Organization Details:")
        print(json.dumps(organization_details, indent=4))

        # You can add more API calls or tests using other methods of the HealthieAPI class here

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Call the main function
    main()
