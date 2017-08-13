from cli import configure, cli
import urllib2, base64
import socket, struct
import json
import time
CONFIG_SERVER="10.66.104.91"

USER="cisco"
PASSWORD="cisco"
ENABLE="cisco"

def base_config():
    configure(['hostname adam-ztd'])
    configure(['username {} privilege 15 password {}'.format(USER,PASSWORD)])
    configure(['enable secret {}'.format(ENABLE)])
    configure(['line vty 0 4', 'login local'])
    print "\n *** restconf *** \n"
    configure(['restconf'])
    print "\n *** sleeping 20 ** \n"
    time.sleep(20)


def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue
            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


def get_my_serial(my_gateway):
    serials = {}
    ### switches not CSR
    url = 'https://{}/restconf/data/Cisco-IOS-XE-platform-oper:components/component?fields=cname;state/serial-no'.format(
    my_gateway)
    request = urllib2.Request(url)
    base64string = base64.b64encode('%s:%s' % ('cisco', 'cisco'))
    request.add_header("Authorization", "Basic %s" % base64string)
    request.add_header('accept', 'application/yang-data+json')
    response = json.load(urllib2.urlopen(request))

    for component in response['Cisco-IOS-XE-platform-oper:component']:
        if 'Switch' in component['cname'] and component['state']['serial-no'] != '':
            serials[component['cname']] = component['state']['serial-no']
    return serials



def get_my_config(serials):
    base = 'http://{}:1880/device?serial='.format(CONFIG_SERVER)
    url =  base + '&serial='.join(serials.values())
    print url
    configs = json.load(urllib2.urlopen(url))
    return configs

def configure_network(**kwargs):
    if 'ip' in kwargs and kwargs['ip'] is not None:
        print kwargs['ip']
        configure(['int g0/0','ip address {} {}'.format(kwargs['ip'], kwargs['netmask'])])
        configure(['ip route vrf Mgmt-vrf 0.0.0.0 0.0.0.0 {}'.format(kwargs['gw'])])


def ending():
    # a choice of endings
    #to save config and stop ZTD process
    #cli('wr mem')

    # will reload and restart the process again
    # ccli('reload')

    # to initiate PnP to APIC-EM, does not work
    #print "Handing over to PnP"
    #configure(['pnp profile fromZTD','transport http ipv4 10.66.104.80 port 80'])

    print "END"

base_config()
my_gateway = get_default_gateway_linux()
print "GW", my_gateway
serials = get_my_serial(my_gateway)
print "Serials", serials
config = get_my_config(serials)
print "config", config
# if switch1 serial is not in the config, then need to renumber...
# and reboot
configure_network(**config)
ending()










