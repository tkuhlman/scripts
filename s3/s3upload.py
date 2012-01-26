#!/usr/bin/env python
#
""" S3 upload
    A simple script that will upload all files in a directory to an s3 bucket. It does not act recursively.
    Why implement yet another s3 tool? As of this writing no tools (only libraries) support multipart upload
    which is required for files larger than 5GB.
    This requires filechunkio from https://bitbucket.org/fabian/filechunkio/
"""

import logging
import os
import sys
import threading

import boto
from filechunkio import FileChunkIO

ACCESSKEY = os.environ['AWS_ACCESS_ID']
SECRETKEY = os.environ['AWS_SECRET_KEY']

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

def mpupload(bucket, keyname, path, file_size):
    """ Upload to s3 using multipart upload.
        One thread for each part, which means this can be a bandwidth hog for large files.
    """
    #split into 4 gigabyte file chunks
    chunk_size = 4294967296
    if file_size % chunk_size > 0:
        num_chunks = (file_size/chunk_size) + 1
    else:
        num_chunks = file_size/chunk_size

    mp = bucket.initiate_multipart_upload(keyname)
    offset = 0
    threads = []
    for chunk in range(1, num_chunks + 1):
        if chunk == num_chunks: #If this is the last go to the end of the file
            file_chunk = FileChunkIO(path, offset=offset)
        #Don't let the last chunk be too small
        elif chunk + 1 == num_chunks and file_size - (offset + chunk_size) < 5242880:
            file_chunk = FileChunkIO(path, offset=offset, bytes=chunk_size/2)
            offset = offset + chunk_size/2
        else:
            file_chunk = FileChunkIO(path, offset=offset, bytes=chunk_size)
            offset = offset + chunk_size
        log.debug('Uploading chunk %i of %i' % (chunk, num_chunks))
        mp_thread = threading.Thread(target=mp.upload_part_from_file, args=(file_chunk, chunk))
        mp_thread.start()
        threads.append(mp_thread)

    for mp_thread in threads: #Wait for all threads to finish
        if mp_thread.is_alive():
            mp_thread.join()

    mp.complete_upload()

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
        prefix = splits[1]
    else:
        prefix = ""

    error_count = 0
    conn = boto.connect_s3(ACCESSKEY, SECRETKEY)
    bucket = conn.get_bucket(bucketname, validate=False)

    #cycle through files uploading anything new
    for filename in os.listdir(src_dir):
        path = os.path.join(src_dir, filename)
        keyname = prefix + '/' + filename
        if os.path.isdir(path):
            log.debug('Skipping dir ' + path)
            continue
        key = bucket.get_key(keyname)
        if key is not None: #skip files already uploaded
            log.info('File %s is already at s3, skipping' % (filename))
            continue
        #I was verifying md5 to verify a complete upload but have stopped because s3 no longer provides
        #an md5 for multipart files, the etag is not a valid md5

        log.info('Uploading %s to %s/%s' % (path, bucketname, keyname))
        file_size = os.stat(path).st_size
        if file_size < 4294967296: #4GB and smaller do a normal upload
            fileobj = open(path, 'rb')
            try:
                key = boto.s3.key.Key(bucket, name = keyname)
                key.set_contents_from_file(fileobj, policy = 'private')
            except boto.exception, msg:
                log.error('Error uploading to ' + keyname + ':' + msg)
                error_count += 1
            finally:
                fileobj.close()
        else:
            try:
                mpupload(bucket, keyname, path, file_size)
            except boto.exception, msg:
                log.error('Error uploading to ' + keyname + ':' + msg)
                error_count += 1

    return error_count


if __name__ == "__main__":
    sys.exit(main())
