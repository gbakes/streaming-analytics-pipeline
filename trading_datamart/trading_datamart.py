import sys
import boto3
import json
import os
from datetime import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import lit


glue_client = boto3.client("glue")
sm_client = boto3.client("secretsmanager")

## @params: [JOB_NAME]
args = getResolvedOptions(
    sys.argv,
    [
        # "JOB_NAME",
        # "WORKFLOW_NAME",
        # "WORKFLOW_RUN_ID",
        "GLUE_GAMEPLAY_DB",
        "GLUE_PLAY_TABLE",
        # "SECRET_ID",
        # "RDS_INSTANCE",
    ],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# added this
job.init("test-job", args)
logger = glueContext.get_logger()

# workflow_name = args["WORKFLOW_NAME"]
# workflow_run_id = args["WORKFLOW_RUN_ID"]
# workflow_params = glue_client.get_workflow_run_properties(
#     Name=workflow_name, RunId=workflow_run_id
# )["RunProperties"]

# get params from EventBridge event
# archive_version = workflow_params["archive_version"]
# archive_status_id = workflow_params["archive_status_id"]
# from_ts = workflow_params["from_ts"]
# platform_instance = workflow_params["platform_instance"]

# Parse the timestamp string into a datetime object
#dt_object_from_ts = datetime.strptime(from_ts, "%Y-%m-%dT%H:%M:%S.%fZ")

# added this 
dt_object_from_ts = datetime(2024, 10, 18, 23, 00, 00, 00)

# Extract year, month, day, and hour
from_ts_year = dt_object_from_ts.year
from_ts_month = dt_object_from_ts.month
from_ts_day = dt_object_from_ts.day
from_ts_hour = dt_object_from_ts.hour

# glue information
glue_db_name = args["GLUE_GAMEPLAY_DB"]
glue_play_table = args["GLUE_PLAY_TABLE"]

# rds_instance = args["RDS_INSTANCE"]

#added this
platform_instance = '0401'

# predicates
predicate_filter_ymdhp_from_ts = f"year = {from_ts_year} and month = {from_ts_month} and day = {from_ts_day} and hour = {from_ts_hour} and platform = {platform_instance}"

# Retrieve credentials for Postgres Trading Datamart
# get_secret_value_response = sm_client.get_secret_value(SecretId=args["SECRET_ID"])
# secret_dict = json.loads(get_secret_value_response["SecretString"])


def create_df(database, table, predicate):
    """
    Create a Glue DataFrame from tsv file
    """

    logger.info(f"Creating DataFrame for table {table} with predicate: {predicate}")

    dynamicframe = glueContext.create_dynamic_frame_from_catalog(
        database=database,
        table_name=table,
        push_down_predicate=predicate,
    )

    return dynamicframe.toDF()

def write_to_postgres(df):
    """
    Write aggregated dataframe into postgresql db
    """

    logger.info("Writing aggregated data to PostgreSQL")

    dyf = DynamicFrame.fromDF(df, glueContext, "grouped")

    # Added these

    secret_dict = {}
    secret_dict['username'] = os.environ['POSTGRES_USER']
    secret_dict['password'] =  os.environ['POSTGRES_PASSWORD']
    rds_instance = os.environ['POSTGRES_HOST']
    database_name = os.environ['POSTGRES_DB']

    glueContext.write_dynamic_frame_from_options(
        frame=dyf,
        connection_type="postgresql",
        connection_options={
            "user": secret_dict["username"],
            "password": secret_dict["password"],
            "url": "jdbc:postgresql://"
            + 'localdb'
            + ":"
            + "5432"
            + f"/{database_name}",
            "dbtable": "public." + 'trading',
        },
    )


query = "SELECT platform, date_trunc('hour', playmodifiedat) as hour, igpcode, gamecode, country, ccycode, mode, \
        \
        IF(useragent LIKE '%(KHTML, like Gecko) Mobile%', 'app', 'web') AS channel,\
        \
        jurisdiction, \
        NVL(maxstake, 0.00) as maxstake,\
        \
        count(distinct igpcode || '-' || playerid) as unique_players, \
        \
        sum(case when mode = 'real' and (isnull(bonusfundtype) or bonusfundtype = '') then 1 else 0 end) as num_rm_plays, \
        sum(case when mode = 'real' and (isnull(bonusfundtype) or bonusfundtype = '') then stake else 0.00 end) as rm_bet, \
        sum(case when mode = 'real' and (isnull(bonusfundtype) or bonusfundtype = '') then win else 0.00 end) as rm_win, \
        \
        sum(case when mode = 'demo' then 1 else 0 end) as num_dm_plays, \
        sum(case when mode = 'demo' then stake else 0.00 end) as dm_bet, \
        sum(case when mode = 'demo' then win else 0.00 end) as dm_win, \
        \
        sum(case when mode = 'real' and bonusfundtype = 'OPERATOR' then 1 else 0 end) as num_fr_op_plays, \
        sum(case when mode = 'real' and bonusfundtype = 'OPERATOR' then stake else 0.00 end) as fr_op_bet, \
        sum(case when mode = 'real' and bonusfundtype = 'OPERATOR' and isnotnull(cleardown) and cleardown != '' then cleardown else 0.00 end) as fr_op_win, \
        \
        sum(case when mode = 'real' and bonusfundtype = 'HIVE' then 1 else 0 end) as num_fr_rgs_plays, \
        sum(case when mode = 'real' and bonusfundtype = 'HIVE' then stake else 0.00 end) as fr_rgs_bet, \
        sum(case when mode = 'real' and bonusfundtype = 'HIVE' and isnotnull(cleardown) and cleardown != '' then cleardown else 0.00 end) as fr_rgs_win \
        \
        FROM play \
        WHERE status = 'FINISHED' \
        GROUP BY platform, date_trunc('hour', playmodifiedat), gamecode, igpcode, country, ccycode, mode, channel, jurisdiction, maxstake"


def run():
    """
    Run function
    """
    ####################################################################################################################
    # Preparation########################################################################################################

    # Create a dataframe
    df_play = create_df(glue_db_name, glue_play_table, predicate_filter_ymdhp_from_ts)

    if df_play.count() == 0:
        logger.error(
            f"No data found in partition with predicate: {predicate_filter_ymdhp_from_ts}"
        )
        return

    # Get columns names from the dataframe
    col_names = df_play.columns

    # Loop through the columns, if some are missing - insert them with null values
    for col in ["useragent", "clienttype", "ipaddress", "maxstake"]:
        if col not in col_names:
            df_play = df_play.withColumn(col, lit(None))

    # Create table to use it in a query
    df_play.createOrReplaceTempView("play")

    # Run the query and save the result in the dataframe
    df_agg = spark.sql(query)

    print(df_agg.printSchema())

    # Write data to the postgres db
    write_to_postgres(df_agg)

    logger.info(
        f"Job completed successfully for partition with predicate: {predicate_filter_ymdhp_from_ts}"
    )


run()

job.commit()