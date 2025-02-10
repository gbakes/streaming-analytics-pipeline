import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as SqlFuncs


class GlueLocalTest:
    def __init__(self):
        params = []
        if "--JOB_NAME" in sys.argv:
            params.append("JOB_NAME")
        args = getResolvedOptions(sys.argv, params)

        self.context = GlueContext(SparkContext.getOrCreate())
        self.job = Job(self.context)
        self.spark = self.context.spark_session

        if "JOB_NAME" in args:
            jobname = args["JOB_NAME"]
        else:
            jobname = "test"
        self.job.init(jobname, args)

    def run(self):
        dyf = read_json(
            self.context,
            "s3://awsglue-datasets/examples/us-legislators/all/persons.json",
        )
        dyf.printSchema()

        demo = self.context.create_dynamic_frame.from_options(
            format_options={},
            connection_type="s3",
            format="parquet",
            connection_options={
                "paths": [
                    "s3://archive-parquet-prod-dev/gameplay/v1/demo_txn/year=2022/month=5/day=11/hour=14/"
                ],
                "recurse": True,
            },
            transformation_ctx="demo",
        )

        demo_sel = SelectFields.apply(
            frame=demo,
            paths=["platformidentifier", "amount"],
            transformation_ctx="demo_sel",
        )

        demo_agg = sparkAggregate(
            self.context,
            parentFrame=demo_sel,
            groups=["platformidentifier"],
            aggs=[["amount", "sum"]],
            transformation_ctx="demo_agg",
        )

        demo_ren = RenameField.apply(
            frame=demo_agg,
            old_name="`sum(amount)`",
            new_name="total_amt",
            transformation_ctx="demo_ren",
        )

        demo_ren.printSchema()
        demo.toDF().show()

        self.job.commit()


def sparkAggregate(
    glueContext, parentFrame, groups, aggs, transformation_ctx
) -> DynamicFrame:
    aggsFuncs = []
    for column, func in aggs:
        aggsFuncs.append(getattr(SqlFuncs, func)(column))
        result = (
            parentFrame.toDF().groupBy(*groups).agg(*aggsFuncs)
            if len(groups) > 0
            else parentFrame.toDF().agg(*aggsFuncs)
        )
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)


def read_json(glue_context, path):
    dynamicframe = glue_context.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [path], "recurse": True},
        format="json",
    )
    return dynamicframe


GlueLocalTest().run()
