#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_zone_zoneset
extends_documentation_fragment: nxos
version_added: 2.9
short_description: Configuration of zone/zoneset.
description:
    - List or print  zone/zoneset for Cisco MDS NXOS.
author:
    - Shankar T (S.THANGARAJ@dell.com)
options:
    nxos_dellemc_cisco_mds_zones:
        description:
            - List of zone/zoneset details
        type: show zones and Zoneset and Track  Status
        suboptions:
            zoneverify:
                description:
                    -list zone by Name or all
            
            zonesetverify:
                description:
                    -list zoneset by name or all
                    
            zonesetstate:
                description:
                    - Get status odf Zone
            zoneclone:
                description:
                    - Clone Zone
           zonesetclone:
                description:
                    - Clone Zoneset
          
               
'''

EXAMPLES = '''
---
-
   - name: Test that zone/zoneset module works
      nxos_dellemc_cisco_mds_zones:
        provider: "{{ creds }}"
        zoneverify:
          - name: "zonenamesample"
            vsan: 11
         zoneverify:
          - name: "all"
            vsan: 11
        zonesetverify:
          - name: "zonesetsample"
            vsan: 11
        zonesetverify:
          - name: "all"
            vsan: 11  
        zonesetstate:
          - name: "zonesetsample"
            vsan: 12 
         zoneclone:
          - name: "SampleZonename"
            newname: "NewZonename"
            vsan: 11
        zonesetclone:
          - name: "SampleZonesetname"
            newname: "newZonesetname"
            vsan: 11

'''

RETURN = '''
commands:
  description: commands sent to the device
  returned: always
  type: list
  sample:
    - terminal dont-ask
    - zone name zoneA vsan 923
    - member pwwn 11:11:11:11:11:11:11:11
    - no member device-alias test123
    - zone commit vsan 923
    - no terminal dont-ask
    - zone clone s_cluster1_11AA0FC00_11BB0FC02 demoTest vsan 11
	- zoneset clone DEMOTestZoneset1 DEMOTestZonesetclone vsan 11
    - zone commit vsan 11

