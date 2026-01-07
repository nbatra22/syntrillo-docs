# Path: ./sources/syntrillo/system/local_environment_and_secrets.py
import os
import json
import requests
from dotenv import load_dotenv
from syntrillo.system.logger import logger

class LocalEnvironmentAndSecrets:
    """
    This class delivers secrets (keys, passwords, etc.) from the local environment where the code is running.

    If running on AWS Lambda, it retrieves secrets from AWS Secrets Manager.

    If running a personal PC, it retrieves secrets from the .env file located in the root of the repository.

    If running on PythonAnywhere, it retrieves secrets from a .env file located in a specific directory.

    Each secret is accessed by calling the appropriate method.

    """

    # ------------------------------
    # AWS env variables with ARNs (so that they are not hard coded below)
    AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN = 'AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN'
    AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN = 'AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN'
    AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN = 'AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN'
    AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN = 'AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN'
    AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN = 'AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN'
    AWS_SECRETS_MANAGER_CANDID_SECRET_ARN = 'AWS_SECRETS_MANAGER_CANDID_SECRET_ARN'
    AWS_LAMBDA_BLOOD_PRESSURE_ANALYSIS_ARN = 'AWS_LAMBDA_BLOOD_PRESSURE_ANALYSIS_ARN'

    # ------------------------------
    # array of available secret codes
    # first is local in .env, second is in aws secrets managers
    SECRET_CODES = {
        'healthie' : {
            'organization'  : ( 'HEALTHIE_ORGANIZATION', 'healthieOrganization'  ),
            'api_key'       : ( 'HEALTHIE_API_KEY',      'healthieApiKey'        ),
        },
        'healthie_ids' : {
            'excluded_patients' : ( 'HEALTHIE_EXCLUDED_PATIENTS',  'excluded_patients'),
            'messenger_id'  : ( 'HEALTHIE_MESSENGER',  'messenger_id'),
            'clinicians'    : ( 'HEALTHIE_CLINICIANS',  'clinicians'),
            'physicians'    : ( 'HEALTHIE_PHYSICIANS',  'physicians'),
            'patient_dashboard_ids' : ( 'HEALTHIE_PATIENT_DASHBOARD_IDS', 'patient_dashboard_ids')
        },
        'tenovi_hwi' : {
            'client_domain' : ( 'TENOVI_CLIENT_DOMAIN',  'tenoviHwiClientDomain' ),
            'api_key'       : ( 'TENOVI_API_KEY',        'tenoviHwiApiKey'       ),
        },
        'openai' : {
            'api_key'       : ( 'OPENAI_API_KEY',        'openAiApiKey'          ),
        },
        'aws_database' : {
            'host'          : ( 'AWS_DATABASE_CONFIG_HOST',        'host' ),
            'user'          : ( 'AWS_DATABASE_CONFIG_USER',        'username' ),
            'password'      : ( 'AWS_DATABASE_CONFIG_PASSWORD',    'password' ),
            'local_port'    : ( 'AWS_DATABASE_CONFIG_LOCAL_PORT',  None ),
        },
        'candid' : {
            'client_id'       : ( 'CANDID_CLIENT_ID',        'client_id'       ),
            'client_secret'   : ( 'CANDID_CLIENT_SECRET',    'client_secret'   ),
            'candid_api'      : ( 'CANDID_API',              'candid_api'      ),
            'pre_encounter'   : ( 'CANDID_PRE_ENCOUNTER',    'pre_encounter'   ),
        },
    }

    # ------------------------------
    # hidden class constants

    # default path to the .env file, at the root of the repository
    _DEFAULT_DOTENV_PATH = ".env"

    # Pythonanywhere identification file path
    _PYTHON_ANYWHERE_ID_PATH = '/home/syntrillo/_this_is_PythonAnywhere_'

    # In pythonanywhere, the .env file is located in the home directory, and has to be specified manually
    _PYTHON_ANYWHERE_DOTENV_PATH = '/home/syntrillo/Syntrillo_Clinic/.env'

    # ------------------------------
    def __init__(
        self,
        load_aws_database_secrets: bool = False,
        load_healthie_secrets: bool = False,
        load_healthie_ids_secrets: bool = False,
        load_tenovi_hwi_secrets: bool = False,
        load_openai_secrets: bool = False,
        load_candid_secrets: bool = False,
        ) -> None:
        """
        Initializes the GetLocalSecrets class.
        """

        # ------------------------------
        # init class attributes
        self._is_lambda = False
        self._is_pythonanywhere = False
        self._is_local = False
        self._dotenv_path = None

        # names below have to match the ones in the SECRET_CODES
        self._aws_database_secrets = None
        self._healthie_secrets = None
        self._healthie_ids_secrets = None
        self._tenovi_hwi_secrets = None
        self._openai_secrets = None

        try:
            # ------------------------------
            # determine the environment where the code is running
            if (os.getenv(self.AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_CANDID_SECRET_ARN) != None
            ):
                # If this test passes, it means we are in the lambda function
                self._is_lambda = True
            elif os.path.exists(self._PYTHON_ANYWHERE_ID_PATH):
                # If this test passes, it means we are in PythonAnywhere
                self._is_pythonanywhere = True
                self._dotenv_path = self._PYTHON_ANYWHERE_DOTENV_PATH
            else:
                # If none of the above tests pass, it means we are running locally
                self._is_local = True
                self._dotenv_path = self._DEFAULT_DOTENV_PATH

            # ------------------------------
            # load the environment variables if needed
            if self._is_local or self._is_pythonanywhere:
                load_dotenv(dotenv_path=self._dotenv_path)

            elif self._is_lambda:
                if load_aws_database_secrets:
                    self._aws_database_secrets = self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN))

                if load_healthie_secrets:
                    self._healthie_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN))

                if load_healthie_ids_secrets:
                    self._healthie_ids_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN))

                if load_tenovi_hwi_secrets:
                    self._tenovi_hwi_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN))

                if load_openai_secrets:
                    self._openai_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN))

                if load_candid_secrets:
                    self._candid_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_CANDID_SECRET_ARN))

        except Exception as e:
            # Handle exceptions related to the initialization of the class
            raise Exception(f"Error initializing GetLocalSecrets: {e}")

    @staticmethod
    def get_secrets(secret_arn : str) -> dict:
        try:
            get_secret_value_response = requests.get(
                f"http://localhost:2773/secretsmanager/get?secretId={secret_arn}",
                headers={"X-AWS-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')},
            )
            get_secret_value_response.raise_for_status()  # Raise an exception for non-2xx status codes
        except requests.exceptions.RequestException as e:
            # Handle exceptions related to the HTTP request
            # if "an unexpected error occurred while executing request" in the response text => check lammbda permissions to read in secrets manager
            raise Exception(f"Error fetching secret [{get_secret_value_response.text}]: {e}")

        try:
            secret_value = get_secret_value_response.text
            secret_dict = json.loads(secret_value)
        except json.JSONDecodeError as e:
            # Handle exceptions related to JSON decoding
            raise Exception(f"Error decoding secret value [{get_secret_value_response.text}]: {e}")

        try:
            secrets_string = secret_dict["SecretString"]
        except KeyError as e:
            # Handle exceptions related to missing "SecretString" key
            raise Exception(f"Error retrieving SecretString: {e}")

        try:
            secrets_dict=json.loads(secrets_string)
            return secrets_dict
        except json.JSONDecodeError as e:
            # Handle exceptions related to not well formated secret string (non json)
            raise Exception(f"Error decoding secrets (should be in json format in aws secrets manager): {e}")

    def get_secret_value(self, group, variable) :
        """
        Retrieves the secret from the specified group and variable name based on the environment.
        """

        # init
        secret_value = None

        # get the secret code
        try:
            secret_code = self.SECRET_CODES[group][variable]
        except KeyError as e:
            # raise an exception if the secret is not found
            raise Exception(f"Secret not found : {group}, {variable} : {e}")

        # get the secret based on the environment
        if self._is_local or self._is_pythonanywhere:
            secret_value = os.getenv(secret_code[0])
            if not secret_value:
                raise Exception(f"Secret not found: {secret_code[0]}")

        elif self._is_lambda:
            secrets = getattr(self, f"_{group}_secrets")
            secret_value = secrets.get(secret_code[1])
            if not secret_value:
                raise Exception(f"Secret not found: {secret_code[1]} in group {group}")

        else:
            # raise an exception if the environment is not recognized
            raise Exception(f"Unknown environment")

        return secret_value

    # ------------------------------
    # methods to get the secrets
    def get_healthie_organization(self):
        return self.get_secret_value('healthie', 'organization')

    def get_healthie_api_key(self):
        return self.get_secret_value('healthie', 'api_key')

    def get_tenovi_hwi_client_domain(self):
        return self.get_secret_value('tenovi_hwi', 'client_domain')

    def get_tenovi_hwi_api_key(self):
        return self.get_secret_value('tenovi_hwi', 'api_key')

    def get_aws_database_host(self):
        return self.get_secret_value('aws_database', 'host')

    def get_aws_database_user(self):
        return self.get_secret_value('aws_database', 'user')

    def get_aws_database_password(self):
        return self.get_secret_value('aws_database', 'password')

    def get_aws_database_local_port(self):
        return self.get_secret_value('aws_database', 'local_port')

    def get_openai_api_key(self):
        return self.get_secret_value('openai', 'api_key')

    # ------------------------------
    # Are we in a production environment
    def is_production(self):
        return self.get_healthie_organization() == 'production'

    # Are we in a staging environment
    def is_staging(self):
        return self.get_healthie_organization() == 'staging'

    # Are we in a local environment
    def is_local(self):
        return self._is_local

    # Are we in a lambda environment
    def is_lambda(self):
        return self._is_lambda

    # Are we in a pythonanywhere environment
    def is_pythonanywhere(self):
        return self._is_pythonanywhere

    # ------------------------------
    # some other methods
    def get_healthie_full_platform_name(self):
        """
        Returns the full platform name for Healthie. Either:
            - 'healthie_production'
            - 'healthie_staging'
        """
        return 'healthie_' + self.get_healthie_organization()


if __name__ == '__main__':
    # test the class
    secrets = LocalEnvironmentAndSecrets(
        load_aws_database_secrets=True,
        load_healthie_secrets=True,
        load_healthie_ids_secrets=True,
        load_tenovi_hwi_secrets=True,
        load_openai_secrets=True,
        load_candid_secrets=True,
    )

    # get the secrets
    healthie_api_key = secrets.get_secret_value('healthie', 'api_key')
    healthie_organization = secrets.get_secret_value('healthie', 'organization')
    healthie_excluded_patients = secrets.get_secret_value('healthie', 'excluded_patients')
    healthie_messenger_id = secrets.get_secret_value('healthie', 'messenger_id')
    healthie_clinicians = secrets.get_secret_value('healthie', 'clinicians')

    tenovi_api_key = secrets.get_secret_value('tenovi_hwi', 'api_key')
    tenovi_client_domain = secrets.get_secret_value('tenovi_hwi', 'client_domain')

    aws_database_host = secrets.get_secret_value('aws_database', 'host')
    aws_database_user = secrets.get_secret_value('aws_database', 'user')
    aws_database_password = secrets.get_secret_value('aws_database', 'password')
    aws_database_port = secrets.get_secret_value('aws_database', 'local_port')

    openai_api_key = secrets.get_secret_value('openai', 'api_key')

    candid_client_id = secrets.get_secret_value('candid', 'client_id')
    candid_client_secret = secrets.get_secret_value('candid', 'client_secret')
    candid_api = secrets.get_secret_value('candid', 'candid_api')
    candid_pre_encounter = secrets.get_secret_value('candid', 'pre_encounter')

    print("\n\nsecrets:")
    print(f"healthie_api_key : {healthie_api_key}")
    print(f"healthie_organization : {healthie_organization}")

    print(f"tenovi_api_key : {tenovi_api_key}")
    print(f"tenovi_client_domain : {tenovi_client_domain}")

    print(f"aws_database_host : {aws_database_host}")
    print(f"aws_database_user : {aws_database_user}")
    print(f"aws_database_password : {aws_database_password}")
    print(f"aws_database_port : {aws_database_port}")

    print(f"openai_api_key : {openai_api_key}")

    print("done")

    # should be available in the environment
    overide_uid = os.getenv('OVERDIDE_HEALTHIE_USER_ID')
    print(f"overide_uid : {overide_uid}")


class LocalEnvironmentAndSecretsNoCache:
    """
    This class delivers secrets (keys, passwords, etc.) from the local environment where the code is running.

    If running on AWS Lambda, it retrieves secrets from AWS Secrets Manager.

    If running a personal PC, it retrieves secrets from the .env file located in the root of the repository.

    If running on PythonAnywhere, it retrieves secrets from a .env file located in a specific directory.

    Each secret is accessed by calling the appropriate method.

    """

    # ------------------------------
    # AWS env variables with ARNs (so that they are not hard coded below)
    AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN = 'AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN'
    AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN = 'AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN'
    AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN = 'AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN'
    AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN = 'AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN'
    AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN = 'AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN'
    AWS_SECRETS_MANAGER_CANDID_SECRET_ARN = 'AWS_SECRETS_MANAGER_CANDID_SECRET_ARN'
    # ------------------------------
    # array of available secret codes
    # first is local in .env, second is in aws secrets managers
    SECRET_CODES = {
        'healthie' : {
            'organization'  : ( 'HEALTHIE_ORGANIZATION', 'healthieOrganization'  ),
            'api_key'       : ( 'HEALTHIE_API_KEY',      'healthieApiKey'        ),
        },
        'healthie_ids' : {
            'excluded_patients' : ( 'HEALTHIE_EXCLUDED_PATIENTS',  'excluded_patients'),
            'messenger_id'  : ( 'HEALTHIE_MESSENGER',  'messenger_id'),
            'clinicians'    : ( 'HEALTHIE_CLINICIANS',  'clinicians'),
            'physicians'    : ( 'HEALTHIE_PHYSICIANS',  'physicians'),
        },
        'tenovi_hwi' : {
            'client_domain' : ( 'TENOVI_CLIENT_DOMAIN',  'tenoviHwiClientDomain' ),
            'api_key'       : ( 'TENOVI_API_KEY',        'tenoviHwiApiKey'       ),
        },
        'openai' : {
            'api_key'       : ( 'OPENAI_API_KEY',        'openAiApiKey'          ),
        },
        'aws_database' : {
            'host'          : ( 'AWS_DATABASE_CONFIG_HOST',        'host' ),
            'user'          : ( 'AWS_DATABASE_CONFIG_USER',        'username' ),
            'password'      : ( 'AWS_DATABASE_CONFIG_PASSWORD',    'password' ),
            'local_port'    : ( 'AWS_DATABASE_CONFIG_LOCAL_PORT',  None ),
        },
    }

    # ------------------------------
    # hidden class constants

    # default path to the .env file, at the root of the repository
    _DEFAULT_DOTENV_PATH = ".env"

    # Pythonanywhere identification file path
    _PYTHON_ANYWHERE_ID_PATH = '/home/syntrillo/_this_is_PythonAnywhere_'

    # In pythonanywhere, the .env file is located in the home directory, and has to be specified manually
    _PYTHON_ANYWHERE_DOTENV_PATH = '/home/syntrillo/Syntrillo_Clinic/.env'

    # ------------------------------
    def __init__(
        self,
        load_aws_database_secrets: bool = False,
        load_healthie_secrets: bool = False,
        load_healthie_ids_secrets: bool = False,
        load_tenovi_hwi_secrets: bool = False,
        load_openai_secrets: bool = False,
        load_candid_secrets: bool = False,
        ) -> None:
        """
        Initializes the GetLocalSecrets class.
        """

        # ------------------------------
        # init class attributes
        self._is_lambda = False
        self._is_pythonanywhere = False
        self._is_local = False
        self._dotenv_path = None

        # names below have to match the ones in the SECRET_CODES
        self._aws_database_secrets = None
        self._healthie_secrets = None
        self._healthie_ids_secrets = None
        self._tenovi_hwi_secrets = None
        self._openai_secrets = None

        try:
            # ------------------------------
            # determine the environment where the code is running
            if (os.getenv(self.AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN) != None
                or os.getenv(self.AWS_SECRETS_MANAGER_CANDID_SECRET_ARN) != None
            ):
                # If this test passes, it means we are in the lambda function
                self._is_lambda = True
            elif os.path.exists(self._PYTHON_ANYWHERE_ID_PATH):
                # If this test passes, it means we are in PythonAnywhere
                self._is_pythonanywhere = True
                self._dotenv_path = self._PYTHON_ANYWHERE_DOTENV_PATH
            else:
                # If none of the above tests pass, it means we are running locally
                self._is_local = True
                self._dotenv_path = self._DEFAULT_DOTENV_PATH

            # ------------------------------
            # load the environment variables if needed
            if self._is_local or self._is_pythonanywhere:
                load_dotenv(dotenv_path=self._dotenv_path)

            elif self._is_lambda:
                if load_aws_database_secrets:
                    self._aws_database_secrets = self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN))

                if load_healthie_secrets:
                    self._healthie_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN))

                if load_healthie_ids_secrets:
                    self._healthie_ids_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN))

                if load_tenovi_hwi_secrets:
                    self._tenovi_hwi_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN))

                if load_openai_secrets:
                    self._openai_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN))

                if load_candid_secrets:
                    self._candid_secrets=self.get_secrets(os.getenv(self.AWS_SECRETS_MANAGER_CANDID_SECRET_ARN))

        except Exception as e:
            # Handle exceptions related to the initialization of the class
            raise Exception(f"Error initializing GetLocalSecrets: {e}")



    @staticmethod
    def get_secrets(secret_arn : str) -> dict:
        max_retries = 5
        wait_time = 0.0
        for attempt in range(max_retries):
            try:
                import boto3
                client = boto3.client('secretsmanager')
                get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
            except requests.exceptions.RequestException as e:
                print('attempt: ****', attempt)
                if attempt == max_retries - 1:
                    # Handle exceptions related to the HTTP request
                    # if "an unexpected error occurred while executing request" in the response text => check lammbda permissions to read in secrets manager
                    raise Exception(f"Error fetching secret [{get_secret_value_response.text}]: {e}")

                import time
                time.sleep(wait_time)
                wait_time *= 1  # Exponential backoff

        try:
            secret_dict = get_secret_value_response
            print(secret_dict)
        except json.JSONDecodeError as e:
            # Handle exceptions related to JSON decoding
            raise Exception(f"Error decoding secret value [{get_secret_value_response.text}]: {e}")

        try:
            secrets_string = secret_dict["SecretString"]
        except KeyError as e:
            # Handle exceptions related to missing "SecretString" key
            raise Exception(f"Error retrieving SecretString: {e}")

        try:
            secrets_dict=json.loads(secrets_string)
            return secrets_dict
        except json.JSONDecodeError as e:
            # Handle exceptions related to not well formated secret string (non json)
            raise Exception(f"Error decoding secrets (should be in json format in aws secrets manager): {e}")

    def get_secret_value(self, group, variable) :
        """
        Retrieves the secret from the specified group and variable name based on the environment.
        """

        # init
        secret_value = None

        # get the secret code
        try:
            secret_code = self.SECRET_CODES[group][variable]
        except KeyError as e:
            # raise an exception if the secret is not found
            raise Exception(f"Secret not found : {group}, {variable} : {e}")

        # get the secret based on the environment
        if self._is_local or self._is_pythonanywhere:
            secret_value = os.getenv(secret_code[0])
            if not secret_value:
                raise Exception(f"Secret not found: {secret_code[0]}")

        elif self._is_lambda:
            secrets = getattr(self, f"_{group}_secrets")
            secret_value = secrets.get(secret_code[1])
            if not secret_value:
                raise Exception(f"Secret not found: {secret_code[1]} in group {group}")

        else:
            # raise an exception if the environment is not recognized
            raise Exception(f"Unknown environment")

        return secret_value

    # ------------------------------
    # methods to get the secrets
    def get_healthie_organization(self):
        return self.get_secret_value('healthie', 'organization')

    def get_healthie_api_key(self):
        return self.get_secret_value('healthie', 'api_key')

    def get_tenovi_hwi_client_domain(self):
        return self.get_secret_value('tenovi_hwi', 'client_domain')

    def get_tenovi_hwi_api_key(self):
        return self.get_secret_value('tenovi_hwi', 'api_key')

    def get_aws_database_host(self):
        return self.get_secret_value('aws_database', 'host')

    def get_aws_database_user(self):
        return self.get_secret_value('aws_database', 'user')

    def get_aws_database_password(self):
        return self.get_secret_value('aws_database', 'password')

    def get_aws_database_local_port(self):
        return self.get_secret_value('aws_database', 'local_port')

    def get_openai_api_key(self):
        return self.get_secret_value('openai', 'api_key')

    # ------------------------------
    # Are we in a production environment
    def is_production(self):
        return self.get_healthie_organization() == 'production'

    # Are we in a staging environment
    def is_staging(self):
        return self.get_healthie_organization() == 'staging'

    # Are we in a local environment
    def is_local(self):
        return self._is_local

    # Are we in a lambda environment
    def is_lambda(self):
        return self._is_lambda

    # Are we in a pythonanywhere environment
    def is_pythonanywhere(self):
        return self._is_pythonanywhere

    # ------------------------------
    # some other methods
    def get_healthie_full_platform_name(self):
        """
        Returns the full platform name for Healthie. Either:
            - 'healthie_production'
            - 'healthie_staging'
        """
        return 'healthie_' + self.get_healthie_organization()


