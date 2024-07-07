import lambda_functions.checking_function.handler as check

check.initiate_database_connection()

check.call_external_url()

check.clean_database()

check.display_database_content()

check.register_patient_devices()

check.display_database_content()

