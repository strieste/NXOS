Top Talkers
====================

# Description
This script creates a NXOS guest-shell process that will install tools needed to capture, process and report top talkers of network traffic on a nexus switch.


# Contents

* toptalkers.py
  - This is a valid and function script that can be run from any Nexus Guest shell. 

## Installing 
 
Install the scripts to your NXOS filesystem
    
scp toptalkers.py user@nexusswitch

##Usage

From a guest shell on NXOS, run toptalkers.py to execute.  This script will kick off and download and execute the tools it needs each time its run.

#Support
As of 12/1/15 this script supports softflowd 0.9.9 as well as any gcc compiler
    
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


