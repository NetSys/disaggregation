
//import com.google.common.primitives.UnsignedBytes
import org.apache.spark.SparkContext._
import org.apache.spark._
import org.apache.spark.{SparkConf, SparkContext}
import java.util.Comparator
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.BytesWritable;

object lexicographicComparator extends Comparator[Array[Byte]] with Serializable {
  def compare(k1: Array[Byte], k2: Array[Byte]): Int = {
    val l = math.min(k1.length, k2.length)
    var i = 0
    while (i < l) {
      if (k1(i) != k2(i))
        return (k1(i) & 0xff) - (k2(i) & 0xff)
      i += 1
    }
    k1.length - k2.length
  }
  
}

/**
 * An application that generates data according to the terasort spec and shuffles them.
 * This is a great example program to stress test Spark's shuffle mechanism.
 *
 * See http://sortbenchmark.org/
 */
object TeraSort {

//  implicit val caseInsensitiveOrdering = UnsignedBytes.lexicographicalComparator
  implicit val caseInsensitiveOrdering = lexicographicComparator

  def main(args: Array[String]) {

    if (args.length < 2) {
      println("usage:")
      println("DRIVER_MEMORY=[mem] bin/run-example terasort.TeraSort " +
        "[input-file] [output-file]")
      println(" ")
      println("example:")
      println("DRIVER_MEMORY=50g bin/run-example terasort.TeraSort " +
        "/home/myuser/terasort_in /home/myuser/terasort_out")
      System.exit(0)
    }

    // Process command line arguments
    val inputFile = args(0)
    val outputFile = args(1)

    val conf = new SparkConf()
      .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
      .setAppName(s"TeraSort")
    val sc = new SparkContext(conf)

    //val dataset = sc.newAPIHadoopFile[Array[Byte], Array[Byte], TeraInputFormat](inputFile)
    val dataset = sc.sequenceFile[NullWritable, BytesWritable](inputFile).map(_._2.get()).map( (a : Array[Byte]) => (a.slice(0,TeraInputFormat.KEY_LEN), a.slice(TeraInputFormat.KEY_LEN + 1, TeraInputFormat.KEY_LEN + TeraInputFormat.VALUE_LEN))   )
    val sorted = dataset.partitionBy(new TeraSortPartitioner(dataset.partitions.length)).sortByKey()
    //sorted.saveAsNewAPIHadoopFile[TeraOutputFormat](outputFile)
    sorted.map( (a : (Array[Byte], Array[Byte])) => a._1 ++ a._2).map(bytesArray => (NullWritable.get(), new BytesWritable(bytesArray)))
          .saveAsSequenceFile(outputFile)
  }
}
