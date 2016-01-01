#!/usr/bin/env python
""" Takes an apache web log and replaces ips with a number to allows for anonymized analysis.
    Optionally some ips can be striped also.
"""
import argparse
import netaddr
import sys


def main():
    # Parse arguments, build skip_set and paths as needed
    parser = argparse.ArgumentParser()
    parser.add_argument('log_path', help='The path to the log to be anonymized')
    parser.add_argument('--output', '-o', help='Output file, defaults to input file'
                                               'with .anonymized extension')
    parser.add_argument('--skip', '-s', action='append', help='A cidr notation network for which any'
                                                       'for which any source traffic will be removed'
                                                       'from the final output. Can be specified multiple'
                                                       'times')
    parser.add_argument('--skip_private', action='store_true', default=False,
                        help='If specified remove any private source ips from the final file')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help='Verbose: output lines processed/skipped')
    args = parser.parse_args()

    if args.skip is not None:
        skip_ips = netaddr.IPSet()
        for cidr in args.skip:
            skip_ips.add(cidr)
    else:
        skip_ips = None
    if args.output is None:
        anonymized_path = args.log_path + '.anonymized'
    else:
        anonymized_path = args.output

    # Process the lines of the file
    ips = {}
    total = 0
    skip = 0
    with open(anonymized_path, 'w') as new_file:
        with open(args.log_path, 'r') as log_file:
            for line in log_file:
                total += 1
                splits = line.split()
                ip = netaddr.IPAddress(splits[0])
                if (args.skip_private and ip.is_private()) or (skip_ips is not None and ip in skip_ips):
                    skip += 1
                    continue

                if not ips.has_key(str(ip)):
                    ips[str(ip)] = str(len(ips))

                anonymized_line = "{} {}\n".format(ips[str(ip)], ' '.join(splits[1:]))
                new_file.write(anonymized_line)

    if args.verbose:
        print('Total lines processed {}, skipped {}'.format(total, skip))


if __name__ == "__main__":
    sys.exit(main())
