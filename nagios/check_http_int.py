#!/usr/bin/env python
""" Check Integer via http
This nagios plugin hits a http page which should return a simple integer in the body.
 This integer is then compared to warning/critical parameters and the output formatted appropriate for nagios.
"""

import os, sys, urllib2
from optparse import OptionParser

VERSION='1.0'

def main(argv=None):
    if argv is None:
        argv = sys.argv
    #Get the settings
    (options, args) = parseArgs(argv)
    url = args[1]

    #Hit the url, parse the thresholds
    try:
        body = urllib2.urlopen(url)
        value = int(body.read())
        crit_low, crit_high = threshold_parse(options.critical)
        warn_low, warn_high = threshold_parse(options.warning)
    except:
        #If the url fails return unknown
        mesg = 'Unknown:'
        value = None
        exit = 3
    else:
        if (crit_high is not None and value > crit_high) or (crit_low is not None and value < crit_low):
            exit = 2
            mesg = 'Critical:'
        elif (warn_high is not None and value > warn_high) or (warn_low is not None and value < warn_low):
            exit = 1
            mesg = 'Warning:'
        else:
            exit = 0
            mesg = 'OK:'

    #Create the output for nagios
    print '%s %s returned %s|value=%s' % (mesg, url, str(value), str(value))
    sys.exit(exit)


def parseArgs(argv):
    "Parses the arguments"
    #Define the cmdline arguments
    usage="usage: %prog -w <warning> -c <critical> <url>\n" + \
        "A number for warning or critical is treated as a max, alternatively you can specify min:max.\n" + \
        "It will then alert for value < min or value > max."
    parser = OptionParser(usage=usage, version="%prog " + VERSION)
    parser.add_option('-w', dest='warning', default=0, help='Warning limit.')
    parser.add_option('-c', dest='critical', default=0, help='Critical limit.')
    #Do the actual parsing
    (options, args) = parser.parse_args(argv)
    if len(args) < 2:
        parser.print_usage()
        sys.exit(3)

    return options, args

def threshold_parse(threshold):
    splits = threshold.split(':')
    if len(splits) == 1:
        high = int(threshold)
        low = None
    else:
        if len(splits[0]) == 0:
            low = None
        else:
            low = int(splits[0])
        if len(splits[1]) == 0:
            high = None
        else:
            high = int(splits[1])

    return low, high

if __name__ == "__main__":
    sys.exit(main())