if __name__ == '__main__':
    # test the class
    secrets = LocalEnvironmentAndSecrets(
        load_aws_database_secrets=True,
        load_healthie_secrets=True,
        load_healthie_ids_secrets=True,
        load_tenovi_hwi_secrets=True,
        load_openai_secrets=True,
        load_candid_secrets=True,
        )

    # get the secrets
    healthie_api_key = secrets.get_secret_value('healthie', 'api_key')
    healthie_organization = secrets.get_secret_value('healthie', 'organization')
    healthie_excluded_patients = secrets.get_secret_value('healthie', 'excluded_patients')
    healthie_messenger_id = secrets.get_secret_value('healthie', 'messenger_id')
    healthie_clinicians = secrets.get_secret_value('healthie', 'clinicians')

    tenovi_api_key = secrets.get_secret_value('tenovi_hwi', 'api_key')
    tenovi_client_domain = secrets.get_secret_value('tenovi_hwi', 'client_domain')

    aws_database_host = secrets.get_secret_value('aws_database', 'host')
    aws_database_user = secrets.get_secret_value('aws_database', 'user')
    aws_database_password = secrets.get_secret_value('aws_database', 'password')
    aws_database_port = secrets.get_secret_value('aws_database', 'local_port')

    openai_api_key = secrets.get_secret_value('openai', 'api_key')

    candid_client_id = secrets.get_secret_value('candid', 'client_id')
    candid_client_secret = secrets.get_secret_value('candid', 'client_secret')
    candid_api = secrets.get_secret_value('candid', 'candid_api')
    candid_pre_encounter = secrets.get_secret_value('candid', 'pre_encounter')

    print("\n\nsecrets:")

    print(f"tenovi_api_key : {tenovi_api_key}")
    print(f"tenovi_client_domain : {tenovi_client_domain}")

    print(f"aws_database_host : {aws_database_host}")
    print(f"aws_database_user : {aws_database_user}")
    print(f"aws_database_password : {aws_database_password}")
    print(f"aws_database_port : {aws_database_port}")

    print(f"openai_api_key : {openai_api_key}")

    print("done")

    print(f"healthie_api_key : {healthie_api_key}")
    print(f"healthie_organization : {healthie_organization}")

    # should be available in the environment
    overide_uid = os.getenv('OVERDIDE_HEALTHIE_USER_ID')
    print(f"overide_uid : {overide_uid}")
