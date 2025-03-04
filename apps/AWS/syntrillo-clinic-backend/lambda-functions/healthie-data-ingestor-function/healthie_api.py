from typing import Optional

from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.system.logger import logger

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
    try:
        auth = HealthieAuth()
        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        json_response, log_response = auth.send_query(query, variables)
        logger.info(f"GraphQL log response: {log_response}")

        return json_response
    except Exception as e:
        logger.error(f"Error running GraphQL query: {e}")
        raise e