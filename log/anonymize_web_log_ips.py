#!/usr/bin/env python
""" Takes an apache web log and replaces ips with a number to allows for anonymized analysis.
    Optionally some ips can be striped also.
"""
import sys

def skip_ip(ip, skip_ips):
    """ Return true if ip startswith any of the ips in the skip_ips list """
    for skip_ip in skip_ips:
        if ip.startswith(skip_ip):
            return True

    return False

def main(argv=None):
    if argv is None:
        argv = sys.argv

    skip_ips = None
    if len(argv) < 2:
        print('Usage: {} <path to web log with ip as first component> [ip prefix to skip]')
    elif len(argv) > 2:
        skip_ips = sys.argv[2:]

    ips = {}
    with open(argv[1] + '.anonymized', 'w') as new_file:
        with open(argv[1], 'r') as log_file:
            for line in log_file:
                splits = line.split()
                ip = splits[0]
                if skip_ips is not None and skip_ip(ip, skip_ips):
                    continue

                if not ips.has_key(ip):
                    ips[ip] = str(len(ips))

                anonymized_line = "{} {}\n".format(ips[ip], ' '.join(splits[1:]))
                new_file.write(anonymized_line)


if __name__ == "__main__":
    sys.exit(main())
