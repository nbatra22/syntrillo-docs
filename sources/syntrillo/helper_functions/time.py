from datetime import datetime, timedelta
import pytz
import json
import pandas as pd
from typing import Tuple, List

# ------------------------------------------------------
# helper function to convert a timestamp to EST
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

# ------------------------------------------------------
# helper function to create date ranges
def create_date_ranges(
    from_date: datetime,
    to_date: datetime,
    delta: timedelta,
    range_name_prefix: str,
    extra_count: int = 0,
    previous_consecutive_range : dict = None
) -> List[dict]:
    """
    Create date ranges from a start date to an end date with a specified interval.

    Args:
        from_date (datetime): The start date of the period.
        to_date (datetime): The end date of the period.
        delta (timedelta): The length of each range.
        range_name_prefix (str): The prefix for each range name (e.g., 'Month', 'Week', 'Day').
        extra_count (int, optional): An additional number to add to the range count. Defaults to 0.

    Returns:
        List[dict]: A list of dictionaries, each containing:
            - 'from_date' (datetime): The start date of the range.
            - 'to_date' (datetime): The end date of the range.
            - 'range_name' (str): The name of the range.
    """
    # Align the start date to midnight to ensure even ranges
    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Align the end date to the end of the day to ensure even ranges
    to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    ranges = []
    current_start = from_date
    range_count = 1

    while current_start <= to_date:
        current_end = current_start + delta - timedelta(microseconds=1)
        if current_end > to_date:
            current_end = to_date

        range_name = f"{range_name_prefix} {range_count + extra_count}"

        ranges.append({
            'from_date': current_start,
            'to_date': current_end,
            'range_name': range_name,
            'previous_consecutive_range': previous_consecutive_range
        })

        previous_consecutive_range = {
            'from_date': current_start,
            'to_date': current_end,
            'range_name': range_name,
        }

        current_start = current_end + timedelta(microseconds=1)
        range_count += 1

    return ranges

# ------------------------------------------------------
# Helper function to get date ranges for reporting
def get_date_ranges_for_reporting(
    from_date: datetime,
    to_date: datetime,
    period: str = 'weekly',  # 'weekly' or 'monthly'
    last_ranges_unit: str = None,  # 'week', 'month', 'day' (default: 'week' for 'weekly', 'month' for 'monthly')
    use_total: bool = False,  # whether to use total days or weeks for range name
    add_entire_range: bool = False,  # whether to add a range for the entire period at the beginning
    entire_range_label: str = 'Entire range',  # name for the whole period range
    max_number_of_rows: int = 8  # max number of rows in the output (not counting the entire range)
) -> Tuple[pd.DataFrame, dict]:
    """
    Creates a dataframe with date ranges for the requested period.

    Args:
        from_date (datetime): Start date of the period.
        to_date (datetime): End date of the period.
        period (str): 'weekly' or 'monthly' to define the period for the ranges.
        last_ranges_unit (str): Defines how to handle the last ranges: 'month', 'week', 'day'.
                               Defaults to 'week' for 'weekly' and 'month' for 'monthly'.
                               Examples:
                                 - 'weekly' period with 'week' last_ranges_unit: Remaining days grouped as a single range.
                                 - 'weekly' period with 'day' last_ranges_unit: Remaining days as individual ranges.
                                 - 'monthly' period with 'month' last_ranges_unit: Remaining days grouped as a single range.
                                 - 'monthly' period with 'week' last_ranges_unit: Remaining days grouped in weeks.
                                 - 'monthly' period with 'day' last_ranges_unit: Remaining days as individual ranges.
        use_total (bool): Whether to use total days or weeks for range names.
        add_entire_range (bool): Whether to add a range for the entire period at the beginning.
        entire_range_label (str): Name for the entire period range.
        max_number_of_rows (int): Maximum number of rows in the output (not counting the entire range).
                                  If the number of ranges exceeds this value, the first ranges will be collapsed

    Returns:
        Tuple (pd.DataFrame, dict):
            - pd.DataFrame: Dataframe with 'from_date', 'to_date', and 'range_name' columns.
            - dict: Log with 'success' and 'message' keys.
    """

    # ------------------------------------------------------
    # Determine default value for last_ranges_unit
    if last_ranges_unit is None:
        last_ranges_unit = 'week' if period == 'weekly' else 'month'

    # Validate last_ranges_unit
    if last_ranges_unit not in ['week', 'month', 'day']:
        log = {
            'success': False,
            'message': 'Invalid last_ranges_unit',
        }
        return None, log

    # Validate period
    if period not in ['weekly', 'monthly']:
        log = {
            'success': False,
            'message': 'Invalid period',
        }
        return None, log

    # Convert dates from string to datetime if necessary
    if not isinstance(from_date, datetime) or not isinstance(to_date, datetime):
        try:
            from_date = datetime.fromisoformat(from_date)
            to_date = datetime.fromisoformat(to_date)
        except ValueError:
            log = {
                'success': False,
                'message': 'Invalid date format',
            }
            return None, log

    # Ensure from_date is before to_date
    if from_date > to_date:
        log = {
            'success': False,
            'message': 'from_date is after to_date',
        }
        return None, log

    # ------------------------------------------------------
    # Align from_date to the start of the day
    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Align to_date to the end of the day
    to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # ------------------------------------------------------
    # Main logic for creating ranges
    date_ranges = []

    # row id to collapse from
    collapse_from_row : int = 0

    # Add a range for the entire period if requested
    if add_entire_range:
        date_ranges.append({
            'from_date': from_date,
            'to_date': to_date,
            'range_name': entire_range_label,
            'previous_consecutive_range': None
        })
        if max_number_of_rows is not None:
            # this entire range row at the top does not count towards the max_number_of_rows
            max_number_of_rows += 1
            collapse_from_row = 1

    # Create ranges based on the period
    if period == 'weekly':
        date_ranges_periods = create_date_ranges(from_date, to_date, timedelta(weeks=1), 'Week')
    elif period == 'monthly':
        date_ranges_periods = create_date_ranges(from_date, to_date, timedelta(days=30), 'Month')

    date_ranges.extend(date_ranges_periods)

    # ------------------------------------------------------
    # Handle the last range according to last_ranges_unit
    if date_ranges and last_ranges_unit != period[:-2]:
        last_range = date_ranges.pop()
        last_from = last_range['from_date']
        last_to = last_range['to_date']

        # get last range label if use_total is False
        if use_total:
            last_range_label = ""
        else:
            last_range_label = last_range['range_name'] + ' - '

        # previous_consecutive_range is the last in date_ranges, unless special case of whole period
        previous_consecutive_range = date_ranges[-1]
        if previous_consecutive_range['range_name'] == entire_range_label:
            previous_consecutive_range = None

        if last_ranges_unit == 'week':
            extra_count = (to_date - from_date).days // 7 if use_total else 0
            date_ranges.extend(create_date_ranges(last_from, last_to, timedelta(weeks=1), last_range_label + 'Week',
                                                  extra_count=extra_count, previous_consecutive_range=previous_consecutive_range))

        elif last_ranges_unit == 'day':
            extra_count = (to_date - from_date).days if use_total else 0
            date_ranges.extend(create_date_ranges(last_from, last_to, timedelta(days=1), last_range_label + 'Day',
                                                  extra_count=extra_count, previous_consecutive_range=previous_consecutive_range))

    # ------------------------------------------------------
    # Handle the maximum number of rows
    if max_number_of_rows is not None and len(date_ranges) > max_number_of_rows:
        # Determine how many ranges to collapse at the top
        num_to_collapse = len(date_ranges) - max_number_of_rows + 2  # +2 to account for the entire range and the last range

        # Collapse the top ranges
        collapsed_from_date = date_ranges[collapse_from_row]['from_date']
        collapsed_to_date = date_ranges[num_to_collapse - 1]['to_date']
        collapsed_range_name = f"{date_ranges[collapse_from_row]['range_name']} to {date_ranges[num_to_collapse - 1]['range_name']}"

        # Create the collapsed range
        collapsed_range = {
            'from_date': collapsed_from_date,
            'to_date': collapsed_to_date,
            'range_name': collapsed_range_name,
            'previous_consecutive_range': None
        }

        # Update date_ranges with the collapsed range
        if collapse_from_row == 0:
            date_ranges = [collapsed_range] + date_ranges[num_to_collapse:]
        else:
            date_ranges = date_ranges[:collapse_from_row] + [collapsed_range] + date_ranges[num_to_collapse:]


    # ------------------------------------------------------
    # Create DataFrame from ranges
    df = pd.DataFrame(date_ranges)
    df['from_date'] = pd.to_datetime(df['from_date'])
    df['to_date'] = pd.to_datetime(df['to_date'])
    df['range_name'] = df['range_name'].astype(str)

    # Log success
    log = {
        'success': True,
        'message': 'Date ranges created successfully',
    }

    return df, log


# ------------------------------------------------------
# tests

if __name__ == '__main__':

    # Test 1: Convert to EST
    print("\nTest 1: Convert to EST")
    print(convert_to_est('2022-01-01T12:00:00'))
    print(convert_to_est('2022-01-01T12:00:00', '%Y-%m-%d %H:%M:%S'))

    # Test 2: Create date ranges
    print("\nTest 2: Create date ranges")
    from_date = datetime(2022, 1, 1)
    to_date = datetime(2022, 1, 31)
    delta = timedelta(weeks=1)
    ranges = create_date_ranges(from_date, to_date, delta, 'Week')
    print(json.dumps(ranges, default=str, indent=2))

    # Test 3: Get date ranges for reporting
    print("\nTest 3: Get date ranges for reporting")
    from_date = datetime(2024, 6, 19)
    to_date = datetime(2024, 7, 9)
    period = 'monthly'
    last_ranges_unit = 'week'
    use_total = False
    add_entire_range = True
    date_ranges_df, log = get_date_ranges_for_reporting(
        from_date,
        to_date,
        period,
        last_ranges_unit,
        use_total,
        add_entire_range,
        entire_range_label='Entire Time',
        max_number_of_rows=8,
        )
    print(date_ranges_df)


