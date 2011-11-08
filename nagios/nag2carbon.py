#!/usr/bin/env python
"""Nagios performance data to carbon
    This is meant to be run as a nagios perfdata command. It takes the given performance data
    and send it to carbon (Part of graphite).

    The command expects the hostname, service name and performance data to be passed in.
    Optionally a hostgroup can be included, if so it is checked against a list of hostgroups
    processing is done for and if it isn't in that list it is skipped.
"""

import sys
import time
from socket import socket

CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003

#Only process performance data for these host groups
HOSTGROUPS = ['sql', 'windows']

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) < 4:
        print "Usage: " + argv[0] + " <hostname> <service name> <performance data> [Host group]"
        return 0

    hostname = argv[1].replace('.', '_')
    service = argv[2].replace(' ', '_')
    pdata = argv[3]

    #Skip if the specified hostgroup is not in the list to process.
    if len(argv) == 5:
        hostgroup = argv[4]
        if hostgroup not in HOSTGROUPS:
            print 'Hostgroup %s not in the list of hostgroups for which performance data' % hostgroup + \
                ' is processesed, skipping.'
            return 0

    #Parse the perfdata
    lines = []
    now = int(time.time())
    for perf in pdata.split(): #split all the data on whitespace
        pname, pvalues = perf.split('=', 1) #name and values split on =
        pvalue = pvalues.split(';')[0] #Only take the first value
        lines.append("%s.%s.%s %s %d" % (hostname, service, pname, pvalue, now))

    #Setup the socket
    sock = socket()
    try:
        sock.connect( (CARBON_SERVER, CARBON_PORT) )
    except:
        print "Couldn't connect to carbon server"
        return 1

    #send the message, each line seperated by newlines and with a trailing newline
    sock.sendall("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())

