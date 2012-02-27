#!/usr/bin/env python
""" Removes a host and all services from nagios.
    The pynag library is used to do this.
"""

import sys

from pynag import Model, Control

#Default debian/ubuntu nagios locations
Model.cfg_file = '/etc/nagios3/nagios.cfg'
NAGIOS_BIN = '/usr/sbin/nagios3'
NAGIOS_CFG = '/etc/nagios3/nagios.cfg'
NAGIOS_INIT = '/etc/init.d/nagios3'

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) != 2:
        print "Usage: " + argv[0] + " <hostname>"
        return 1

    hostname = argv[1]

    #Begin deleting with services first
    remove_services(hostname)

    #Note if any hostgroup definitions contain hostnames they should be deleted here
    #In my setup hosts aleays define which hostgroups they belong to.

    #Delete the host itself last
    remove_host(hostname)

    #Check config and restart
    nd = Control.daemon(NAGIOS_BIN, NAGIOS_CFG, NAGIOS_INIT)
    if not nd.verify_config():
        print 'Config verification failed, run "nagios -v /etc/nagios/nagios.cfg" to identify the error'
        return 2
    nd.restart()

def remove_host(hostname):
    "Remove host and host extinfo for the given hostname."
    nag_hosts = Model.Host.objects.filter(host_name=hostname)
    if len(nag_hosts) != 1:
        print 'Hostname %s not found' % hostname
        return 1
    else:
        nag_host = nag_hosts[0]

    hostext_list = Model.ObjectFetcher('hostextinfo').filter(host_name=hostname)
    for hostext in hostext_list:
        print 'Removing hostextinfo for host %s' % hostext.host_name
        hostext.delete()

    print 'Removing host %s' % nag_host.host_name
    nag_host.delete()

def remove_services(hostname):
    "Remove all services for the given hostname."
    #To find services I use host_name__contains because of a limitation of pynag, the hostname field is
    # not parsed for ',' a service with multiple hostnames defined has a hostname attribute of all
    #them run together seperated by commas
    services = Model.Service.objects.filter(host_name__contains=hostname)

    for service in services:
        print 'removing service %s for host %s' % (service.service_description, hostname)
        if service.host_name == hostname:
            service.delete()
        else: #The service must define multiple host names
            new_list = []
            host_list = service.host_name.split(',')
            for host in host_list:
                if host != hostname:
                    new_list.append(host) 
            service.host_name = ','.join(new_list)

if __name__ == "__main__":
    sys.exit(main())
