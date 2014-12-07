source "tcp-common-opt.tcl"

# create a simulator object
set ns [new Simulator]
puts "Date: [clock format [clock seconds]]"
set sim_start [clock seconds]
set enableNAM 0

Agent/TCP set ecn_ 1
Agent/TCP set old_ecn_ 1
Agent/TCP/FullTcp set spa_thresh_ 0
Agent/TCP set window_ 64
Agent/TCP set windowInit_ 2
Agent/TCP set windowOption_ 0
Agent/TCP set tcpTick_ 0.000001
Agent/TCP set maxrto_ 2

Agent/TCP/FullTcp set nodelay_ true; # disable Nagle
Agent/TCP/FullTcp set interval_ 0.000006
#Shuang
Agent/TCP set window_ 1000000
Agent/TCP set windowInit_ 12
Agent/TCP/FullTcp/Sack set clear_on_timeout_ false;
#Agent/TCP/FullTcp set pipectrl_ true;
Agent/TCP/FullTcp/Sack set sack_rtx_threshmode_ 2;
set queueSize 36
if {$queueSize > 12} {
   Agent/TCP set maxcwnd_ [expr $queueSize - 1];
} else {
   Agent/TCP set maxcwnd_ 12;
}
set myAgent Agent/TCP";


Queue set limit_ $queueSize


# create four nodes
set node1 [$ns node]
set node2 [$ns node]
set node3 [$ns node]
set node4 [$ns node]

# create links between the nodes
$ns duplex-link $node1 $node3 10Gb 15us DropTail 
$ns duplex-link $node2 $node3 10Gb 15us DropTail 
$ns duplex-link $node3 $node4 10Gb 15us DropTail 
$ns queue-limit $node3 $node4 4

# monitor the queue for the link between node 2 and node 3
$ns duplex-link-op $node3 $node4 queuePos 0.5
# necessary to remember the old bandwidth
set packetSize 1000
# First TCP traffic source
# create the first TCP agent and attach it to node node1
set tcp1 [new Agent/TCP]
$ns attach-agent $node1 $tcp1
$tcp1 set fid_ 1    # blue color
$tcp1 set class_ 1

# window_ * (packetsize_ + 40) / RTT
$tcp1 set window_ 25 
$tcp1 set packetSize_ $packetSize

# create a TCP sink agent and attach it to node node4
set sink [new Agent/TCPSink]
$ns attach-agent $node4 $sink

# connect both agents
$ns connect $tcp1 $sink

# create an FTP source "application";
set ftp1 [new Application/FTP]
$ftp1 attach-agent $tcp1


# Second TCP traffic source
# create the second TCP agent and attach it to node node2
set tcp2 [new Agent/TCP]
$ns attach-agent $node2 $tcp2
$tcp2 set fid_ 2    # red color
$tcp2 set class_ 2

# window_ * (packetsize_ + 40) / RTT
$tcp2 set window_ 25 
$tcp2 set packetSize_ $packetSize

# create a second TCP sink agent and attach it to node node4
set sink2 [new Agent/TCPSink]
$ns attach-agent $node4 $sink2

# connect tcp2 source to tcp sink at node 4
$ns connect $tcp2 $sink2

# create a second FTP source "application";
set ftp2 [new Application/FTP]
$ftp2 attach-agent $tcp2

set flowlog [open flow.tr w]
proc queueTrace {} {
}

# schedule events for all the flows
$ns at 0.1 "$ftp1 start"
$ns at 0.1 "$ftp2 start"
$ns at 5.0 "$ftp2 stop"
$ns at 5.0 "$ftp1 stop"

# call the finish procedure after 6 seconds of simulation time
$ns at 6 "finish"

# run the simulation
$ns run

