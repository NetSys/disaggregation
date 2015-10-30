import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import org.apache.spark.sql._
//import org.apache.spark.sql.SQLContext.implicits._

case class Visit(sourceIP : String, destURL : String, visitDate : String, adRevenue : Double, userAgent : String, countryCode : String, languageCode : String, searchWord : String, duration : Int)

case class Ranking(pageURL : String, pageRank : Int, avgDuration : Int)


object SparkSql {
  def main(args: Array[String]) {
      args.foreach(println)
      val conf = new SparkConf().setAppName("SparkSql")
      val sc = new SparkContext(conf)
      val sqlCtx = new org.apache.spark.sql.SQLContext(sc)
      import sqlCtx.implicits._
      val visits = sc.textFile("/uservisits").map(_.split(",")).map(v => Visit(v(0), v(1), v(2), v(3).toDouble, v(4), v(5), v(6), v(7), v(8).toInt)).toDF()
      visits.registerTempTable("uservisits")
      val rankings = sc.textFile("/rankings").map(_.split(",")).map(r => Ranking(r(0), r(1).toInt, r(2).toInt)).toDF()
      rankings.registerTempTable("rankings")
      val result = sqlCtx.sql(args(1))
      result.rdd.saveAsTextFile(args(0))
  }
}


