activatezoneset
===============

Changes to a zone set do not take effect to a full zone set until you activate it. so	Role "activatezoneset"
Activates the specified zone set.

Requirements
------------

A zone set consists of one or more zones. A zone can be a member of more than one zone set and consists of multiple zone members. Members in a zone can access each other; members in different zones cannot access each other. Devices can belong to more than one zone.A zone set can be activated or deactivated as a single entity across all switches in the fabric. Only one zone set can be activated at any time. If zoning is not activated, all devices are members of the default zone. If zoning is activated, any device that is not in an active zone (a zone that is part of an active zone set) is a member of the default zone.

Role Variables
--------------

vsan_number : Specify the VSAN numeber for the Zonset Present

zoneset_name : Specify Zonesent name to activate

zoneset_action: activate  

Dependencies
------------
Set  environment for using an already registered Cisco MDS Swtich endpoint as per below format

 CISCO_MDS_ENDPOINT_NAME= Name of the endpoint
 
 CISCO_MDS_ENDPOINT_HOST= Cisco MDS Switch Hostname or IP Address
 
 CISCO_MDS_USER= Swtich Login ID
 
 CISCO_MDS_PASSWORD= Swtich Password

Example Playbook
----------------
```
---
- name: Converge
  hosts: localhost
  collections:
    - dtms.dellemc_cisco_collection
  tasks:
    - include_vars: vars.yml
    - name: "Include activatezoneset"
      include_role:
        name: "activatezoneset"
```
License
-------

Dell Proprietary 

Author Information
------------------

Shankar Thangaraj(S.Thangaraj@dell.com) - Digital Solutions