'''


import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import load_config, nxos_argument_spec, run_commands


__metaclass__ = type


class ShowZonesetActive(object):
    """docstring for ShowZonesetActive"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.module = module
        self.activeZSName = None
        self.parseCmdOutput()

    def execute_show_zoneset_active_cmd(self):
        command = 'show zoneset active vsan ' + str(self.vsan) + ' | grep zoneset'
        output = execute_show_command(command, self.module)[0]
        return output

    def parseCmdOutput(self):
        patZoneset = r"zoneset name (\S+) vsan " + str(self.vsan)
        output = self.execute_show_zoneset_active_cmd().split("\n")
        if len(output) == 0:
            return
        else:
            for line in output:
                line = line.strip()
                mzs = re.match(patZoneset, line.strip())
                if mzs:
                    self.activeZSName = mzs.group(1).strip()
                    return

    def isZonesetActive(self, zsname):
        if zsname == self.activeZSName:
            return True
        return False


class ShowZoneset(object):
    """docstring for ShowZoneset"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.module = module
        self.zsDetails = {}
        self.parseCmdOutput()

    def execute_show_zoneset_cmd(self):
        command = 'show zoneset vsan ' + str(self.vsan)
        output = execute_show_command(command, self.module)[0]
        return output

    def parseCmdOutput(self):
        patZoneset = r"zoneset name (\S+) vsan " + str(self.vsan)
        patZone = r"zone name (\S+) vsan " + str(self.vsan)
        output = self.execute_show_zoneset_cmd().split("\n")
        for line in output:
            line = line.strip()
            mzs = re.match(patZoneset, line.strip())
            mz = re.match(patZone, line.strip())
            if mzs:
                zonesetname = mzs.group(1).strip()
                self.zsDetails[zonesetname] = []
                continue
            elif mz:
                zonename = mz.group(1).strip()
                v = self.zsDetails[zonesetname]
                v.append(zonename)
                self.zsDetails[zonesetname] = v

    def isZonesetPresent(self, zsname):
        return zsname in self.zsDetails.keys()

    def isZonePresentInZoneset(self, zsname, zname):
        if zsname in self.zsDetails.keys():
            return zname in self.zsDetails[zsname]
        return False


class ShowZone(object):
    """docstring for ShowZone"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.module = module
        self.zDetails = {}
        self.parseCmdOutput()

    def execute_show_zone_vsan_cmd(self):
        command = 'show zone vsan ' + str(self.vsan)
        output = execute_show_command(command, self.module)[0]
        return output

    def parseCmdOutput(self):
        patZone = r"zone name (\S+) vsan " + str(self.vsan)
        output = self.execute_show_zone_vsan_cmd().split("\n")
        for line in output:
            line = ' '.join(line.strip().split())
            m = re.match(patZone, line)
            if 'init' in line:
                line = line.replace('init', 'initiator')
            if m:
                zonename = m.group(1).strip()
                self.zDetails[zonename] = []
                continue
            else:
                # For now we support only pwwn and device-alias under zone
                # Ideally should use 'supported_choices'..maybe next time.
                if "pwwn" in line or "device-alias" in line:
                    v = self.zDetails[zonename]
                    v.append(line)
                    self.zDetails[zonename] = v

    def isZonePresent(self, zname):
        return zname in self.zDetails.keys()

    def isZoneMemberPresent(self, zname, cmd):
        if zname in self.zDetails.keys():
            zonememlist = self.zDetails[zname]
            for eachline in zonememlist:
                if cmd in eachline:
                    return True
        return False

    def listZones(self):
        patZone = r"zone name (\S+) vsan " + str(11)
        output = self.execute_show_zone_vsan_cmd().split("\n")
        zDetails=[]
        for line in output:
            line = ' '.join(line.strip().split())
            m = re.match(patZone, line)
            if 'init' in line:
                line = line.replace('init', 'initiator')
            if m:
                zonename = m.group(1).strip()
                self.zDetails[zonename] = []
                continue
            else:
                # For now we support only pwwn and device-alias under zone
                # Ideally should use 'supported_choices'..maybe next time.
                if "pwwn" in line or "device-alias" in line:
                    v = self.zDetails[zonename]
                    v.append(line)
                    self.zDetails[zonename] = v
        return zDetails

class ShowZoneStatus(object):
    """docstring for ShowZoneStatus"""

    def __init__(self, module, vsan):
        self.vsan = vsan
        self.vsanAbsent = False
        self.module = module
        self.default_zone = ""
        self.mode = ""
        self.session = ""
        self.sz = ""
        self.locked = False
        self.update()

    def execute_show_zone_status_cmd(self):
        command = 'show zone status vsan ' + str(self.vsan)
        output = execute_show_command(command, self.module)[0]
        return output

    def update(self):

        output = self.execute_show_zone_status_cmd().split("\n")

        patfordefzone = "VSAN: " + str(self.vsan) + r" default-zone:\s+(\S+).*"
        patformode = r".*mode:\s+(\S+).*"
        patforsession = r"^session:\s+(\S+).*"
        patforsz = r".*smart-zoning:\s+(\S+).*"
        for line in output:
            if "is not configured" in line:
                self.vsanAbsent = True
                break
            mdefz = re.match(patfordefzone, line.strip())
            mmode = re.match(patformode, line.strip())
            msession = re.match(patforsession, line.strip())
            msz = re.match(patforsz, line.strip())

            if mdefz:
                self.default_zone = mdefz.group(1)
            if mmode:
                self.mode = mmode.group(1)
            if msession:
                self.session = msession.group(1)
                if self.session != "none":
                    self.locked = True
            if msz:
                self.sz = msz.group(1)

    def isLocked(self):
        return self.locked

    def getDefaultZone(self):
        return self.default_zone

    def getMode(self):
        return self.mode

    def getSmartZoningStatus(self):
        return self.sz

    def isVsanAbsent(self):
        return self.vsanAbsent


def execute_show_command(command, module, command_type='cli_show'):
    output = 'text'
    commands = [{
        'command': command,
        'output': output,
    }]
    return run_commands(module, commands)


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def getMemType(supported_choices, allmemkeys, default='pwwn'):
    for eachchoice in supported_choices:
        if eachchoice in allmemkeys:
            return eachchoice
    return default


def main():

    supported_choices = ['device-alias']
    zone_member_spec = dict(
        pwwn=dict(required=True, type='str', aliases=['device-alias']),
        devtype=dict(type='str', choices=['initiator', 'target', 'both']),
        remove=dict(type='bool', default=False)
    )

    zone_spec = dict(
        name=dict(required=True, type='str'),
        members=dict(type='list', elements='dict', options=zone_member_spec),
        remove=dict(type='bool', default=False),
        #verifyzonename=dict(type='str')
    )

    zoneverify_spec = dict(
        name=dict(required=True, type='str'),
        vsan=dict(required=True, type='int')
        #verifyzonename=dict(type='str')
    )

    zonesetverify_spec = dict(
        name=dict(required=True, type='str'),
        vsan=dict(required=True, type='int')
        #verifyzonename=dict(type='str')
    )

    zonelist_spec = dict(
        #name=dict(required=True, type='str'),
        vsan=dict(required=True, type='int')
        #verifyzonename=dict(type='str')
    )

    zonesetstate_spec = dict(
        name=dict(required=True, type='str'),
        vsan=dict(required=True, type='int')
        #verifyzonename=dict(type='str')
    )

    zoneset_member_spec = dict(
        name=dict(required=True, type='str'),
        remove=dict(type='bool', default=False)
    )

    zoneset_spec = dict(
        name=dict(type='str', required=True),
        members=dict(type='list', elements='dict', options=zoneset_member_spec),
        remove=dict(type='bool', default=False),
        action=dict(type='str', choices=['activate', 'deactivate'])
    )

    zonedetails_spec = dict(
        vsan=dict(required=True, type='int'),
        mode=dict(type='str', choices=['enhanced', 'basic']),
        default_zone=dict(type='str', choices=['permit', 'deny']),
        smart_zoning=dict(type='bool'),
        zone=dict(type='list', elements='dict', options=zone_spec),
        zoneset=dict(type='list', elements='dict', options=zoneset_spec)
    )

    zoneclone_spec = dict(
        name=dict(required=True, type='str'),
        newname=dict(required=True, type='str'),
        vsan=dict(required=True, type='int')
       
    )

    zonesetclone_spec = dict(
        name=dict(required=True, type='str'),
        newname=dict(required=True, type='str'),
        vsan=dict(required=True, type='int')
       
    )

    argument_spec = dict(
        zone_zoneset_details=dict(type='list', elements='dict', options=zonedetails_spec),
        zoneverify=dict(type='list', elements='dict',options=zoneverify_spec),
        zonesetverify=dict(type='list', elements='dict',options=zonesetverify_spec),
        zonesetstate=dict(type='list', elements='dict',options=zonesetstate_spec),
        zoneclone=dict(type='list', elements='dict',options=zoneclone_spec),
        zonesetclone=dict(type='list', elements='dict',options=zonesetclone_spec)
        
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    messages = list()
    commands = list()
    result = {'changed': False}

    commands_executed = []

       
    
    if module.params['zoneverify'] is not None:
        zoneverifyDetail =  module.params['zoneverify']
        for zoneverifydata in zoneverifyDetail:
            shZoneObj = ShowZone(module, str(zoneverifydata['vsan']))
            if zoneverifydata['name'] == "all":
                messages.append("ZONE LIST:" + ' '.join([str(elem) for elem in shZoneObj.zDetails])) 
            #commands_executed.append("show zone vsan 11")
            else:
                if shZoneObj.isZonePresent(zoneverifydata['name']):
                    messages.append("ZONE FOUND")
                else:
                    messages.append("ZONE NOT FOUND")

    if module.params['zonesetverify'] is not None: 
        zonesetverifyDetail =  module.params['zonesetverify']
        for zonesetverifydata in zonesetverifyDetail:
             shZonesetObj = ShowZoneset(module, str(zonesetverifydata['vsan']))
             if zonesetverifydata['name'] == "all":
                messages.append("ZONESSET LIST:" + ' '.join([str(elem) for elem in shZonesetObj.zsDetails])) 
             else:
                #commands_executed.append("show zone vsan 11")
                if shZonesetObj.isZonesetPresent(zonesetverifydata['name']):
                    messages.append("ZONESET FOUND")
                else:
                    messages.append("ZONESET NOT FOUND")

    if module.params['zonesetstate'] is not None: 
        zonesetstateDetail =  module.params['zonesetstate']
        for zonesetstatedata in zonesetstateDetail:
            shZonesetstateObj = ShowZonesetActive(module, str(zonesetstatedata['vsan']))
            #commands_executed.append("show zone vsan 11")
            if shZonesetstateObj.isZonesetActive(zonesetstatedata['name']):
                messages.append("ZONESET ACTIVE")
            else:
                messages.append("ZONESET INACTIVE")

    if module.params['zoneclone'] is not None: 
        zoneverifyDetail =  module.params['zoneclone']
        for zoneverifydata in zoneverifyDetail:
            shZoneObj = ShowZone(module, str(zoneverifydata['vsan']))
            if shZoneObj.isZonePresent(zoneverifydata['newname']):
                messages.append("Target zone name already in use. Specify a new name.")
            else:
                commands_executed.append("zone clone "+zoneverifydata['name']+" "+ zoneverifydata['newname'] +" vsan "+str(zoneverifydata['vsan']))
                commands_executed.append("zone commit vsan "+str(zoneverifydata['vsan']))
                messages.append("Zone Clone Completed")
    
    if module.params['zonesetclone'] is not None: 
        zonesetverifyDetail =  module.params['zonesetclone']
        for zonesetclonedata in zonesetverifyDetail:
            shZoneObj = ShowZoneset(module, str(zonesetclonedata['vsan']))
            if shZoneObj.isZonesetPresent(zonesetclonedata['newname']):
                messages.append("Target zoneset name already in use. Specify a new name.")
            else:
                commands_executed.append("zoneset clone "+zonesetclonedata['name']+" "+ zonesetclonedata['newname'] +" vsan "+str(zonesetclonedata['vsan']))
                commands_executed.append("zone commit vsan "+str(zonesetclonedata['vsan']))
                messages.append("Zoneset Clone Completed")

    if commands_executed:
        commands_executed = ["terminal dont-ask"] + commands_executed + ["no terminal dont-ask"]

    cmds = flatten_list(commands_executed)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=False, commands=cmds, msg="Check Mode: No cmds issued to the hosts")
        else:
            result['changed'] = True
            commands = commands + cmds
            load_config(module, cmds)

    result['messages'] = messages
    result['commands'] = commands_executed
    result['warnings'] = warnings
    module.exit_json(**result)


if __name__ == '__main__':
    main()