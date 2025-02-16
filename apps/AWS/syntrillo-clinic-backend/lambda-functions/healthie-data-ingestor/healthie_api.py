from typing import Optional

from syntrillo.api_healthie.auth import HealthieAuth

def run_graphql_query(
    query: str,
    variables: Optional[dict] = {}
) -> dict:
    """
    Runs the given GraphQL query against Healthie's backend
    Args:
        query (str): The GraphQL query to run
        variables (dict): Optional, the variables to pass to the query
    Returns:
        dict: The JSON response 'data' from the API.
    """
    auth = HealthieAuth()
    # Make the GraphQL query request using the send_query method inherited from HealthieAPI
    json_response, log_response = auth.send_query(query, variables)

    # TODO: replace this with proper logging.
    # Need to check how logging works when running inside the AWS Lambda runtime
    print(log_response)

    return json_response