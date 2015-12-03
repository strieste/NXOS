Using IP SLA to Update Configurations
====================

# Description
This script creates a NXOS guest-shell process to demonstrate how IP SLA can be used to detect specific network events and then update network configurations based on that.


# Contents

* vm_detection.py
  - This is a valid and function script that can be run from any Nexus Guest shell. 

## Installing 
 
Install the scripts to your NXOS filesystem
    
scp ip_sla.py user@nexusswitch

##Usage

From a guest shell on NXOS, run ip_sla.py -h for usage parameters

#Support
=    
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


