# Path: ./sources/syntrillo/api_healthie/metrics.py

from syntrillo.api_healthie.auth import HealthieAuth
import datetime
import random

class HealthieMetrics():
    """
    A utility class for specific Healthie API interactions.


    """
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

        return response


    def store_metric_data(
        self,
        user_id : str,
        metric_stat : str,
        entry_category : str,
        created_at : datetime,
    ):
        """

        This is just a peculiar Journal Entry type that stores a single metric value.

        https://docs.gethealthie.com/docs/#creating-an-entry

        https://docs.gethealthie.com/schema/createentryinput.doc

        https://docs.gethealthie.com/docs/#storing-metric-data

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
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S %z")
        variables = {
            'type' : "MetricEntry",
            'category': entry_category,
            'metric_stat': metric_stat,
            'created_at': created_at_str,
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
        created_at : datetime  , # will be formated to string "2021-09-23 15:27:01 -0400"
        description : str = None,
    ):
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
        """

        # return an error if systolic or diastolic values are in not proper ranges : 10-300
        if not (10 <= int(systolic) <= 300) or not (10 <= int(diastolic) <= 300):
            log = {
                'success': False,
                'error': "Systolic and diastolic values must be between 10 and 300."
            }
            return None, log

        # return an error if systolic is less than diastolic
        if int(systolic) < int(diastolic):
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
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S %z")
        variables = {
            'type' : "MetricEntry",  # raises an internal server error if not set properly
            'category': "Blood Pressure",
            'user_id': user_id,
            'systolic_metric_stat': systolic,
            'diastolic_metric_stat': diastolic,
            'created_at': created_at_str,
            'description': description
        }

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(mutation, variables)

        return response, log



if __name__ == "__main__":
    metrics = HealthieMetrics()
    entries = metrics.list_journal_entries()
    # HealthieAuth.print_pretty_json(entries)

    # Generate a random date within a range of today +/- 10 days
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=10)
    end_date = today + datetime.timedelta(days=10)
    random_date = start_date + datetime.timedelta(days=random.randint(0, (end_date - start_date).days))

    if True:
        user_id = "1035117"
        metric_stat = str(random.randint(50, 120))
        entry_category = "Heart Rate"
        created_at = None
        response, log = metrics.store_metric_data(
            user_id=user_id,
            metric_stat=metric_stat,
            entry_category=entry_category,
            created_at=random_date,
            )
        HealthieAuth.print_pretty_json(log)

    if True:
        user_id = "1035117"
        metric_stat = str(random.randint(0, 20))
        entry_category = "StrokeRiskScore"
        created_at = None
        response, log = metrics.store_metric_data(
            user_id=user_id,
            metric_stat=metric_stat,
            entry_category=entry_category,
            created_at=random_date,
            )
        HealthieAuth.print_pretty_json(log)

    if True:
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

