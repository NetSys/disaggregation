from pyspark import SparkContext
from pyspark.sql import HiveContext

sc = SparkContext(appName = "Parquet Converter")
hiveContext = HiveContext(sc)
hiveContext.table("rankings").saveAsParquetFile("/user/spark/benchmark/rankings-parquet")
hiveContext.table("uservisits").saveAsParquetFile("/user/spark/benchmark/uservisits-parquet")
hiveContext.table("documents").saveAsParquetFile("/user/spark/benchmark/documents-parquet")
