Interface Monitoring
====================

# Description
This script creates a NXOS guest-shell process that will detect specific virtual machines within connected hypervisors.


# Contents

* nexus_interface_monitor.py
  - This is a valid and function script that can be run from any Nexus Guest shell. 

## Installing 
 
Install the scripts to your NXOS filesystem
    
scp nexus_interface_monitor.py user@nexusswitch

##Usage

From a guest shell on NXOS, run vm_detection -h for usage parameters

#Support
As of 12/1/15 this script supports ESX 5.x/6.x, KVM and Citrix Xen
    
# License

Copyright 2014-2015 Cisco Systems, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


