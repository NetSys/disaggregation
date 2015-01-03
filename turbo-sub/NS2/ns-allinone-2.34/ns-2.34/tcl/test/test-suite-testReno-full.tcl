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
# @(#) $Header: /cvsroot/nsnam/ns-2/tcl/test/test-suite-testReno-full.tcl,v 1.13 2006/01/24 23:00:08 sallyfloyd Exp $
#
# To view a list of available tests to run with this script:
# ns test-suite-testReno-full.tcl
#

source misc_simple.tcl
remove-all-packet-headers       ; # removes all except common
add-packet-header Flags IP TCP  ; # hdrs reqd for TCP

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

Agent/TCP set minrto_ 0
# The default is being changed to minrto_ 1
Agent/TCP set syn_ false
Agent/TCP set delay_growth_ false
# In preparation for changing the default values for syn_ and delay_growth_.

Trace set show_tcphdr_ 1

set wrap 90
set wrap1 [expr 90 * 512 + 40]

Class Topology

Topology instproc node? num {
    $self instvar node_
    return $node_($num)
}

#
# Links1 uses 8Mb, 5ms feeders, and a 800Kb 10ms bottleneck.
# Queue-limit on bottleneck is 2 packets.
#
Class Topology/net4 -superclass Topology
Topology/net4 instproc init ns {
    $self instvar node_
    set node_(s1) [$ns node]
    set node_(s2) [$ns node]
    set node_(r1) [$ns node]
    set node_(k1) [$ns node]

    $self next
    $ns duplex-link $node_(s1) $node_(r1) 8Mb 0ms DropTail
    $ns duplex-link $node_(s2) $node_(r1) 8Mb 0ms DropTail
    $ns duplex-link $node_(r1) $node_(k1) 800Kb 100ms DropTail
    $ns queue-limit $node_(r1) $node_(k1) 8
    $ns queue-limit $node_(k1) $node_(r1) 8

    $self instvar lossylink_
    set lossylink_ [$ns link $node_(r1) $node_(k1)]
    set em [new ErrorModule Fid]
    set errmodel [new ErrorModel/Periodic]
    $errmodel unit pkt
    $lossylink_ errormodule $em
}


