import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf

object WordCount {
  def main(args: Array[String]) {
      args.foreach(println)
      val conf = new SparkConf().setAppName("WordCount")
      val sc = new SparkContext(conf)
      val file = sc.textFile(args(0))
      val counts = file.flatMap(line => line.split(" "))
                       .map(word => (word, 1))
                       .reduceByKey(_ + _)
      counts.saveAsTextFile(args(1))
  }
}


