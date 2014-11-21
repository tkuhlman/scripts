#!/usr/bin/env python
""" Create TLS Server Certifciate
    This script creates server certicates using the fully qualified domain names given as arguments.
    It assumes the base directory is the CA dir and openssl is in the path

    To create your own CA the /usr/lib/ssl/misc/CA.pl script that ships with linux versions of OpenSSL can be used.
"""

import os, sys
from subprocess import Popen, PIPE, STDOUT

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) < 2:
        print "Usage: " + argv[0] + " <fqdn> [fqdn]"
        return 1

    print "Please enter the CA password"
    CAPASS = sys.stdin.readline()[:-1]

    for fqdn in argv[1:]:
        host = fqdn.split('.')[0]

        #Create the request
        req = Popen('openssl req -config ./openssl.cnf -newkey rsa:2048 -nodes -keyout ' + host + \
            '_private.pem -out ' + host + '_req.txt', stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
        req.stdin.write("\n\n\n\n" + fqdn + "\nDNS:" + host + "\n\n\n\n")        
        if req.wait() != 0:
            print 'Error in creating the certificate request for ' + fqdn
            continue

        #Sign the request
        os.putenv('CApassword', CAPASS)
        check = Popen('openssl ca -config ./openssl.cnf -in ' + host + '_req.txt -out ' + host + \
            '.pem -passin env:CApassword', stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
       
        (checkout, checkerror) = check.communicate("n\nn\n\n")
        print checkout, checkerror

        #At this point the user can review the cert and choose to commit or not
        print "Do the changes look correct? Commit? [y/n] ",
        choice = sys.stdin.readline()[:-1]
        if choice == 'y':
            print "Committing changes"
            sign = Popen('openssl ca -config ./openssl.cnf -in ' + host + '_req.txt -out ' + host + \
                '.pem -passin env:CApassword', stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
            sign.communicate("y\ny\n\n")
            if sign.wait() != 0:
                print 'Error in signing certificate request for ' + fqdn
        else:
            print "Cancelling changes"


        os.remove(host + '_req.txt')

if __name__ == "__main__":
    sys.exit(main())

