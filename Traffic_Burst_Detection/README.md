Traffic Burst Detection
====================

# Description
This script creates a NXOS guest-shell process that will detect bursts in traffic on any available Nexus Interface.


# Contents

* vm_detection.py
  - This is a valid and function script that can be run from any Nexus Guest shell. 
  
* config.txt


## Installing 
 
Install the scripts to your NXOS filesystem
    
scp config.txt user@nexusswitch
scp trafficburstdetection.py user@nexusswith

##Usage

From a guest shell on NXOS, run vm_detection -h for usage parameters

The associated file called config.txt is read by the script to set specific thresholds to be triggered. 

The options are:

input rate: 2222222222
txload: 333
rxload: 10
packets input: 6666666
packets output: 44444444444


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


