# Path: ./sources/syntrillo/system/dot_env_loader.py
import os
from dotenv import load_dotenv

class DotEnvFileLoader:

    # default path to the .env file, at the root of the repository
    DEFAULT_DOTENV_PATH = ".env"

    # In pythonanywhere, the .env file is located in the home directory, and has to be specified manually
    PYTHON_ANYWHERE_FLAG = '/home/syntrillo/_this_is_PythonAnywhere_'
    PYTHON_ANYWHERE_DOTENV_PATH = '/home/syntrillo/Syntrillo_Clinic/.env'

    def __init__(self):
        """
        Determines the correct path to the .env file based on the environment where this code is running.

        Loads the file.

        Returns:
            str: The path to the .env file.
        """
        if os.path.exists(self.PYTHON_ANYWHERE_FLAG):
            self.dotenv_path = self.PYTHON_ANYWHERE_DOTENV_PATH
        else:
            self.dotenv_path = self.DEFAULT_DOTENV_PATH

        load_dotenv(dotenv_path=self.dotenv_path)

    def get_dotenv_path(self):
        return self.dotenv_path



# Example usage
if __name__ == '__main__':
    env_locator = DotEnvFileLoader()
    dotenv_path = env_locator.get_dotenv_path()
    print(f"Using .env file at: {dotenv_path}")

    # example of using the environment variables
    print("TENOVI_CLIENT_DOMAIN:", os.getenv('TENOVI_CLIENT_DOMAIN'))

