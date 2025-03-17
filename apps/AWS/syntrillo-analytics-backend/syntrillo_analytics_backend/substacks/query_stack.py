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

        # ---------------------------------------------------------------------
        # TenoviRawMeasurementsTable
        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        # PIITable
        # ---------------------------------------------------------------------
        columns = [
            glue.CfnTable.ColumnProperty(
                name="syntrillo_internal_key",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="patient_name",
                type="string"
            ),
        ]

        # Create the Glue Table
        csv_table = glue.CfnTable(
            self, "PatientPIIDataTable",
            database_name=glue_database.ref,
            catalog_id=self.account,
            table_input=glue.CfnTable.TableInputProperty(
                name="patient_pii_data",
                # description="Sample CSV table",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "csv",
                    "skip.header.line.count": "0"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=f"s3://{self.environment_name}.syntrillo-analytics.pii-data/patient_piis/",
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

        # ---------------------------------------------------------------------
        # Healthie Form Template
        # ---------------------------------------------------------------------
        columns = [
            glue.CfnTable.ColumnProperty(
                name="operation",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="form_id",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="module_id",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="form_name",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="module_label",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="module_options",
                type="string"
            ),
        ]

        # Create the Glue Table
        csv_table = glue.CfnTable(
            self, "HealthieFormTemplatesTable",
            database_name=glue_database.ref,
            catalog_id=self.account,
            table_input=glue.CfnTable.TableInputProperty(
                name="healthie_form_templates",
                # description="Sample CSV table",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "csv",
                    "skip.header.line.count": "0"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=f"s3://{self.environment_name}.syntrillo-analytics.raw-data/syntrillo$HealthInformation/healthie_form_templates",
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

        # ---------------------------------------------------------------------
        # Healthie Form Template
        # ---------------------------------------------------------------------
        columns = [
            glue.CfnTable.ColumnProperty(
                name="operation",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="module_id",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="form_id",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="syntrillo_internal_key",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="answer",
                type="string"
            ),
            glue.CfnTable.ColumnProperty(
                name="created_at",
                type="string"
            ),
        ]

        # Create the Glue Table
        csv_table = glue.CfnTable(
            self, "HealthieFormResponsesTable",
            database_name=glue_database.ref,
            catalog_id=self.account,
            table_input=glue.CfnTable.TableInputProperty(
                name="healthie_form_responses",
                # description="Sample CSV table",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "csv",
                    "skip.header.line.count": "0"
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=f"s3://{self.environment_name}.syntrillo-analytics.raw-data/syntrillo$HealthInformation/healthie_form_responses",
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

        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------

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
            database=glue_database.ref,            
            query_string=trailing_three_month_view,
            name="CDKCreateTrailingThreeMonthsView",
            work_group=athena_workgroup.name
        ).node.add_dependency(athena_workgroup)
        
        trailing_three_month_view = (
            "CREATE OR REPLACE VIEW trailing_three_intervals_view AS"
            "\nWITH reference_date AS ("
            "\n    SELECT "
            "\n        DATE '2025-01-01' AS base_date,"
            "\n        current_date AS current_date_value,"
            "\n        -- Calculate how many complete 30-day intervals have passed since base date"
            "\n        floor(date_diff('day', DATE '2025-01-01', current_date) / 30) AS completed_intervals"
            "\n)"
            "\nSELECT"
            "\n    -- Current interval dates"
            "\n    date_format(date_add('day', (completed_intervals + 1) * 30 - 1, base_date), '%b-%d-%Y') AS end_current_date,"
            "\n    date_format(date_add('day', completed_intervals * 30, base_date), '%b-%d-%Y') AS start_current_date,"
            "\n    "
            "\n    -- Previous interval dates"
            "\n    date_format(date_add('day', completed_intervals * 30 - 1, base_date), '%b-%d-%Y') AS end_prev_date,"
            "\n    date_format(date_add('day', (completed_intervals - 1) * 30, base_date), '%b-%d-%Y') AS start_prev_date,"
            "\n    "
            "\n    -- Two intervals ago dates"
            "\n    date_format(date_add('day', (completed_intervals - 1) * 30 - 1, base_date), '%b-%d-%Y') AS end_two_ago_date,"
            "\n    date_format(date_add('day', (completed_intervals - 2) * 30, base_date), '%b-%d-%Y') AS start_two_ago_date"
            "\nFROM reference_date"
        )

        # Create a named query in Athena
        athena.CfnNamedQuery(self, "CDKCreateTrailingThreeIntervalView",
            database=glue_database.ref,
            query_string=trailing_three_month_view,
            name="CDKCreateTrailingThreeIntervalView",
            work_group=athena_workgroup.name
        ).node.add_dependency(athena_workgroup)

        bp_measurement_count_view = (
            "CREATE OR REPLACE VIEW bp_measurement_count_view AS"
            "\nWITH reference_date AS ("
            "\n    SELECT"
            "\n        DATE '2025-01-01' AS base_date,"
            "\n        current_date AS current_date_value,"
            "\n        floor(date_diff('day', DATE '2025-01-01', current_date) / 30) AS completed_intervals"
            "\n),"
            "\ndate_ranges AS ("
            "\n    SELECT"
            "\n        current_date_value AS end_date,"
            "\n        date_add('day', completed_intervals * 30, base_date) AS start_of_current,"
            "\n        date_add('day', (completed_intervals + 1) * 30 - 1, base_date) AS end_of_current,"
            "\n        date_add('day', (completed_intervals - 1) * 30, base_date) AS start_of_prev,"
            "\n        date_add('day', completed_intervals * 30 - 1, base_date) AS end_of_prev,"
            "\n        date_add('day', (completed_intervals - 2) * 30, base_date) AS start_of_two_ago,"
            "\n        date_add('day', (completed_intervals - 1) * 30 - 1, base_date) AS end_of_two_ago"
            "\n    FROM reference_date"
            "\n),"
            "\nadjusted_timestamps AS ("
            "\n    SELECT"
            "\n        lower(regexp_replace(t.syntrillo_internal_key, '(.{8})(.{4})(.{4})(.{4})(.{12})', '$1-$2-$3-$4-$5')) AS syntrillo_internal_key,"
            "\n        p.patient_name,"
            "\n        t.metric_name,"
            "\n        date(substr(t.timestamp_local, 1, 10)) AS adjusted_date,"
            "\n        CAST(t.value_1 AS DOUBLE) AS value_1"
            "\n    FROM syntrillo_analysis_db.tenovi_raw_measurements t"
            "\n    JOIN syntrillo_analysis_db.patient_pii_data p"
            "\n        ON p.syntrillo_internal_key = lower(regexp_replace(t.syntrillo_internal_key, '(.{8})(.{4})(.{4})(.{4})(.{12})', '$1-$2-$3-$4-$5'))"
            "\n)"
            "\nSELECT"
            "\n    t.patient_name,"
            "\n    GREATEST(16 - COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_current"
            "\n        AND t.adjusted_date <= dr.end_of_current"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END), 0) AS measurements_remaining,"
            "\n    COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_current"
            "\n        AND t.adjusted_date <= dr.end_of_current"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END) AS current_interval_count,"
            "\n    COALESCE(ROUND(AVG(CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_current"
            "\n        AND t.adjusted_date <= dr.end_of_current"
            "\n        THEN t.value_1"
            "\n    END), 1), 0) AS current_interval_SBP_avg,"
            "\n    COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_prev"
            "\n        AND t.adjusted_date <= dr.end_of_prev"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END) AS one_interval_ago_count,"
            "\n    COALESCE(ROUND(AVG(CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_prev"
            "\n        AND t.adjusted_date <= dr.end_of_prev"
            "\n        THEN t.value_1"
            "\n    END), 1), 0) AS one_interval_ago_SBP_avg,"
            "\n    COUNT(DISTINCT CASE"
            "\n        WHEN t.adjusted_date >= dr.start_of_two_ago"
            "\n        AND t.adjusted_date <= dr.end_of_two_ago"
            "\n        THEN date_format(t.adjusted_date, '%Y-%m-%d')"
            "\n    END) AS two_intervals_ago_count"
            "\nFROM"
            "\n    adjusted_timestamps t"
            "\nCROSS JOIN date_ranges dr"
            "\nWHERE"
            "\n    t.metric_name = 'blood_pressure'"
            "\n    AND t.adjusted_date >= dr.start_of_two_ago"
            "\n    AND t.adjusted_date <= dr.end_of_current"
            "\nGROUP BY"
            "\n    t.patient_name"
            "\nORDER BY"
            "\n    current_interval_count DESC,"
            "\n    one_interval_ago_count DESC,"
            "\n    two_intervals_ago_count DESC"
        )

        # Create a named query in Athena
        athena.CfnNamedQuery(self, "CDKCreateBPMeasurementCountView",
            database=glue_database.ref,
            query_string=bp_measurement_count_view,
            name="CDKCreateBPMeasurementCountView",
            work_group=athena_workgroup.name
        ).node.add_dependency(athena_workgroup)