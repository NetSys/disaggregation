#
# Copyright (c) 1995 The Regents of the University of California.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#	This product includes software developed by the Computer Systems
#	Engineering Group at Lawrence Berkeley Laboratory.
# 4. Neither the name of the University nor of the Laboratory may be used
#    to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# @(#) $Header: /cvsroot/nsnam/ns-2/tcl/test/test-suite-frto.tcl,v 1.4 2006/01/24 23:00:06 sallyfloyd Exp $
#
# To view a list of available tests to run with this script:
# ns test-suite-tcpVariants.tcl
#

source misc.tcl
remove-all-packet-headers       ; # removes all except common
add-packet-header Flags IP TCP  ; # hdrs reqd for validation test

Agent/TCP set tcpTick_ 0.1
# The default for tcpTick_ is being changed to reflect a changing reality.
Agent/TCP set rfc2988_ false
# The default for rfc2988_ is being changed to true.
# FOR UPDATING GLOBAL DEFAULTS:
Agent/TCP set precisionReduce_ false ;   # default changed on 2006/1/24.
Agent/TCP set rtxcur_init_ 6.0 ;      # Default changed on 2006/01/21
Agent/TCP set updated_rttvar_ false ;  # Variable added on 2006/1/21
Agent/TCP set useHeaders_ false
# The default is being changed to useHeaders_ true.
Agent/TCP set windowInit_ 1
# The default is being changed to 2.
Agent/TCP set singledup_ 0
# The default is being changed to 1
source topologies.tcl

Agent/TCP set minrto_ 0
# The default is being changed to minrto_ 1
Agent/TCP set syn_ false
Agent/TCP set delay_growth_ false
# In preparation for changing the default values for syn_ and delay_growth_.

Agent/TCP set frto_enabled_ true
Agent/TCP set sfrto_enabled_ true

Agent/TCP set partial_ack_ true

Trace set show_tcphdr_ 1

set wrap 200
set wrap1 [expr 90 * 512 + 40]

TestSuite instproc finish file {
	global quiet wrap PERL
	exec echo "0.Color: red" > temp.rands
	exec echo "2.Color: blue" >> temp.rands
	exec echo "1.Color: red" >> temp.rands
	exec echo "3.Color: purple" >> temp.rands
          exec $PERL ../../bin/getrc -b -s 0 -d 2 all.tr | \
          $PERL ../../bin/raw2xg -c -s 0.01 -m $wrap -r -t $file >> temp.rands
          exec $PERL ../../bin/getrc -b -s 2 -d 0 all.tr | \
          $PERL ../../bin/raw2xg -c -a -s 0.01 -m $wrap -t $file >> temp.rands
	  exec $PERL ../../bin/getrc -s 2 -d 3 all.tr | \
          $PERL ../../bin/raw2xg -c -d -s 0.01 -m $wrap -t $file >> temp.rands
	if {$quiet == "false"} {
		exec xgraph -bb -tk -nl -m -x time -y packets temp.rands &
	}
        ## now use default graphing tool to make a data file
	## if so desired
        exit 0
}

TestSuite instproc printtimers { tcp time} {
	global quiet
	if {$quiet == "false"} {
        	puts "time: $time sRTT(in ticks): [$tcp set srtt_]/8 RTTvar(in ticks): [$tcp set rttvar_]/4 backoff: [$tcp set backoff_]"
	}
}

TestSuite instproc printtimersAll { tcp time interval } {
        $self instvar dump_inst_ ns_
        if ![info exists dump_inst_($tcp)] {
                set dump_inst_($tcp) 1
                $ns_ at $time "$self printtimersAll $tcp $time $interval"
                return
        }
	set newTime [expr [$ns_ now] + $interval]
	$ns_ at $time "$self printtimers $tcp $time"
        $ns_ at $newTime "$self printtimersAll $tcp $newTime $interval"
}


#
# Links1 uses 8Mb, 5ms feeders, and a 800Kb 10ms bottleneck.
# Queue-limit on bottleneck is 2 packets.
#
Class Topology/net4 -superclass NodeTopology/4nodes
Topology/net4 instproc init ns {
    $self next $ns
    $self instvar node_
    $ns duplex-link $node_(s1) $node_(r1) 8Mb 0ms DropTail
    $ns duplex-link $node_(s2) $node_(r1) 8Mb 0ms DropTail
    $ns duplex-link $node_(r1) $node_(k1) 800Kb 10ms DropTail
    $ns queue-limit $node_(r1) $node_(k1) 8
    $ns queue-limit $node_(k1) $node_(r1) 8
    if {[$class info instprocs config] != ""} {
	$self config $ns
    }

    $self instvar lossylink_
    set lossylink_ [$ns link $node_(r1) $node_(k1)]
    set em [new ErrorModule Fid] 
    set errmodel [new ErrorModel/Periodic]
    $errmodel unit pkt
    $lossylink_ errormodule $em
}


Class Topology/net4delay -superclass NodeTopology/4nodes
Topology/net4delay instproc init ns {
    global delayerDL myns_

    $self next $ns
    $self instvar node_
    $ns duplex-link $node_(s1) $node_(r1) 2Mb 5ms DropTail
    $ns duplex-link $node_(s2) $node_(r1) 2Mb 5ms DropTail
    $ns duplex-link $node_(r1) $node_(k1) 800Kb 20ms DropTail
    $ns queue-limit $node_(r1) $node_(k1) 8
    $ns queue-limit $node_(k1) $node_(r1) 8
    
    set delayerDL [new Delayer]
    $ns insert-delayer $node_(s1) $node_(r1) $delayerDL
    $ns after 1.5 "insertDelay"
    set myns_ $ns

    if {[$class info instprocs config] != ""} {
	$self config $ns
    }

    $self instvar lossylink_
    set lossylink_ [$ns link $node_(r1) $node_(k1)]
    set em [new ErrorModule Fid] 
    set errmodel [new ErrorModel/Periodic]
    $errmodel unit pkt
    $lossylink_ errormodule $em
}


