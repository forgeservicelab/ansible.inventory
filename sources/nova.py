#!/usr/bin/env python

# (c) 2012 Marco Vito Moscaritolo <marco@agavee.com>
# modified by Tomas Karasek <tomas.karasek@digile.fi>
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
inventory: nova2
short_description: OpenStack external inventory script
description:
  - |
    Generates inventory that Ansible can understand by making API
    request to OpenStack endpoint using the novaclient library.
  - |
    When run against a specific host, this script returns following variables:
        os_os-ext-sts_task_state
        os_addresses
        os_links
        os_image
        os_os-ext-sts_vm_state
        os_flavor
        os_id
        os_rax-bandwidth_bandwidth
        os_user_id
        os_os-dcf_diskconfig
        os_accessipv4
        os_accessipv6
        os_progress
        os_os-ext-sts_power_state
        os_metadata
        os_status
        os_updated
        os_hostid
        os_name
        os_created
        os_tenant_id
        os__info
        os__loaded
    where some items can have nested structure.
version_added: None
options:
  an_option_name:
    description:
      - desc line 1
      - desc line 2
    required: false
    default: null
author: Tomas Karasek
notes:
  - This script assumes following environment variables are set:
  - OS_AUTH_URL, OS_TENANT_NAME, OS_USERNAME, OS_PASSWORD
  - You can get a shellscript that sets them in your OpenStack dashboard.
  - For more details, see U(https://github.com/openstack/python-novaclient)
examples:
    - description: List instances
      code: nova.py --list
    - description: Show instance properties
      code: nova.py --instance INSTANCE_IP
'''


import sys
import re
import os
import novaclient.client

class NovaInventoryError(Exception):
    pass

try:
    import json
except:
    import simplejson as json


###################################################
# executed with no parameters, return the list of
# all groups and hosts


client = novaclient.client.Client(
    version     = '1.1',
    username    = os.environ['OS_USERNAME'],
    api_key     = os.environ['OS_PASSWORD'],
    auth_url    = os.environ['OS_AUTH_URL'],
    project_id  = os.environ['OS_TENANT_NAME'],
)


def getAccessIP(vm):
    private = [ x['addr'] for x
                in getattr(vm, 'addresses').itervalues().next()
                if x['OS-EXT-IPS:type'] == 'fixed'
              ]
    public  = [ x['addr'] for x
                in getattr(vm, 'addresses').itervalues().next()
                if x['OS-EXT-IPS:type'] == 'floating'
              ]
    access_ip = vm.accessIPv4 or public or private
    if access_ip:
        access_ip = ''.join(access_ip)
    else:
        raise NovaInventoryError("Cant figure public ip of %s" % vm)
    return access_ip

def getSshUser(vm):
    ssh_user = 'root'
    try:
        image_name = client.images.get(vm.image['id']).name
        if 'ubuntu' in image_name.lower():
            ssh_user = 'ubuntu'
        if 'centos' in  image_name.lower():
            ssh_user = 'cloud-user'
    except:
        pass
    return ssh_user

def getServerGroups(vm):
    if 'groups' in vm.metadata:
        servers_groups = vm.metadata['groups'].split(',')
    else:
        return ['nova']


if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
    groups = {}
    groups['_meta'] = {'hostvars': {}}

    # Cycle on servers
    for f in client.servers.list():
        access_ip = getAccessIP(f)

        # Define group (or set to empty string)
        servers_groups = getServerGroups(f)
        # servers name is another group - alias
        servers_groups.append(f.name)

        # Create group if not exist
        for g in servers_groups:
            if g not in groups:
                groups[g] = []

        for g in servers_groups:
            groups[g].append(access_ip)
        user = getSshUser(f)
        groups['_meta']['hostvars'][access_ip] = {
            'ansible_ssh_host': access_ip,
            'ansible_ssh_user': user}

    # Return server list
    print json.dumps(groups)
    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
    results = {}
    for instance in client.servers.list():
        access_ip = getAccessIP(instance)

        if sys.argv[2] in instance.name or sys.argv[2] == access_ip:
            for key in vars(instance):
                # Extract value
                value = getattr(instance, key)

                # Generate sanitized key
                key = 'os_' + re.sub("[^A-Za-z0-9\-]", "_", key).lower()

                # Att value to instance result (exclude manager class)
                #TODO: maybe use value.__class__ or similar inside of key_name
                if key != 'os_manager':
                    results[key] = value

    print json.dumps(results)
    sys.exit(0)

else:
    print "usage: --list  ..OR.. --host <hostname>"
    sys.exit(1)
