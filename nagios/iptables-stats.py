#!/usr/bin/env python
#
# Copyright (c) 2008 Tim Kuhlman <tim@backgroundprocess.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
"""This nagios plugin collects byte and packet counts from iptables.

 You can pull the counts from any individual rules. Ccounts from the chain as a
 whole aren't pulled because they can't be zeroed out and so are less useful.
 This means it is often helpful to have a rule matching the chains policy at the end
 of a chain. For example '-A INPUT -j DROP' or '-A OUTPUT -j ACCEPT'

 I don't differentiate between dropped packets and rejected, they both show up as blocked.

 The iptables command requires root. This means that either this script needs
 to be run as root, setuid root or sudo needs to be used. A properly setup sudo is
 the most secure of the options. When setting up sudo specify the command to be
 'iptables -L'. The '-L' is very important without it you are also giving permissions
 to add and delete firewall rules. Below is an example of the relevant line from
 my sudoers setup.

 nagios   ALL=NOPASSWD: /sbin/iptables -L *

"""

import os, sys
from optparse import OptionParser

VERSION='1.0'
IPTABLES='/usr/bin/sudo /sbin/iptables'

def main(argv=None):
    if argv is None:
        argv = sys.argv
    #Get the settings
    options = parseArgs(argv)

    #Run the command
    outpipe=os.popen(IPTABLES + ' -L ' + options.chain + ' -Z -x -n -v --line-numbers -t ' + options.table, 'r')

    #parse the Output
    results = parseOutput(outpipe, options.rules, options.seconds)
    if options.verbose:
        for line in results:
            print 'Line number:' + str(line[0]) + ' Packets:' + str(line[1]) + ' Bytes:' + str(line[2]) \
            + ' Accepted:' + str(line[3])

    if options.totals:
        (totalPktsAccepted, totalBytesAccepted, totalPktsBlocked, totalBytesBlocked) = getTotals(results)

    #begin building the output lines and checking the limits based on the options
    mesg=''
    perf=''
    exit=0 #0 okay, 1 warning, 2 critical, 3 unknown
    #bytes/packets or both, totals or individuals
    if options.packets:
        if options.totals:
            if options.accepted:
                if options.packetCritical != 0 and totalPktsAccepted > options.packetCritical:
                    mesg = mesg + ' Critical! '
                    if exit < 2:
                        exit = 2
                elif options.packetWarning !=0 and totalPktsAccepted > options.packetWarning:
                    mesg = mesg + ' WARNING! '
                    if exit < 1:
                        exit = 1
                mesg = mesg + ' Accepted Packet Total:' + str(totalPktsAccepted)
                perf = perf + " 'Total Packets Accepted'=" + str(totalPktsAccepted) +";" \
                + str(options.packetWarning) + ";" + str(options.packetCritical)
            if options.blocked:
                if options.packetCritical != 0 and totalPktsBlocked > options.packetCritical:
                    mesg = mesg + ' Critical! '
                    if exit < 2:
                        exit = 2
                elif options.packetWarning !=0 and totalPktsBlocked > options.packetWarning:
                    mesg = mesg + ' WARNING! '
                    if exit < 1:
                        exit = 1
                mesg = mesg + ' Blocked Packet Total:' + str(totalPktsBlocked)
                perf = perf + " 'Total Packets Blocked'=" + str(totalPktsBlocked) \
                + ";" + str(options.packetWarning) + ";" + str(options.packetCritical)
        if options.individuals:
            for line in results:
                if options.accepted and line[3]:
                    if options.packetCritical != 0 and line[1] > options.packetCritical:
                        mesg = mesg + ' Critical! '
                        if exit < 2:
                            exit = 2
                    elif options.packetWarning !=0 and line[1] > options.packetWarning:
                        mesg = mesg + ' WARNING! '
                        if exit < 1:
                            exit = 1
                    mesg = mesg + ' Rule ' + str(line[0]) + ' Accepted Packets:' + str(line[1])
                    perf = perf + " 'Rule " + str(line[0]) + " Packets Accepted'=" + str(line[1]) + ";" \
                    + str(options.packetWarning) + ";" + str(options.packetCritical)
                if options.blocked and not line[3]:
                    if options.packetCritical != 0 and line[1] > options.packetCritical:
                        mesg = mesg + ' Critical! '
                        if exit < 2:
                            exit = 2
                    elif options.packetWarning !=0 and line[1] > options.packetWarning:
                        mesg = mesg + ' WARNING! '
                        if exit < 1:
                            exit = 1
                    mesg = mesg + ' Rule ' + str(line[0]) + ' Packet Total:' + str(line[1])
                    perf = perf + " 'Rule " + str(line[0]) + " Packets Blocked'=" + str(line[1]) + ";" \
                    + str(options.packetWarning) + ";" + str(options.packetCritical)
    if options.bytes:
        if options.totals:
            if options.accepted:
                if options.byteCritical != 0 and totalPktsAccepted > options.byteCritical:
                    mesg = mesg + ' Critical! '
                    if exit < 2:
                        exit = 2
                    elif options.byteWarning != 0 and totalPktsAccepted > options.byteWarning:
                        mesg = mesg + ' WARNING! '
                    if exit < 1:
                        exit = 1
                mesg = mesg + ' Accepted Bytes Total:' + str(totalPktsAccepted)
                perf = perf + " 'Total Bytes Accepted'=" + str(totalPktsAccepted) + ";" + str(options.byteWarning) \
                + ";" + str(options.byteCritical)
            if options.blocked:
                if options.byteCritical != 0 and totalPktsBlocked > options.byteCritical:
                    mesg = mesg + ' Critical! '
                    if exit < 2:
                        exit = 2
                elif options.byteWarning != 0 and totalPktsBlocked > options.byteWarning:
                    mesg = mesg + ' WARNING! '
                    if exit < 1:
                        exit = 1
                mesg = mesg + ' Blocked Bytes Total:' + str(totalPktsBlocked)
                perf = perf + " 'Total Bytes Blocked'=" + str(totalPktsBlocked) + ";" + str(options.byteWarning) \
                + ";" + str(options.byteCritical)
        if options.individuals:
            for line in results:
                if options.accepted and line[3]:
                    if options.byteCritical != 0 and line[1] > options.byteCritical:
                        mesg = mesg + ' Critical! '
                        if exit < 2:
                            exit = 2
                    elif options.byteWarning != 0 and line[1] > options.byteWarning:
                        mesg = mesg + ' WARNING! '
                        if exit < 1:
                            exit = 1
                    mesg = mesg + ' Rule ' + str(line[0]) + ' Accepted Bytes:' + str(line[1])
                    perf = perf + " 'Rule " + str(line[0]) + " Bytes Accepted'=" + str(line[1]) + ";" \
                    + str(options.byteWarning) + ";" + str(options.byteCritical)
                if options.blocked and not line[3]:
                    if options.byteCritical != 0 and line[1] > options.byteCritical:
                        mesg = mesg + ' Critical! '
                        if exit < 2:
                            exit = 2
                    elif options.byteWarning != 0 and line[1] > options.byteWarning:
                        mesg = mesg + ' WARNING! '
                        if exit < 1:
                            exit = 1
                    mesg = mesg + ' Rule ' + str(line[0]) + ' Bytes Total:' + str(line[1])
                    perf = perf + " 'Rule " + str(line[0]) + " Bytes Blocked'=" + str(line[1]) + ";" \
                    + str(options.byteWarning) + ";" + str(options.byteCritical)

    #print the message and exit
    if exit == 0:
        state = 'OK:'
    elif exit == 1:
        state = 'Warning:'
    elif exit == 2:
        state = 'Critical:'
    elif exit == 3:
        state = 'Unknown:'
    print state + mesg + '|' + perf
    sys.exit(exit)