TestSuite instproc emod {} {
        $self instvar topo_
        $topo_ instvar lossylink_
        set errmodule [$lossylink_ errormodule]
        return $errmodule
} 

TestSuite instproc drop_pkts pkts {
    $self instvar ns_
    set emod [$self emod]
    set errmodel1 [new ErrorModel/List]
    $errmodel1 droplist $pkts
    $emod insert $errmodel1
    $emod bind $errmodel1 1
}

TestSuite instproc setup {tcptype list} {
	global wrap wrap1
        $self instvar ns_ node_ testName_

	set fid 1
        # Set up TCP connection
    	if {$tcptype == "Tahoe"} {
      		set tcp1 [$ns_ create-connection TCP $node_(s1) \
          	TCPSink/DelAck $node_(k1) $fid]
    	} elseif {$tcptype == "Sack1"} {
      		set tcp1 [$ns_ create-connection TCP/Sack1 $node_(s1) \
          	TCPSink/Sack1/DelAck  $node_(k1) $fid]
    	} else {
      		set tcp1 [$ns_ create-connection TCP/$tcptype $node_(s1) \
          	TCPSink/DelAck $node_(k1) $fid]
    	}
        $tcp1 set window_ 28
        set ftp1 [$tcp1 attach-app FTP]
        $ns_ at 1.0 "$ftp1 produce 35"

        $self tcpDump $tcp1 6.0
	$self drop_pkts $list

        $self traceQueues $node_(r1) [$self openTrace 6.0 $testName_]
        $ns_ run
}

# Definition of test-suite tests


###################################################
## Checking for RFC2581-compliant immediate ACK on filling a hole.
###################################################

Class Test/immediateAck -superclass TestSuite
Test/immediateAck instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4
	set test_	immediateAck
	Agent/TCPSink set RFC2581_immediate_ack_ true
	$self next
}
Test/immediateAck instproc run {} {
	Agent/TCPSink/DelAck set interval_ 200ms
        $self setup Tahoe {3 4}
}


Class Test/immediateAckReno -superclass TestSuite
Test/immediateAckReno instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4
	set test_	immediateAckReno
	Agent/TCPSink set RFC2581_immediate_ack_ true
	$self next
}
Test/immediateAckReno instproc run {} {
	Agent/TCPSink/DelAck set interval_ 200ms
        $self setup Reno {3 4}
}


Class Test/immediateAckNewReno -superclass TestSuite
Test/immediateAckNewReno instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4
	set test_	immediateAckNewReno
	Agent/TCPSink set RFC2581_immediate_ack_ true
	$self next
}
Test/immediateAckNewReno instproc run {} {
	Agent/TCPSink/DelAck set interval_ 200ms
        $self setup Newreno {5 6}
}

Class Test/noImmediateAckNewReno -superclass TestSuite
Test/noImmediateAckNewReno instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4
	set test_	noImmediateAckNewReno
	Agent/TCPSink set RFC2581_immediate_ack_ false
	Test/noImmediateAckNewReno instproc run {} [Test/immediateAckNewReno info instbody run ]
	$self next
}


Class Test/noImmediateAckSack -superclass TestSuite
Test/noImmediateAckSack instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4
	set test_	noImmediateAckSack
	Agent/TCPSink set RFC2581_immediate_ack_ false
	$self next
}
Test/noImmediateAckSack instproc run {} {
	Agent/TCPSink/Sack1/DelAck set interval_ 200ms
        $self setup Sack1 {3 4}
}

proc insertDelay {} {
        global delayerDL myns_

        $delayerDL block
 
        set len 1
        $myns_ after $len "$delayerDL unblock"
}


Class Test/delaySpikesSack -superclass TestSuite
Test/delaySpikesSack instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4delay
	set test_	delaySpikesSack
	Agent/TCPSink set RFC2581_immediate_ack_ false
	
	$self next
}
Test/delaySpikesSack instproc run {} {
	Agent/TCPSink/Sack1/DelAck set interval_ 200ms
        $self setup Sack1 {30}
}

Class Test/dropsNDelaySpikes -superclass TestSuite
Test/dropsNDelaySpikes instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4delay
	set test_	dropsNDelaySpikes
	Agent/TCPSink set RFC2581_immediate_ack_ true

	$self next
}
Test/dropsNDelaySpikes instproc run {} {
	Agent/TCPSink/Sack1/DelAck set interval_ 200ms
        $self setup Sack1 {17 18 30}
}

Class Test/spikeNDupAck -superclass TestSuite
Test/spikeNDupAck instproc init topo {
	$self instvar net_ defNet_ test_
	set net_	$topo
	set defNet_	net4delay
	set test_	spikeNDupAck
	Agent/TCPSink set RFC2581_immediate_ack_ true

	$self next
}
Test/spikeNDupAck instproc run {} {
	Agent/TCPSink/Sack1/DelAck set interval_ 200ms
        $self setup Sack1 {13 30}
}


TestSuite runTest

### Local Variables:
### mode: tcl
### tcl-indent-level: 8
### tcl-default-application: ns
### End:
