
//import com.google.common.primitives.Longs

import org.apache.spark.Partitioner

/**
 * Partitioner for terasort. It uses the first seven bytes of the byte array to partition
 * the key space evenly.
 */
case class TeraSortPartitioner(numPartitions: Int) extends Partitioner {

  import TeraSortPartitioner._

  val rangePerPart = (max - min) / numPartitions

  override def getPartition(key: Any): Int = {
    val b = key.asInstanceOf[Array[Byte]]
    val prefix = Longs.fromBytes(0, b(0), b(1), b(2), b(3), b(4), b(5), b(6))
    (prefix / rangePerPart).toInt
  }
}

object TeraSortPartitioner {
  val min = Longs.fromBytes(0, 0, 0, 0, 0, 0, 0, 0)
  val max = Longs.fromBytes(0, -1, -1, -1, -1, -1, -1, -1)  // 0xff = -1
}