def getTotals(results):
    "Add up the totals, returns total accpeted and total dropped for bytes and packets"
    goodBytes = 0
    goodPkts = 0
    badBytes = 0
    badPkts = 0
    for line in results:
        if line[3]:
            goodBytes = goodBytes + line[2]
            goodPkts = goodPkts + line[1]
        else:
            badBytes = badBytes + line[2]
            badPkts = badPkts + line[1]

    return (goodPkts, goodBytes, badPkts, badBytes)



def parseArgs (argv):
    "Parses the arguments"
    #Define the cmdline arguments
    usage="usage: %prog [options]"
    description=""
    parser = OptionParser(usage=usage, description=description, version="%prog " + VERSION)
    parser.add_option('-w', type='int', dest='warning', default=0, help='Warning limit, if byte/packet limits are not set this is used.')
    parser.add_option('-c', type='int', dest='critical', default=0, help='Critical limit, if byte/packet limits are not set this is used.')
    parser.add_option('--byte-warning', type='int', dest='byteWarning', help='Byte warning limit. Used on both individual and total counts if both are specified.')
    parser.add_option('--packet-warning', type='int', dest='packetWarning', help='Packet warning limit. Used on both individual and total counts if both are specified.')
    parser.add_option('--byte-critical', type='int', dest='byteCritical', help='Byte critical limit. Used on both individual and total counts if both are specified.')
    parser.add_option('--packet-critical', type='int', dest='packetCritical', help='Packet critical limit. Used on both individual and total counts if both are specified.')
    parser.add_option('-C', '--chain', dest='chain', default="INPUT", help='Iptables chain to check. [default: %default]')
    parser.add_option('-T', '--table', dest='table', default='filter', help='Iptables table to check. [default: %default]')
    parser.add_option('-t', '--totals', dest='totals', action='store_true', default=False, help='Output the total counts for accepted and blocked.')
    parser.add_option('-i', '--individuals', dest='individuals', action='store_true', default=False, help='Output the individual rule counts for accepted and blocked.')
    parser.add_option('--blocked-only', dest='accepted', action="store_false", default=True, help='Output only blocked count')
    parser.add_option('--accepted-only', dest='blocked', action="store_false", default=True, help='Output only accepted count')
    parser.add_option('-p', '--packet-only', dest='bytes', action="store_false", default=True, help='Output packet count only. [default: packets and bytes]')
    parser.add_option('-b', '--byte-only', dest='packets', action="store_false", default=True, help='Output byte count only. [default: packets and bytes]')
    parser.add_option('-r', '--rule', dest='rules', type='int', action='append', help='Rule to use in counts. Can be specified multiple times, like "-r 1 -r 3" [default: All rules in the chain]')
    parser.add_option('-s', '--seconds', dest='seconds', type='int', help='If specified the counts will be divided byt this number to give bytes per second or packets per second.')
    parser.add_option("-v", action="store_true", default=False, dest="verbose", help="Verbose")

    #Do the actual parsing
    (options, args) = parser.parse_args(argv)

    # I don't want anything left over
    if len(args) > 1:
        print "Unknown options: ", args[1:]
        parser.print_help()
        sys.exit(3)

    #Check for mutually exclusive options
    if options.blocked == False and options.accepted == False:
        print "--blocked-only and --accepted-only are mutually exclusive."
        parser.print_help()
        sys.exit(3)
    if options.packets == False and options.bytes == False:
        print "-p (--packet-only) and -b (--byte-only) are mutually exclusive."
        parser.print_help()
        sys.exit(3)

    #require -t or -i or both
    if options.totals == False and options.individuals == False:
        print "Options -t (--totals) and/or -i (--individuals) required."
        parser.print_help()
        sys.exit(3)

    #if packet/byte warning and critical limits are not set but the general ones are set them
    if options.warning != None:
        if options.byteWarning == None:
            options.byteWarning = options.warning
        if options.packetWarning == None:
            options.packetWarning = options.warning
    if options.critical != None:
        if options.byteCritical == None:
            options.byteCritical = options.critical
        if options.packetCritical == None:
            options.packetCritical = options.critical

    return options

def parseOutput(out, rules, seconds):
    """ Takes a file object as input and parses it. Returns a tuple like
        ((line number, packet count, byte count, Accepted boolean))
        The accepted boolean is true if the count is accepted false if it is blocked.
        If rule numbers are specified only those rules are added to the results.
    """
    results = []
    for line in out.readlines():
        words = line.split()
        #skip lines that don't start with a number, these are headers and footers
        try:
            linenum = int(words[0])
        except:
            continue
        #Skip rules not specified if any are specified
        if rules != None and linenum not in rules:
            continue

        if seconds == None:
            pkts = int(words[1])
            bytes = int(words[2])
        else:
            #I want it to round and that takes some converion mess
            pkts = int(round(int(words[1])/float(seconds)))
            bytes = int(round(int(words[2])/float(seconds)))
        if words[3] == 'ACCEPT':
            accepted = True
        else:
            accepted = False
        results.append((linenum, pkts, bytes, accepted))

    return tuple(results)

if __name__ == "__main__":
    sys.exit(main())
