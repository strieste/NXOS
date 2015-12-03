Layer 2 Traceroute
====================

# Description
This script creates a NXOS guest-shell process that will perform a traceroute-like operation across a layer 2 network in order to calculate a bridging path.


# Contents

* layer_2_traceroute.py
  - This is a valid and function script that can be run from any Nexus Guest shell. 

## Installing 
 
Install the scripts to your NXOS filesystem
    
scp layer_2_traceroute.py user@nexusswitch

##Usage

 layer_2_traceroute.py -u admin -p 4u2kn0w -s esw1 -m 08:00:27:3e:cc:6a

Add flag -t if you wish connect via telnet. If flag -t omitted, the connection will done via ssh.

If there are errors, use flag -v for verbose.


#Support
As of 12/1/15 this script supports NXOS, and IOS
    
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


