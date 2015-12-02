#!/usr/bin/python
import sys
import re
import optparse
from netaddr import EUI
import netaddr


def get_port_for_mac(data, mac):
    learnedmacport = ""
    for line in data:
        if line.find(str(mac)) != -1:
            values = line.split()
            learnedmacport = values[3]
    return learnedmacport


mac = EUI('01-23-45-67-89-0A')

DEFAULTUSER = 'admin'
DEFAULTPW = '1vtG@lw@y'
MAX_HOPS = 100
EXPECT_TIMEOUT = 6

usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage=usage)
parser.add_option("-u", "--user", type="string", dest="username", help="Username for switch", metavar="username",
                  default=DEFAULTUSER)
parser.add_option("-p", "--password", type="string", dest="password", help="Password for switch", metavar="password",
                  default=DEFAULTPW)
parser.add_option("-s", "--switch", type="string", dest="next_switch_ip", help="Ip-address for the first switch",
                  metavar="Ip Address")
parser.add_option("-m", "--mac", type="string", dest="mac", help="MAC Address to Traceroute on", metavar="MAC")
parser.add_option('-v', "--verbose", action="store_true", default=False, dest="verbose")
parser.add_option('-t', "--telnet", action="store_true", default=False, dest="telnet",
                  help="Use telnet for connections")
(options, args) = parser.parse_args()

if not options.mac:
    print "MAC address required as argument to execute mactrace"
    parser.print_help()
    sys.exit(0)


def die(msg):
    print msg
    sys.exit(1)


MAC = EUI(options.mac)
MAC.dialect = netaddr.mac_cisco
start = 1
print "Search MAC: %s" % MAC

next_switch_ip = options.next_switch_ip
if not next_switch_ip or next_switch_ip == "":
    import json

    hostname = json.loads(clid("show hostname"))
    hostname = hostname["hostname"]
    out = json.loads(clid("show mac address-table address %s" % options.mac))
    learnedmacport = out['TABLE_mac_address']['ROW_mac_address']["disp_port"]
    print "%d %s %s" % (start, hostname, learnedmacport)
    start += 1
    mac_count = int(cli("show mac address-table interface %s | count" % learnedmacport)[1])
    if mac_count <= 1:
        sys.exit(0)
    else:
        next_switch_ip = cli("show cdp neighbors interface %s detail" % learnedmacport)[1]
        next_switch_ip.replace('\n', ' ')
        res = re.search("\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s", next_switch_ip)
        if res:
            next_switch_ip = res.group().strip()
        else:
            die(
                "Not found matching to regexp '\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s' from: 'show cdp neighbors interface %s detail' on %s n" % (
                learnedmacport, hostname))

for num in range(start, MAX_HOPS + start):
    if options.telnet:
        import pexpect

        child = pexpect.spawn('telnet %s' % next_switch_ip, maxread=30000)
        if options.verbose:
            child.logfile = sys.stdout
        child.expect('[Uu]sername:\s|[Ll]ogin:\s')
        child.sendline(options.username)
        child.expect('Password: ')
        child.sendline(options.password)
        child.expect("#")
        child.sendline('terminal length 0')
        child.expect("#")
        child.sendline('show mac address-table address %s' % MAC)
        res = child.expect(["#", "% Invalid"])
        if res == 1:
            child.expect("#")
            child.sendline('show mac-address-table address %s' % MAC)
            child.expect("#")
        data = child.before.splitlines()
        learnedmacport = get_port_for_mac(data, MAC)
        if (learnedmacport == ""):
            die("Can't find macport")

        child.sendline('show run')
        child.expect("#")
        data = re.search('(\s+|^)[Hh]ostname(\s+)(\S+)', child.before)
        hostname = ""
        if data:
            hostname = data.group(3)
        if hostname != "":
            print "%d %s (%s) %s" % (num, hostname, next_switch_ip, learnedmacport)
        else:
            print "%d %s %s" % (num, next_switch_ip, learnedmacport)

        child.sendline("show cdp nei %s detail" % learnedmacport)
        child.expect("#")
        data = child.before
        res = re.search("\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s", data)
        next_switch_ip = ""
        if res:
            next_switch_ip = res.group(1).strip()
        if (next_switch_ip == ""):
            sys.exit(0)
    else:
        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(hostname=next_switch_ip, username=options.username, password=options.password, port=22)
        _, stdout, stderr = client.exec_command('show mac address-table address %s' % MAC)
        data = stdout.read()
        check = data + stderr.read()
        if check.find("Line has invalid") != -1:
            client.connect(hostname=next_switch_ip, username=options.username, password=options.password, port=22)
            _, stdout, _ = client.exec_command('show mac-address-table address %s' % MAC)
            data = stdout.read()

        data = data.splitlines()
        learnedmacport = get_port_for_mac(data, MAC)
        if (learnedmacport == ""):
            die("Can't find macport")

        client.connect(hostname=next_switch_ip, username=options.username, password=options.password, port=22)
        _, stdout, _ = client.exec_command('show run')
        data = stdout.read()
        data = re.search('(\s+|^)[Hh]ostname(\s+)(\S+)', data)
        hostname = ""
        if data:
            hostname = data.group(3)
        if hostname != "":
            print "%d %s (%s) %s" % (num, hostname, next_switch_ip, learnedmacport)
        else:
            print "%d %s %s" % (num, next_switch_ip, learnedmacport)

        client.connect(hostname=next_switch_ip, username=options.username, password=options.password, port=22)
        _, stdout, _ = client.exec_command("show cdp nei %s detail" % learnedmacport)
        data = stdout.read()
        res = re.search("\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s", data)
        next_switch_ip = ""
        if res:
            next_switch_ip = res.group(1).strip()
        if (next_switch_ip == ""):
            sys.exit(0)