TestSuite instproc finish file {
    global quiet wrap PERL
    set wrap [expr 90 * 1000 + 40]
    exec $PERL ../../bin/set_flow_id -s all.tr | \
	    $PERL ../../bin/getrc -e -s 2 -d 3 | \
	    $PERL ../../bin/raw2xg -v -s 0.00001 -m $wrap -t $file > temp.rands
    
    if {$quiet == "false"} {
	exec xgraph -bb -tk -nl -m -x time -y packets temp.rands &
    }
    ## now use default graphing tool to make a data file
    ## if so desired
    # exec csh gnuplotC.com temp.rands $file
    exit 0
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

TestSuite instproc setup {tcptype window list} {
    global wrap wrap1
    $self instvar ns_ node_ testName_
    $self setTopo
    
    Agent/TCP set bugFix_ false
    set fid 1
    # Set up TCP connection
    if {$tcptype == "FullTcp"} {
	set tcp1 [new Agent/TCP/FullTcp]
	set sink [new Agent/TCP/FullTcp]
	$ns_ attach-agent $node_(s1) $tcp1
	$ns_ attach-agent $node_(k1) $sink
	$tcp1 set fid_ $fid
	$sink set fid_ $fid
	$ns_ connect $tcp1 $sink
	# set up TCP-level connections
	$sink listen ; # will figure out who its peer is
    } elseif {$tcptype == "BayFullTcp"} {
	set sink [new Agent/TCP/BayFullTcp]
	set tcp1 [new Agent/TCP/BayFullTcp]
	$ns_ attach-agent $node_(k1) $sink
	$ns_ attach-agent $node_(s1) $tcp1
	$sink set fid_ $fid
	$tcp1 set fid_ $fid
	$ns_ connect $sink $tcp1
	# set up TCP-level connections
	$tcp1 listen ; # will figure out who its peer is
    } elseif {$tcptype == "FullTcpTahoe"} {
	set tcp1 [new Agent/TCP/FullTcp/Tahoe]
	set sink [new Agent/TCP/FullTcp/Tahoe]
	$ns_ attach-agent $node_(s1) $tcp1
	$ns_ attach-agent $node_(k1) $sink
	$tcp1 set fid_ $fid
	$sink set fid_ $fid
	$ns_ connect $tcp1 $sink
	# set up TCP-level connections
	$sink listen ; # will figure out who its peer is
    } elseif {$tcptype == "FullTcpNewreno"} {
	set tcp1 [new Agent/TCP/FullTcp/Newreno]
	set sink [new Agent/TCP/FullTcp/Newreno]
	$ns_ attach-agent $node_(s1) $tcp1
	$ns_ attach-agent $node_(k1) $sink
	$tcp1 set fid_ $fid
	$sink set fid_ $fid
	$ns_ connect $tcp1 $sink
	# set up TCP-level connections
	$sink listen ; # will figure out who its peer is
    } elseif {$tcptype == "FullTcpSack1"} {
	set tcp1 [new Agent/TCP/FullTcp/Sack]
	set sink [new Agent/TCP/FullTcp/Sack]
	$ns_ attach-agent $node_(s1) $tcp1
	$ns_ attach-agent $node_(k1) $sink
	$tcp1 set fid_ $fid
	$sink set fid_ $fid
	$ns_ connect $tcp1 $sink
	# set up TCP-level connections
	$sink listen ; # will figure out who its peer is
    } else {
	puts "Error: Type of FullTcp not supported\n"
	exit 1
    }

    #$tcp1 set window_ 5
    $tcp1 set window_ $window
    if {$tcptype == "BayFullTcp"} {
	$tcp1 set window_ $window 
	set cli [new Agent/BayTcpApp/FtpClient]
	$sink attach-application $cli
	$cli tcp $sink
	set sftp [new Agent/BayTcpApp/FtpServer]
	$sftp file_size 10000000
	$tcp1 attach-application $sftp
        $ns_ at 1.0 "$cli start"
    } else {
        set ftp1 [$tcp1 attach-app FTP]
        $ns_ at 1.0 "$ftp1 start"
    }
    
    $self tcpDump $tcp1 4.0
    $self drop_pkts $list
    
    #$self traceQueues $node_(r1) [$self openTrace 4.01 $testName_]
    $ns_ at 4.01 "$self cleanupAll $testName_"
    $ns_ run
}
    

# Definition of test-suite tests

###################################################
## Two drops
###################################################

Class Test/Tahoe_FullTCP -superclass TestSuite
Test/Tahoe_FullTCP instproc init {} {
	$self instvar net_ test_
	set net_	net4
	set test_	Tahoe_FullTCP
	$self next
}
Test/Tahoe_FullTCP instproc run {} {
    $self setup FullTcpTahoe {5} {15 18}
}

#Class Test/Tahoe_FullTCP_without_Fast_Retransmit -superclass TestSuite
#Test/Tahoe_FullTCP_without_Fast_Retransmit instproc init {} {
#	$self instvar net_ test_
#	set net_	net4
#	set test_	Tahoe_FullTCP_without_Fast_Retransmit
#	Agent/TCP set noFastRetrans_ true
#	$self next
#}
#Test/Tahoe_FullTCP_without_Fast_Retransmit instproc run {} {
#        $self setup FullTcpTahoe {5} {15 18}
#}

Class Test/Reno_FullTCP -superclass TestSuite
Test/Reno_FullTCP instproc init {} {
	$self instvar net_ test_
	set net_	net4
	set test_	Reno_FullTCP
	$self next
}
Test/Reno_FullTCP instproc run {} {
        $self setup FullTcp {5} {15 18}
}

# What is this test doing?
# After the partial ACK, it seems that BayFullTCP keeps the inflated
#  congestion window, but advances the left edge of the congestion window? 
Class Test/Reno_BayFullTCP -superclass TestSuite
Test/Reno_BayFullTCP instproc init {} {
	$self instvar net_ test_
	set net_	net4
	set test_	Reno_BayFullTCP
	$self next
}
Test/Reno_BayFullTCP instproc run {} {
        $self setup BayFullTcp {5} {14 17}
}

Class Test/NewReno_FullTCP -superclass TestSuite
Test/NewReno_FullTCP instproc init {} {
	$self instvar net_ test_
	set net_	net4
	set test_	NewReno_FullTCP
	Agent/TCP set noFastRetrans_ false
	$self next
}
Test/NewReno_FullTCP instproc run {} {
        $self setup FullTcpNewreno {5} {15 18}
}

#Class Test/Sack_FullTCP -superclass TestSuite
#Test/Sack_FullTCP instproc init {} {
#	$self instvar net_ test_
#	set net_	net4
#	set test_	Sack_FullTCP
#	Agent/TCP set noFastRetrans_ false
#	$self next
#}
#Test/Sack_FullTCP instproc run {} {
#        $self setup FullTcpSack1 {5} {15 18}
#}

###################################################
## One drop
###################################################

Class Test/Tahoe_FullTCP2 -superclass TestSuite
Test/Tahoe_FullTCP2 instproc init {} {
    $self instvar net_ test_
    set net_	net4
    set test_	Tahoe_FullTCP2
    $self next
}
Test/Tahoe_FullTCP2 instproc run {} {
        $self setup FullTcpTahoe {8} {17}
}

#Class Test/Tahoe_FullTCP2_without_Fast_Retransmit -superclass TestSuite
#Test/Tahoe_FullTCP2_without_Fast_Retransmit instproc init {} {
    #$self instvar net_ test_
    #set net_	net4
    #set test_	Tahoe_FullTCP2_without_Fast_Retransmit
    #Agent/TCP/FullTcp/Tahoe set noFastRetrans_ true
    #$self next
    #}
#Test/Tahoe_FullTCP2_without_Fast_Retransmit instproc run {} {
    #$self setup FullTcpTahoe {8} {17}
    #}

Class Test/Reno_FullTCP2 -superclass TestSuite
Test/Reno_FullTCP2 instproc init {} {
	$self instvar net_ test_
	set net_	net4
	set test_	Reno_FullTCP2
	$self next
}
Test/Reno_FullTCP2 instproc run {} {
        $self setup FullTcp {8} {17}
}

Class Test/Reno_BayFullTCP2 -superclass TestSuite
Test/Reno_BayFullTCP2 instproc init {} {
	$self instvar net_ test_
	set net_	net4
	set test_	Reno_BayFullTCP2
	$self next
}
Test/Reno_BayFullTCP2 instproc run {} {
        $self setup BayFullTcp {8} {16}
}

Class Test/NewReno_FullTCP2 -superclass TestSuite
Test/NewReno_FullTCP2 instproc init {} {
	$self instvar net_ test_
	set net_	net4
	set test_	NewReno_FullTCP2
	Agent/TCP set noFastRetrans_ false
	$self next
}
Test/NewReno_FullTCP2 instproc run {} {
        $self setup FullTcpNewreno {8} {17}
}

#Class Test/Sack_FullTCP2 -superclass TestSuite
#Test/Sack_FullTCP2 instproc init {} {
#	$self instvar net_ test_
#	set net_	net4
#	set test_	Sack_FullTCP2
#	Agent/TCP set noFastRetrans_ false
#	$self next
#}
#Test/Sack_FullTCP2 instproc run {} {
#        $self setup FullTcpSack1 {8} {17}
#}

TestSuite runTest

