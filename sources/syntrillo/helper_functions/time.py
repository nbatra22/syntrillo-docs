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
    ) -> List[dict]:
    """
    Create date ranges from a start date to an end date with a given delta.

    Args:
         - from_date: datetime object, beginning of the period
         - to_date: datetime object, end of the period
         - delta: timedelta object, the length of each range
         - range_name_prefix: str, the prefix for the range name : Month, Week, Day
         - extra_count : number to add to the range count

    Returns:
        List[dict]: a list of dictionaries with the following keys
            - from_date: datetime object, beginning of the range
            - to_date: datetime object, end of the range
            - range_name: str, the name of the range

    """
    # force from_date to be at midnight to have even ranges
    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # force to_date to be at 23:59:59 to have even ranges
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
            'range_name': range_name
        })

        current_start = current_end + timedelta(microseconds=1)
        range_count += 1

    return ranges

# ------------------------------------------------------
# Helper function to get date ranges for reporting
def get_date_ranges_for_reporting(
    from_date: datetime,
    to_date: datetime,
    period: str = 'weekly', # or monthly
    last_ranges_unit : str = None, # 'week', or 'month', or 'day' (None will default to 'week' for weekly and 'month' for monthly)
    use_total: bool = False, # whether to use total days or weeks for range name
    add_whole_range: bool = False, # whether to add a range for the whole period at the begining of the dataframe
    whole_period_name: str = 'Whole Period', # name for the whole period range
    ) -> Tuple[ pd.DataFrame, dict ]:
    """
    delivers a dataframe with the date ranges for the period requested

    Args:
       - from_date: datetime object, beginning of the period
       - to_date: datetime object, end of the period
       - period: str, 'weekly' or 'monthly' : the period for the ranges
       - last_ranges_unit: str, 'month' or 'week' or 'day' : defines how to handle the last ranges. None will default to 'week' for weekly and 'month' for monthly
            For example:
            - if period is weekly and last_ranges_unit is 'week', the last range will be a single row with the remaining days (less than 7)  (default)
            - if period is weekly and last_ranges_unit is 'day', the last ranges will be several days ranges with 1 day each
            - if period is monthly and last_ranges_unit is 'month', the last range will be a single row with the remaining days (less than 30) (default)
            - if period is monthly and last_ranges_unit is 'week', the last ranges will be several weeks ranges with 7 days each
            - if period is monthly and last_ranges_unit is 'day', the last ranges will be several days ranges with 1 day each
        - use_total: bool, whether to use total days or weeks for range name

    Returns a Tuple
       - pd.DataFrame: dataframe with
           - the date ranges, columns are 'from_date' and 'to_date', both datetime objects.
           - a meaningful name for the range, column 'range_name' : Month 1, Week 1, etc.
       - log: dict with the following keys: success, message

    """

    # ------------------------------------------------------
    # manage last_ranges_unit
    if last_ranges_unit is None:
        last_ranges_unit = 'week' if period == 'weekly' else 'month'

    # assert last_ranges_unit is valid
    if last_ranges_unit not in ['week', 'month', 'day']:
        log = {
            'success': False,
            'message': 'Invalid last_ranges_unit',
        }
        return None, log

    # assert period is valid
    if period not in ['weekly', 'monthly']:
        log = {
            'success': False,
            'message': 'Invalid period',
        }
        return None, log

    # if dates are not datetime objects, assume they are string with isoformat and convert them
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

    # assert from_date is before to_date
    if from_date > to_date:
        log = {
            'success': False,
            'message': 'from_date is after to_date',
        }
        return None, log

    # ------------------------------------------------------
    # force from_date to be at midnight to have even ranges
    from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # force to_date to be at 23:59:59 to have even ranges
    to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)


    # ------------------------------------------------------
    # main logic for creating ranges
    date_ranges = []

    # add a range for the whole period
    if add_whole_range:
        date_ranges.append({
            'from_date': from_date,
            'to_date': to_date,
            'range_name': whole_period_name
        })

    # create ranges for the period
    if period == 'weekly':
        date_ranges_periods = create_date_ranges(from_date, to_date, timedelta(weeks=1), 'Week')
    elif period == 'monthly':
        date_ranges_periods = create_date_ranges(from_date, to_date, timedelta(days=30), 'Month')

    date_ranges.extend(date_ranges_periods)

    # ------------------------------------------------------
    # handle the last range according to last_ranges_unit
    if date_ranges and last_ranges_unit != period[:-2]:
        last_range = date_ranges.pop()
        last_from = last_range['from_date']
        last_to = last_range['to_date']

        if last_ranges_unit == 'week':
            if use_total:
                # count number of weeks to add
                extra_count = (to_date - from_date).days // 7
            else:
                extra_count = 0

            date_ranges.extend(create_date_ranges(last_from, last_to, timedelta(weeks=1), 'Week', extra_count=extra_count))

        elif last_ranges_unit == 'day':
            if use_total:
                # count number of days to add
                extra_count = (to_date - from_date).days
            else:
                extra_count = 0

            date_ranges.extend(create_date_ranges(last_from, last_to, timedelta(days=1), 'Day', extra_count=extra_count))

    # create DataFrame from ranges, with specific columns types
    df= pd.DataFrame(date_ranges)
    df['from_date'] = pd.to_datetime(df['from_date'])
    df['to_date'] = pd.to_datetime(df['to_date'])
    df['range_name'] = df['range_name'].astype(str)

    # log success
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
    from_date = datetime(2022, 1, 1)
    to_date = datetime(2022, 2, 15)
    period = 'weekly'
    last_ranges_unit = 'week'
    use_total = True
    add_whole_range = True
    date_ranges_df, log = get_date_ranges_for_reporting(from_date, to_date, period, last_ranges_unit, use_total, add_whole_range)
    print(date_ranges_df)


