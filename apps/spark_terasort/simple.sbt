name := "terasort"

version := "1.0"

scalaVersion := "2.10.4"

resolvers += "Akka Repository" at "http://repo.akka.io/releases/"
resolvers += "Spray Repository" at "http://repo.spray.cc/"
resolvers += "Scalaz Bintray Repo" at "http://dl.bintray.com/scalaz/releases"

libraryDependencies += "org.apache.spark" %% "spark-core" % "1.3.0"
//libraryDependencies += "org.apache.hadoop" % "hadoop-client" % "2.6.0"
//libraryDependencies += "com.google.guava" % "guava" % "11.0.2"
