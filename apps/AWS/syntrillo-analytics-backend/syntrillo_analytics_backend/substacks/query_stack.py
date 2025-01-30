from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_glue as glue,
    aws_athena as athena,
    aws_s3 as s3,
)

class QueryStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.environment_name = self.environment_context["environment-name"]

        removal_policy_value = self.environment_context["storage"]["removal-policy"]
        self.removal_policy = RemovalPolicy[removal_policy_value]

        # Create Glue Database
        glue_database = glue.CfnDatabase(
            self, "SyntrilloAnalysisDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="syntrillo_analysis_db",
                # description="Database for transformed data"
            )
        )

        # creat athena result bucket
        athena_result_bucket = s3.Bucket(
            self, "SyntrilloAnalysisAthenaResultsBucket",
            bucket_name=f"{self.environment_name}.syntrillo-analytics.athena-results",
            removal_policy=self.removal_policy,
        )

        # Create Athena Workgroup
        athena_workgroup = athena.CfnWorkGroup(
            self, "SyntrilloAnalysisWorkGroup",
            name="syntrillo_analysis_workgroup",
            recursive_delete_option=True,
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                enforce_work_group_configuration=True,
                publish_cloud_watch_metrics_enabled=True,
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{athena_result_bucket.bucket_name}/output/"
                )
            )
        )

        # Define the columns for the table
        columns = [
            glue.CfnTable.ColumnProperty(
                name="operation",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="id",
                type="int"
            ),
            glue.CfnTable.ColumnProperty(
                name="syntrillo_internal_key",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="device_name",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="metric_name",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="value_1",
                type="float"
            ),
            glue.CfnTable.ColumnProperty(
                name="value_2",
                type="float"
            ),
            glue.CfnTable.ColumnProperty(
                name="timestamp_local",
                type="string"
            ),
            # glue.CfnTable.ColumnProperty(
            #     name="data_json",
            #     type="string"  # For JSON data
            #     #type="struct<metric:string,created:string,value_1:string,value_2:string,timestamp:string,dummy_data:boolean,patient_id:string,device_name:string,sensor_code:string,filter_params:struct<measurement_index:int>,hardware_uuid:string,hwi_device_id:string,timezone_offset:int,estimated_timestamp:boolean>"

            # ),
            glue.CfnTable.ColumnProperty(
                name="date",
                type="string"
            )
        ]

        # Create the Glue Table
        csv_table = glue.CfnTable(
            self, "TenoviRawMeasurementsTable",
            database_name=glue_database.ref,
            catalog_id=self.account,
            table_input=glue.CfnTable.TableInputProperty(
                name="tenovi_raw_measurements",
                # description="Sample CSV table",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "csv",
                    "skip.header.line.count": "0"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=f"s3://{self.environment_name}.syntrillo-analytics.raw-data/syntrillo$HealthInformation/tenovi_raw_measurements",
                    input_format="org.apache.hadoop.mapred.TextInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.serde2.OpenCSVSerde",
                        parameters={
                            "separatorChar": ",",
                            "quoteChar": '"',
                            "escapeChar": "\\"
                        }
                    )
                )
            )
        )


        # Define the Athena query to create a view
        trailing_three_month_view = (
            'CREATE OR REPLACE VIEW "trailing_three_month_view" AS'
            "\nSELECT"
            "\nDATE_FORMAT(current_date, '%b-%Y') current_month"
            "\n, DATE_FORMAT(date_add('month', -1, current_date), '%b-%Y') previous_month"
            "\n, DATE_FORMAT(date_add('month', -2, current_date), '%b-%Y') two_months_ago"
        )

        # Create a named query in Athena
        athena.CfnNamedQuery(self, "CDKCreateTrailingThreeMonthsView",
            database="syntrillo_analysis_db",
            query_string=trailing_three_month_view,
            name="CDKCreateTrailingThreeMonthsView",
            work_group="syntrillo_analysis_workgroup"
        )

        bp_measurement_count_view = (
            "CREATE OR REPLACE VIEW bp_measurement_count_view AS"
            "\nWITH reference_date AS ("
            "\n    -- Using current_date to get today's date dynamically"
            "\n    -- This means the query will automatically use whatever date it is when the query runs"
            "\n    SELECT current_date AS date_value"
            "\n),"
            "\ndate_ranges AS ("
            "\n    SELECT"
            "\n        -- End date is now today's date, automatically updated whenever the query runs"
            "\n        date_value AS end_date,"
            "\n        -- Start of current month - truncates current date to first day of month"
            "\n        date_trunc('month', date_value) AS start_of_month,"
            "\n        -- Previous month start - goes back one month and finds its first day"
            "\n        date_trunc('month', date_add('month', -1, date_value)) AS start_of_prev_month,"
            "\n        -- Previous month end - finds last day of previous month"
            "\n        date_add('day', -1, date_trunc('month', date_value)) AS end_of_prev_month,"
            "\n        -- Two months ago start - goes back two months and finds its first day"
            "\n        date_trunc('month', date_add('month', -2, date_value)) AS start_of_two_months_ago,"
            "\n        -- Two months ago end - finds last day of two months ago"
            "\n        date_add('day', -1, date_trunc('month', date_add('month', -1, date_value))) AS end_of_two_months_ago"
            "\n    FROM reference_date"
            "\n),"
            "\nadjusted_timestamps AS ("
            "\n    SELECT"
            "\n        syntrillo_internal_key,"
            "\n        metric_name,"
            "\n        -- Extract just the date portion using substring"
            "\n        date(substr(timestamp_local, 1, 10)) AS adjusted_date"
            "\n    FROM syntrillo_analysis_db.tenovi_raw_measurements"
            "\n)"
            "\nSELECT"
            "\n    t.syntrillo_internal_key,"
            "\n    -- Calculating remaining measurements (out of 16)"
            "\n    GREATEST(16 - COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_month"
            "\n        AND t.adjusted_date <= dr.end_date"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END), 0) AS measurements_remaining,"
            "\n    -- Counting measurements for current month"
            "\n    COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_month"
            "\n        AND t.adjusted_date <= dr.end_date"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END) AS current_month_count,"
            "\n    -- Counting measurements for previous month"
            "\n    COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_prev_month"
            "\n        AND t.adjusted_date <= dr.end_of_prev_month"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END) AS one_month_ago_count,"
            "\n    -- Counting measurements for two months ago"
            "\n    COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_two_months_ago"
            "\n        AND t.adjusted_date <= dr.end_of_two_months_ago"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END) AS two_months_ago_count"
            "\nFROM"
            "\n    adjusted_timestamps t"
            "\nCROSS JOIN date_ranges dr"
            "\nWHERE"
            "\n    t.metric_name = 'blood_pressure'"
            "\n    AND t.adjusted_date >= dr.start_of_two_months_ago"
            "\n    AND t.adjusted_date <= dr.end_date"
            "\nGROUP BY"
            "\n    t.syntrillo_internal_key"
            "\nORDER BY"
            "\n    current_month_count DESC,"
            "\n    one_month_ago_count DESC,"
            "\n    two_months_ago_count DESC"
        )

        # Create a named query in Athena
        athena.CfnNamedQuery(self, "CDKCreateBPMeasurementCountView",
            database="syntrillo_analysis_db",
            query_string=bp_measurement_count_view,
            name="CDKCreateBPMeasurementCountView",
            work_group="syntrillo_analysis_workgroup"
        )