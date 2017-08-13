from cli import configure, cli
from xml.dom import minidom
import re
import json
import urllib2
import sys

CONFIG_SERVER='10.10.10.151'

USER="cisco"
PASSWORD="cisco"
ENABLE="cisco"

def log(message, severity):
    cli('send log %d "%s"' % (severity, message))

def base_config():
    configure(['hostname adam-ztd'])
    configure(['username {} privilege 15 password {}'.format(USER,PASSWORD)])
    configure(['enable secret {}'.format(ENABLE)])
    configure(['line vty 0 4', 'login local'])

def get_serials():
    # xml formatted
    inventory = cli('show inventory | format')
    # skip leading newline
    doc = minidom.parseString(inventory[1:])
    serials =[]
    for node in doc.getElementsByTagName('InventoryEntry'):
        # router, what if there are several?
        chassis = node.getElementsByTagName('ChassisName')[0]
        if chassis.firstChild.data == "Chassis":
            serials.append(node.getElementsByTagName('SN')[0].firstChild.data)
        # switch
        match = re.match('"Switch ([0-9])"', chassis.firstChild.data)
        if match:
            serials.append(node.getElementsByTagName('SN')[0].firstChild.data)

    return serials

def get_my_config(serials):
    # define your own REST API CALL
    base = 'http://{}:1880/device?serial='.format(CONFIG_SERVER)
    url =  base + '&serial='.join(serials)
    log('Getting config from: {}'.format(url), 5)
    configs = json.load(urllib2.urlopen(url))
    return configs

def renumber_stack(serials, serial):
    # find position of the correct switch #1 in the list
    index = serials.index(serial)
    index +=1
    if index <> 1:
        log("Renumbering switch top of stack".format(index),5)
        cli('test pnpa service stack renumber-tos {}'.format(index))
        cli('reload')
        sys.exit(1)
    else:
        log('No need to renumber stack')

def configure_network(**kwargs):
    if 'ip' in kwargs and kwargs['ip'] is not None:
        log('Configuring IP address: {}'.format(kwargs['ip']),5)
        configure(['int g0/0','ip address {} {}'.format(kwargs['ip'], kwargs['netmask'])])
        configure(['ip route vrf Mgmt-vrf 0.0.0.0 0.0.0.0 {}'.format(kwargs['gw'])])


base_config()
serials = get_serials()
log('platform serial numbers:{}'.format(','.join(serials)),5)
config = get_my_config(serials)

# check the renumber option
renumber_stack(serials, config['serial'])
configure_network(**config)
