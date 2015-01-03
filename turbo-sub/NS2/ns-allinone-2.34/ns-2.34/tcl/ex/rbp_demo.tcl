
#
# rbp_simulation.tcl
# $Id: rbp_demo.tcl,v 1.4 1998/10/21 02:29:47 tomh Exp $
#
# Copyright (c) 1997 University of Southern California.
# All rights reserved.                                            
#                                                                
# Redistribution and use in source and binary forms are permitted
# provided that the above copyright notice and this paragraph are
# duplicated in all such forms and that any documentation, advertising
# materials, and other materials related to such distribution and use
# acknowledge that the software was developed by the University of
# Southern California, Information Sciences Institute.  The name of the
# University may not be used to endorse or promote products derived from
# this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
# 

proc usage {} {
	puts stderr {usage: ns rbp_demo.tcl [options]

This simulation is maintained by John Heidemann <johnh@isi.edu>
and was written by John Heidemann and Vikram Visweswaraiah <visweswa@isi.edu>.
It demonstrates rate-based pacing as described in the paper
``Improving Restart of Idle TCP Connections'' (submitted for publication),
available at <http://www.isi.edu/~johnh/PAPERS/Visweswaraiah97a.html>
when invoked as.
}
	exit 1
}

proc default_options {} {
	global opts opt_wants_arg

	set raw_opt_info {
		duration 0

		client-count 10
		client-bw 10Mb
		client-delay 1ms
		# client network Ethernet or Myrinet
		client-queue-method DropTail
		# queue length in packets
		client-queue-length 10
		client-ack-method TCPSink/DelAck

		bottle-bw 800kb
		bottle-delay 100ms
		bottle-queue-method DropTail
		# experiments: 10KB
		# here, measured in packets
		bottle-queue-length 10

		server-bw 10Mb
		server-delay 1ms
		server-queue-method DropTail
		server-queue-length 10
		server-tcp-method TCP/Vegas/RBP
		server-tcp-slow-start-restart true
		server-tcp-window 32
		server-tcp-rbp-scale 0.75

		# packet size is 1000B
		# web page size in 10 pkts
		web-page-size 10

		experiment-trials 10
		# next two are times measured in seconds
		trial-jitter 3
		inter-trial-pause 20

		graph-results 1
		graph-join-queueing 1

		# For controlling algorithm rate or cwnd
		# 1 is Vegas computed rates, 2 is cwnd based alg
		rbp-rate-algorithm 1 

                # time-scale: factor to multiply seconds by to get ns
		# scheduler time units
		time-scale 1
		gen-map 0
		debug 0
		debug-fire-times 0
		    
		# Random number seed; default is 0, so ns will give a 
		# diff. one on each invocation.
		ns-random-seed 0
		
		# Animation options; complete traces are useful
		# for nam only, so do those only when a tracefile
		# is being used for nam
		nam-trace-all 0
		
		# Switch to generate the nam tcl file from here
		# itself
		nam-generate-cmdfile 0
	}

	while {$raw_opt_info != ""} {
		if {![regexp "^\[^\n\]*\n" $raw_opt_info line]} {
			break
		}
		regsub "^\[^\n\]*\n" $raw_opt_info {} raw_opt_info
		set line [string trim $line]
		if {[regexp "^\[ \t\]*#" $line]} {
			continue
		}
		if {$line == ""} {
			continue
		} elseif [regexp {^([^ ]+)[ ]+([^ ]+)$} $line dummy key value] {
			set opts($key) $value
			set opt_wants_arg($key) 1
		} else {
			set opt_wants_arg($key) 0
			# die "unknown stuff in raw_opt_info\n"
		}
	}
}

proc process_args {} {
	global argc argv opts opt_wants_arg

	default_options
	for {set i 0} {$i < $argc} {incr i} {
		set key [lindex $argv $i]
		if {$key == "-?" || $key == "--help" || $key == "-help" || $key == "-h"} {
			usage
		}
		regsub {^-} $key {} key
		if {![info exists opt_wants_arg($key)]} {
			puts stderr "unknown option $key";
			usage
		}
		if {$opt_wants_arg($key)} {
			incr i
			set opts($key) [lindex $argv $i]
		} else {
			set opts($key) [expr !opts($key)]
		}
	}
}

