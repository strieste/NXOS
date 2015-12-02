Memory_and_CPU_Detection
====================

# Description
This script creates a NXOS guest-shell process that parses active CPU and Memory usage and can generate event based alerting.


# Contents

* memory_cpu_hog_detection.py
  - This is a valid and function script that can be run from any Nexus Guest shell. 

# Installation

## Environment

Linux system is preferred. 

For windows users, strongly recommend installing [cygwin](https://www.cygwin.com/).

Required

* Cisco NXOS Shell

## Installing 
 
Install the scripts to your NXOS filesystem
    
scp memory_cpu_hog_detection.py user@nexusswitch

    
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


