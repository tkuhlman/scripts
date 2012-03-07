#!/usr/bin/env python
#
""" Recursively upload a directoy to an s3 bucket setting the content-type, cache-control and expires headers.
    Connection credentials come from one of the standard boto methods http://code.google.com/p/boto/wiki/BotoConfig
"""

from datetime import datetime
import os
import sys

import boto

S3POLICY = 'public-read' #private is the next most common.

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) != 3:
        print "Usage: " + argv[0] + " <source dir> <bucket/prefix>"
        return 1

    src_dir = argv[1]
    splits = argv[2].split('/', 1)
    bucketname = splits[0]
    if len(splits) > 1:
        prefix = splits[1] + '/'
    else:
        prefix = ""

    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucketname, validate=False)

    #Headers to use in uploading the files
    s3headers = {'Expires': datetime(2022, 1, 1).strftime('%a, %d %b %Y %H:%M:%S GMT'), \
        'Cache-Control': 'max-age=315360000' }

    for dirpath, dirs, files in os.walk(src_dir):
        for filename in files:
            path = os.path.join(dirpath, filename)
            keyname = prefix + path.replace(src_dir, '')
            fileobj = open(path, 'rb')
            try:
                key = boto.s3.key.Key(bucket, name = keyname)
                key.set_contents_from_file(fileobj, headers = s3headers, policy = S3POLICY)
            except boto.exception, msg:
                print 'Error uploading to ' + keyname + ':' + msg
            finally:
                fileobj.close()


if __name__ == "__main__":
    sys.exit(main())