proc main {} {
	global argv
#	if {[llength $argv] != 1} {
#		usage
#	}
	process_args
	new TestScale
}



proc my-duplex-link {ns n1 n2 bw delay queue_method queue_length} {
	$ns duplex-link $n1 $n2 $bw $delay $queue_method
	$ns queue-limit $n1 $n2 $queue_length
	$ns queue-limit $n2 $n1 $queue_length
}


#
#  clients
#  c1
#  c2    ---- bottle_c ---- bottle_s ---- s
#  ...
#

Class TestScale

TestScale instproc init_network {} {
	global opts
	# nodes
	# build right to left
	$self instvar ns_ cs_ bottle_c_ bottle_s_ s_

	# build clients
	for {set i 0} {$i < $opts(client-count)} {incr i} {
		set cs_($i) [$ns_ node]
	}

	set bottle_c_ [$ns_ node]
	set bottle_s_ [$ns_ node]
	set s_ [$ns_ node]


	# links
	my-duplex-link $ns_ $s_ $bottle_s_ $opts(server-bw) $opts(server-delay) $opts(server-queue-method) $opts(server-queue-length)
	my-duplex-link $ns_ $bottle_s_ $bottle_c_ $opts(bottle-bw) $opts(bottle-delay) $opts(bottle-queue-method) $opts(bottle-queue-length)
	for {set i 0} {$i < $opts(client-count)} {incr i} {
		my-duplex-link $ns_ $cs_($i) $bottle_c_ $opts(client-bw) $opts(client-delay) $opts(client-queue-method) $opts(client-queue-length)
	}
}

Application/FTP instproc fire {} {
	global opts
	$self instvar maxpkts_
	set maxpkts_ [expr $maxpkts_ + $opts(web-page-size)]
	$self produce $maxpkts_
}

TestScale instproc init_connections {} {
	global opts
	$self instvar ns_ s_  tcp_ ftp_ cs_
	for {set i 0} {$i < $opts(client-count)} {incr i} {
		set tcp_($i) [$ns_ create-connection $opts(server-tcp-method) $s_ $opts(client-ack-method) $cs_($i) 0]
		$tcp_($i) set restart_bugfix_ 1
		$tcp_($i) set window_ $opts(server-tcp-window)
		if {[regexp "RBP" $opts(server-tcp-method)]} {
			$tcp_($i) set rbp_scale_ $opts(server-tcp-rbp-scale)
			$tcp_($i) set rbp_rate_algorithm_ $opts(rbp-rate-algorithm)
		}
		$tcp_($i) set slow_start_restart_ $opts(server-tcp-slow-start-restart)
		set ftp_($i) [$tcp_($i) attach-app FTP]
		$ftp_($i) set maxpkts_ 0
		# $ftp_($i) set experiment_matching_tcp_ $tcp_($i)
		# $tcp_($i) set experiment_matching_ftp_ $ftp_($i)
		$tcp_($i) set experiment_connection_i_ $i
		if {$opts(debug)} {
			puts "tcp_($i) $tcp_($i)"
			puts "ftp_($i) $ftp_($i)"
		}
	}
	# report on number paced
	if [string match {*Vegas/RBP*} $opts(server-tcp-method)] {
		Agent/$opts(server-tcp-method) instproc done {} {
			$self instvar rbp_segs_actually_paced_ rbp_inter_pace_delay_ experiment_connection_i_ cwnd_ v_rtt_
			puts "$experiment_connection_i_: cwnd_=$cwnd_ v_rtt_=$v_rtt_ rbp_segs_actually_paced_=$rbp_segs_actually_paced_ rbp_inter_pace_delay_=$rbp_inter_pace_delay_"
		}
	}
	if [string match {*Reno/RBP*} $opts(server-tcp-method)] {
		Agent/$opts(server-tcp-method) instproc done {} {
			$self instvar rbp_segs_actually_paced_ rbp_inter_pace_delay_ experiment_connection_i_ cwnd_ rtt_ srtt_
			puts "$experiment_connection_i_: cwnd_=$cwnd_ rtt=$rtt_ srtt=$srtt_ rbp_segs_actually_paced_=$rbp_segs_actually_paced_ rbp_inter_pace_delay_=$rbp_inter_pace_delay_"
		}
	}
}

