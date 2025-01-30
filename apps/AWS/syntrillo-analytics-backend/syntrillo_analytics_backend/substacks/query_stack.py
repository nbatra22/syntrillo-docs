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