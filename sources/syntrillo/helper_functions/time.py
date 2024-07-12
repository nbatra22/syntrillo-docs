from datetime import datetime
import pytz

def convert_to_est(timestamp: str, date_format: str = '%Y-%m-%d %H:%M') -> str:
    """
    Convert a timestamp in ISO 8601 format to Eastern Standard Time (EST) and format it.

    Args:
    timestamp (str): The original timestamp in ISO 8601 format.
    date_format (str): The format for the output timestamp. Default is '%Y-%m-%d %H:%M'.

    Returns:
    str: The formatted timestamp in EST. Returns an empty string if input is invalid.
    """
    if timestamp:
        try:
            # Parse the original ISO 8601 timestamp
            original_time: datetime = datetime.fromisoformat(timestamp)

            # Define the EST timezone
            est = pytz.timezone('US/Eastern')

            # Check if the datetime is naive or aware
            if original_time.tzinfo is None:
                # If naive, localize to UTC first
                utc_time: datetime = pytz.utc.localize(original_time)
            else:
                # If aware, convert to UTC first
                utc_time: datetime = original_time.astimezone(pytz.utc)

            # Convert to EST
            est_time: datetime = utc_time.astimezone(est)

            # Format the EST time as per the provided date format
            formatted_time: str = est_time.strftime(date_format)
            return formatted_time
        except ValueError:
            # Handle invalid timestamp format
            return ''

    # Return an empty string if timestamp is not provided or is invalid
    return ''