TestScale instproc schedule_traffic {} {
	global opts
	$self instvar ns_ s_ tcp_ ftp_ rng_

	set base_time [expr 10*$opts(time-scale)]
	for {set i 0} {$i < $opts(experiment-trials)} {incr i} {
		if {$opts(debug-fire-times)} {
			puts "trial $i"
		}
		# schedule a trial
		for {set j 0} {$j < $opts(client-count)} {incr j} {
			set j_time [expr ($base_time + [$rng_ uniform 0 $opts(trial-jitter)] - ($opts(trial-jitter))/2) * $opts(time-scale)]
			$ns_ at $j_time "$ftp_($j) fire"
			if {$opts(debug-fire-times)} {
				puts "$ns_ at $j_time $ftp_($j) fire"
			}
			if { $j == 0 && $opts(debug)} {
				puts "$j fires at $j_time"
			}
		}
		incr base_time $opts(inter-trial-pause)
	}

	# limit duration
	if {$opts(duration) == 0} {
		set opts(duration) [expr ($opts(experiment-trials)+2)*$opts(inter-trial-pause)*$opts(time-scale)]
	}
}

TestScale instproc open_trace { stopTime testName } {
	exec rm -f out.tr temp.rands
	$self instvar ns_ trace_file_
	set trace_file_ [open out.tr w]
	$ns_ at $stopTime \
		"close $trace_file_ ; $self finish"
	return $trace_file_
}

# There seems to be a problem with the foll function, so quit plotting 
# with -a -q, use just -a.

TestScale instproc finish {} {
        global opts
	$self instvar trace_file_

	if {!$opts(graph-results)} {
		exit 0
	}

	if {$opts(graph-join-queueing)} {
		set q "-q"
	} else {
		set q ""
	}
	exec raw2xg -a -m $opts(web-page-size) -q < out.tr | xgraph -t "$opts(server-tcp-method)" &
#	exec raw2xg -a < out.tr | xgraph -t "$opts(server-tcp-method)" &
	
	exit 0
}

Simulator instproc nodes-to-link {n1 n2} {
	$self instvar link_
	return $link_([$n1 id]:[$n2 id])
}

TestScale instproc init {} {
	global opts

	$self instvar ns_ 
	set ns_ [new Simulator]

        # Seed random no. generator; ns-random with arg of 0 heuristically
        # chooses a random number that changes on each invocation.
	$self instvar rng_
	set rng_ [new RNG]
	$rng_ seed $opts(ns-random-seed)
	$rng_ next-random

	$self init_network
	$self init_connections
	$self schedule_traffic


	$self instvar bottle_c_ bottle_s_ s_ cs_
	set trace_file [$self open_trace $opts(duration) TestScale]

        if {$opts(nam-trace-all)} {
	        # trace-all should have worked, but it didn't, so the 
	        # individual trace commands
	    
	        # Trace from server to server router and vice versa
	        $ns_ trace-queue $s_ $bottle_s_ $trace_file
                $ns_ trace-queue $bottle_s_ $s_ $trace_file
		    
	        # Trace from the server router to client router and vice 
		# versa
	        $ns_ trace-queue $bottle_s_ $bottle_c_ $trace_file
	        $ns_ trace-queue $bottle_c_ $bottle_s_ $trace_file

	        # Trace from client router to each client and vice versa
	        for {set i 0} {$i < $opts(client-count)} {incr i} {
		        $ns_ trace-queue  $bottle_c_ $cs_($i) $trace_file
		        $ns_ trace-queue $cs_($i) $bottle_c_ $trace_file
		}

	} else {
         	$ns_ trace-queue $bottle_s_ $bottle_c_ $trace_file
		# note  that we trace after the delay of the bottleneck
		$ns_ trace-queue $bottle_s_ $s_ $trace_file
	}
	if {$opts(gen-map)} {
		$ns_ gen-map
	}       
	$ns_ run
}


main

