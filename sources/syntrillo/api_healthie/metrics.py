# Path: ./sources/syntrillo/api_healthie/metrics.py

from datetime import datetime, timedelta
import random
from typing import Tuple

from syntrillo.api_healthie.auth import HealthieAuth


class HealthieMetrics():
    """
    A utility class for specific Healthie API interactions.


    """

    # names of the categories in Healthie > Settings > Journal Entries
    HEALTHIE_METRICS_BLOOD_PRESSURE_CATEGORY = "Blood Pressure"
    HEALTHIE_METRICS_PULSE_CATEGORY = "Pulse"

    HEALTHIE_METRICS_HOURS_OF_SLEEP_CATEGORY = "Hours of Sleep"
    HEALTHIE_METRICS_AVERAGE_PULSE_CATEGORY = "Average Pulse"
    HEALTHIE_METRICS_MAXIMUM_PULSE_CATEGORY = "Maximum Pulse"
    HEALTHIE_METRICS_TOTAL_STEPS_PER_DAY_CATEGORY = "Total Steps Per Day"


    def __init__(self):
        """
        Initializes the HealthieMetrics instance.
        """
        self.auth = HealthieAuth()


    def list_journal_entries(self):
        """
        Retrieve all entries using GraphQL query.

        https://docs.gethealthie.com/schema/entry.doc

        """

        # Set up the GraphQL query
        query = '''
            query entries(
                    $offset: Int,
                    $type: String,
                    $keywords: String,
                    $entry_id: String,
                    $category: String,
                    $client_id: String,
                    $is_org: Boolean,
                    $end_range: String,
                    $start_range: String,
                    $group_id: String,
                    $sort_by: String,
                    $end_datetime_range: String,
                    $start_datetime_range: String,
                    $summary_view: Boolean
                ) {
                    entries(
                        offset: $offset,
                        type: $type,
                        keywords: $keywords,
                        entry_id: $entry_id,
                        category: $category,
                        client_id: $client_id,
                        is_org: $is_org,
                        end_range: $end_range,
                        start_range: $start_range,
                        group_id: $group_id,
                        sort_by: $sort_by,
                        end_datetime_range: $end_datetime_range,
                        start_datetime_range: $start_datetime_range,
                        summary_view: $summary_view
                    ) {
                        id
                        type
                        added_by_user {
                            id
                        }
                        added_by_user_id
                        category
                        comments { # https://docs.gethealthie.com/schema/comment.doc
                            content
                            user_id
                        }
                        name
                        description
                        external_id             # Third party external ID associated with this entry
                        hide_from_main_feed     # A boolean to check if the entry should be hidden from the main client feed
                        image_url
                        metric_stat
                        metric_stat_string
                        has_subentries
                        subentries {
                            id
                            type
                            added_by_user_id
                            category
                            name
                            description
                            metric_stat
                            metric_stat_string
                        }
                    }
                }
        '''

        # Set up the GraphQL variables
        variables = {
            # 'offset': 0,  # Offset for pagination (if applicable)
            # Add other variables as needed
        }

        # Send the GraphQL query using the inherited send_query method
        response, log = self.auth.send_query(query, variables)

        return response, log


    def store_metric_data(
        self,
        user_id : str,
        metric_stat : str,
        entry_category : str,
        created_at : str,
    ) -> Tuple[dict, dict]:
        """

        This is just a peculiar Journal Entry type that stores a single metric value.

        https://docs.gethealthie.com/docs/#creating-an-entry

        https://docs.gethealthie.com/schema/createentryinput.doc

        https://docs.gethealthie.com/docs/#storing-metric-data

        Args:
            user_id (str): The user ID.
            metric_stat (str): The metric value.
            entry_category (str): The category of the metric data.
            created_at (datetime): The date and time the metric data was created.

        Returns a tupple:
            response (dict): The response from the API.
            log (dict): The log of the request.


        """
        # Set up the GraphQL mutation to create a CustomModule in a Form
        mutation = '''
            mutation createEntry (
            $metric_stat: String, # e.g "182"
            $category: String, # e.g "Weight"
            $type: String, # "MetricEntry"
            $user_id: String # e.g "61"
            $created_at: String, # e.g "2021-09-23 15:27:01 -0400"

            ) {
            createEntry (input:{
                category: $category,
                type: $type,
                metric_stat: $metric_stat,
                user_id: $user_id,
                created_at: $created_at,
            })
            {
                entry {
                id
                }
                messages
                {
                field
                message
                }
            }
            }
        '''

        # Set up the variables for the GraphQL mutation
        variables = {
            'type' : "MetricEntry",
            'category': entry_category,
            'metric_stat': metric_stat,
            'created_at': created_at,
            'user_id': user_id
        }

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(mutation, variables)
        return response, log

    def store_blood_pressure_data(
        self,
        user_id : str,
        systolic : str,
        diastolic : str,
        created_at : str  , # will be formated to string "2021-09-23 15:27:01 -0400"
        description : str = None,
    ) -> Tuple[dict, dict]:
        """

        https://docs.gethealthie.com/schema/subentryinput.doc


        Successfull response:
            {
                "createEntry": {
                    "entry": {
                        "id": "1269673"
                    },
                    "messages": null
                }
            }

        Args:
            user_id (str): The user ID.
            systolic (str): The systolic blood pressure value.
            diastolic (str): The diastolic blood pressure value.
            created_at (datetime): The date and time the metric data was created.
            description (str, optional): The description of the metric data.

        Returns a tupple:
            response (dict): The response from the API.
            log (dict): The log of the request.
        """

        # Convert systolic to a float if possible
        try:
            systolic_float = float(systolic)
        except ValueError:
            log = {
                'success': False,
                'error': "Systolic value must be a valid number."
            }
            return None, log

        # Convert diastolic to a float if possible
        try:
            diastolic_float = float(diastolic)
        except ValueError:
            log = {
                'success': False,
                'error': "Diastolic value must be a valid number."
            }
            return None, log

        # return an error if systolic or diastolic values are in not proper ranges : 10-300
        if not (10 <= systolic_float <= 300) or not (10 <= diastolic_float <= 300):
            log = {
                'success': False,
                'error': "Systolic and diastolic values must be between 10 and 300."
            }
            return None, log

        # return an error if systolic is less than diastolic
        if systolic_float <= diastolic_float:
            log = {
                'success': False,
                'error': "Systolic value must be greater than diastolic value."
            }
            return None, log

        # Set up the GraphQL mutation to create an entry with two subentries for systolic and diastolic blood pressure
        mutation = '''
            mutation createEntry (
                $systolic_metric_stat: String,
                $diastolic_metric_stat: String,
                $category: String,
                $type: String,
                $user_id: String
                $created_at: String,
                $description: String
            ) {
            createEntry (input:{
                category: $category,
                type: $type,
                user_id: $user_id,
                created_at: $created_at,
                description: $description,
                subentries : [
                    {
                        category: "Systolic Blood Pressure",
                        type: "MetricEntry",
                        metric_stat: $systolic_metric_stat,
                    },
                    {
                        category: "Diastolic Blood Pressure",
                        type: "MetricEntry",
                        metric_stat: $diastolic_metric_stat,
                    }
                ]
            })
            {
                entry {
                    id
                }
                messages
                {
                    field
                    message
                }
            }
            }
        '''

        # Set up the variables for the GraphQL mutation
        variables = {
            'type' : "MetricEntry",  # raises an internal server error if not set properly
            'category': "Blood Pressure",
            'user_id': user_id,
            'systolic_metric_stat': systolic,
            'diastolic_metric_stat': diastolic,
            'created_at': created_at,
            'description': description
        }

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(mutation, variables)

        return response, log

    def get_metric_data(
        self,
        user_id: str,
        category: str,
        start_date: datetime = None,
        end_date: datetime = None,
        ) -> Tuple[list, dict]:
        """
        Retrieve metric data for a user within a date range.

        Using OFFSET method, only one available in entries query, unfortunately not 100% reliable

        https://docs.gethealthie.com/docs/#storing-metric-data

        args:
            user_id (str): The user ID.
            category (str): The category of the metric data.
            start_date (datetime, optional): The start date of the date range.
            end_date (datetime, optional): The end date of the date range.

        returns a tuple:
            list: A list of metric data dictionaries.
            dict: The log of the request.
        """

        query = '''
            query entries(
                    $offset: Int,
                    $type: String,
                    $category: String,
                    $client_id: String,
                    $is_org: Boolean,
                    $end_range: String,
                    $start_range: String,
                    $end_datetime_range: String,
                    $start_datetime_range: String,
                ) {
                    entries(
                        offset: $offset,
                        type: $type,
                        category: $category,
                        client_id: $client_id,
                        is_org: $is_org,
                        end_range: $end_range,
                        start_range: $start_range,
                        end_datetime_range: $end_datetime_range,
                        start_datetime_range: $start_datetime_range,
                    ) {
                        id
                        type
                        category
                        name
                        description
                        metric_stat
                        metric_stat_string
                        created_at
                    }
                }
        '''

        all_entries = []
        offset = 0
        success = True

        while True:
            variables = {
                'type': "MetricEntry",
                'client_id': user_id,
                'category': category,
                'offset': offset,
                'start_range': start_date.isoformat() if start_date else None,
                'end_range': end_date.isoformat() if end_date else None
            }

            response, log = self.auth.send_query(query, variables)
            if log['success'] and response and 'entries' in response:
                entries = response['entries']
                if not entries:
                    break
                all_entries.extend(entries)
                offset += len(entries) # documentation says 10, but may be subject to change: hence using len(entries)
            else:
                success = False
                break

        combined_log = {
            'success': success,
            'message': 'Metric data retrieval completed' if success else 'Metric data retrieval failed',
            'total_entries': len(all_entries)
        }

        return all_entries, combined_log


    def get_metric_data__with_cursor(
        self,
        user_id: str,
        category: str,
        start_date: datetime = None,
        end_date: datetime = None,
        ) -> Tuple[list, dict]:
        """
        CURSOR PAGINATION NOT AVAILABLE IN entries QUERY
        https://docs.gethealthie.com/docs/#cursor-pagination

        Retrieve metric data for a user within a date range.

        https://docs.gethealthie.com/docs/#storing-metric-data

        args:
            user_id (str): The user ID.
            category (str): The category of the metric data.
            start_date (datetime, optional): The start date of the date range.
            end_date (datetime, optional): The end date of the date range.

        returns a tupple:
            list: A list of metric data dictionaries.
            dict: The log of the request.
        """

        query = '''
            query entries(
                    $after: Cursor,
                    $should_paginate: Boolean,
                    $page_size: Int,
                    $type: String,
                    $category: String,
                    $client_id: String,
                    $is_org: Boolean,
                    $end_range: String,
                    $start_range: String,
                    $end_datetime_range: String,
                    $start_datetime_range: String,
                ) {
                    entries(
                        should_paginate: $should_paginate,
                        after: $after,
                        page_size: $page_size,
                        type: $type,
                        category: $category,
                        client_id: $client_id,
                        is_org: $is_org,
                        end_range: $end_range,
                        start_range: $start_range,
                        end_datetime_range: $end_datetime_range,
                        start_datetime_range: $start_datetime_range,
                    ) {
                        id
                        type
                        category
                        name
                        description
                        metric_stat
                        metric_stat_string
                        created_at
                        cursor
                    }
                }
        '''

        all_entries = []
        cursor = None
        success = True

        while True:
            variables = {
                'after': cursor,
                'should_paginate': True,
                'page_size': 10,  # 10 is the maximum page size
                'type': "MetricEntry",
                'client_id': user_id,
                'category': category,
                'start_range': start_date.isoformat() if start_date else None,
                'end_range': end_date.isoformat() if end_date else None
            }

            response, log = self.auth.send_query(query, variables)
            if log['success'] and response and 'entries' in response:
                entries = response['entries']
                if not entries:
                    break
                all_entries.extend(entries)
                cursor = entries[-1]['cursor']  # Update cursor to the last entry's cursor for the next fetch
            else:
                success = False
                break

        combined_log = {
            'success': success,
            'message': 'Metric data retrieval completed' if success else 'Metric data retrieval failed',
            'total_entries': len(all_entries)
        }

        return all_entries, combined_log


    def get_metric_latest_timestamp(
        self,
        user_id: str,
        category: str,
        ) -> datetime:
        """
        Using the get_metric_data function, retrieve the latest timestamp of the metric data.

        This function moves back in time by 1 week until it finds the latest timestamp.

        It returns the latest timestamp of the metric data.

        Args:
            user_id (str): The user ID.
            category (str): The category of the metric data.

        Returns:
            latest_timestamp (datetime): The latest timestamp of the metric data, zulu time.


        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        i=0
        while True:
            entries, log = self.get_metric_data(user_id, category, start_date, end_date)
            if entries:
                latest_timestamp = max(entry['created_at'] for entry in entries)
                return datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S %z").strftime("%Y-%m-%dT%H:%M:%SZ")
            end_date = start_date
            start_date -= timedelta(days=7)
            i += 1
            if i > 50:
                return start_date.strftime("%Y-%m-%dT%H:%M:%SZ")


    def remove_metric_data(
        self,
        user_id: str,
        category: str,
        start_date: datetime = None,
        end_date: datetime = None,
        ) -> Tuple[dict, dict]:
        """
        Remove metric data entries for a user within a date range.

        Args:
            user_id (str): The user ID.
            category (str): The category of the metric data.
            start_date (datetime, optional): The start date of the date range. Default None
            end_date (datetime, optional): The end date of the date range. Default None

        Returns:
            log (dict): The log of the request. Contains the number of records deleted and success status.

        """

        overall_log = {
            "success": True,
            "number_of_records_deleted": 0,
            "logs": []
        }

        # have to get metric data first
        all_metrics, log = self.get_metric_data(user_id, category, start_date, end_date)

        overall_log['logs'].append(log)

        # then loop over entries and remove them
        number_of_records_deleted = 0
        for metric in all_metrics:
            entry_id = metric['id']
            mutation = '''
                mutation deleteEntry (
                    $id: ID
                ) {
                    deleteEntry (input:{
                        id: $id
                    })
                    {
                        entry {
                            id
                        }
                        messages
                        {
                            field
                            message
                        }
                    }
                }
                '''
            variables = {
                'id': entry_id
            }
            response, log = self.auth.send_query(mutation, variables)

            if not log['success']:
                overall_log['logs'].append(log)
                overall_log['success'] = False
                break

            number_of_records_deleted += 1

        overall_log['number_of_records_deleted'] = number_of_records_deleted

        return overall_log




if __name__ == "__main__":
    metrics = HealthieMetrics()
    entries, log = metrics.list_journal_entries()
    # HealthieAuth.print_pretty_json(entries)

    # Generate a random date within a range of today +/- 10 days
    today = datetime.now()
    start_date = today - timedelta(days=10)
    end_date = today + timedelta(days=10)
    random_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))

    if False:
        user_id = "1035117"
        for i in range(100):
            # Generate a random date within a range of today +/- 10 days
            # Get today's date
            today = datetime.now()

            # Generate a random number of days between -10 and 10
            random_days = random.randint(-10, 10)

            # Generate a random number of seconds within a day
            random_seconds = random.randint(0, 24*3600 - 1)

            # Calculate the random date by adding/subtracting the random number of days
            random_date = today + timedelta(days=random_days)

            # Calculate the random time within the day
            random_datetime = random_date + timedelta(seconds=random_seconds)

            metric_stat = str(random.randint(50, 120))
            entry_category = "Heart Rate"
            created_at = None
            response, log = metrics.store_metric_data(
                user_id=user_id,
                metric_stat=metric_stat,
                entry_category=entry_category,
                created_at=random_datetime,
                )
        HealthieAuth.print_pretty_json(log)

    if False:
        user_id = "1035117"
        metric_stat = str(random.randint(0, 20))
        entry_category = "test Larry metric"
        created_at = None
        response, log = metrics.store_metric_data(
            user_id=user_id,
            metric_stat=metric_stat,
            entry_category=entry_category,
            created_at=random_date,
            )
        HealthieAuth.print_pretty_json(log)
        HealthieAuth.print_pretty_json(response)

    if False:
        user_id = "1035117"
        systolic = str(random.randint(100, 200))
        diastolic = str(random.randint(50, 90))

        response, log = metrics.store_blood_pressure_data(
            user_id=user_id,
            systolic=systolic,
            diastolic=diastolic,
            created_at=random_date,
            )
        HealthieAuth.print_pretty_json(log)

    if False:
        user_id = "1035117"
        category = "Heart Rate"
        response, log = metrics.get_metric_data(
            user_id=user_id,
            category=category,
            )
        HealthieAuth.print_pretty_json(response)
        HealthieAuth.print_pretty_json(log)

    if False:
        user_id = "1035117"
        category = "Heart Rate"
        log = metrics.remove_metric_data(
            user_id=user_id,
            category=category,
            start_date=today - timedelta(days=60),
            end_date=today
        )
        HealthieAuth.print_pretty_json(log)


    # --------------------

    if False:
        user_id = "1051529"
        category = HealthieMetrics.HEALTHIE_METRICS_BLOOD_PRESSURE_CATEGORY
        # find latest timestamp
        latest_timestamp = metrics.get_metric_latest_timestamp(user_id, category)
        print(latest_timestamp)

    if True:
        user_id = "1051529"
        category = HealthieMetrics.HEALTHIE_METRICS_BLOOD_PRESSURE_CATEGORY
        log = metrics.remove_metric_data(
            user_id=user_id,
            category=category,
            start_date=today - timedelta(days=7),
            end_date=today
        )
        HealthieAuth.print_pretty_json(log)






