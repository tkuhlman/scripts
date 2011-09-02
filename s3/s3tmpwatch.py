#!/usr/bin/env python
#
""" S3 tmpwatch
Given a number of days and an s3 path recursively delete anything in the path older than the number of days.
"""

import boto
from datetime import datetime, timedelta
import os
import sys

ACCESSKEY = os.environ['AWS_ACCESS_ID']
SECRETKEY = os.environ['AWS_SECRET_KEY']

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) != 3:
        print "Usage: " + argv[0] + " <days> <s3 path>"
        return 1

    days = int(argv[1])
    splits = argv[2].split('/', 1)
    bucketname = splits[0]
    if len(splits) > 1:
        prefix = splits[1]
    else:
        prefix = None

    rm_date = datetime.now() - timedelta(days=days)
    conn = boto.connect_s3(ACCESSKEY, SECRETKEY)
    bucket = conn.get_bucket(bucketname, validate=False)

    for key in bucket.list(prefix):
        modified = datetime.strptime(key.last_modified, '%Y-%m-%dT%H:%M:%S.%fZ')
        if modified < rm_date:
            print 'Deleting ' + key.name
            key.delete()


if __name__ == "__main__":
    sys.exit(main())
