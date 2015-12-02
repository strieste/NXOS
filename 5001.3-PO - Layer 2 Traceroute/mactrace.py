import pexpect
import json
import sys
import re
import optparse
import inspect

def macchk(mac):
   import re
   #Check mac format to be in the form of 0000.0000.0000
   # This is the format used in EOS
   if re.match("[0-9a-f]{4}([.])[0-9a-f]{4}(\\1[0-9a-f]{4}){1}$", mac.lower()):
      return 1
   else:
      return 0

DEFAULTUSER='admin'
DEFAULTPW='1vtG@lw@y'
SSH_NEWKEY = 'Are you sure you want to continue connecting'
MAX_HOPS = 100
EXPECT_TIMEOUT = 6

usage = "usage: %prog [options]"
parser = optparse.OptionParser(usage=usage)
parser.add_option("-u", "--user", type="string", dest="username", help="Username for switch",metavar="username",default=DEFAULTUSER)
parser.add_option("-p", "--password", type="string", dest="password", help="Password for switch",metavar="password",default=DEFAULTPW)
parser.add_option("-s", "--switch", type="string", dest="next_switch_ip", help="Ip-address for the first switch", metavar="Ip Address")
parser.add_option("-m", "--mac", type="string", dest="mac", help="MAC Address to Traceroute on",metavar="MAC")
parser.add_option('-v', "--verbose", action="store_true", default=False, dest="verbose")
(options, args) = parser.parse_args()

# Do some simple validation of mac
if options.mac:
   if not macchk(options.mac):
       print "MAC format not valid. You must enter MAC in the following format:  aaaa.bbbb.cccc"
       sys.exit(0)
else:
   print "MAC address required as argument to execute mactrace"
   parser.print_help()
   sys.exit(0)

def die(msg):
    print msg
    sys.exit(1)

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

next_switch_ip = options.next_switch_ip

start = 1
#if True - we on a switch
if next_switch_ip == None:
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
            die("Not found matching to regexp '\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s' from: 'show cdp neighbors interface %s detail' on %s n" % (learnedmacport, hostname))

for num in range(start, MAX_HOPS + start):
    child = pexpect.spawn('ssh %s@%s' % (options.username, next_switch_ip))
    if options.verbose:
        child.logfile = sys.stdout
    child.timeout = EXPECT_TIMEOUT
    res = child.expect([SSH_NEWKEY, '[Pp]assword:', pexpect.TIMEOUT])
    if res == 0:
        child.sendline('yes')
        res = child.expect([SSH_NEWKEY, '[Pp]assword:', pexpect.TIMEOUT])
    if res == 1:
        child.sendline(options.password)
    else:
        die("Timeout on %s while expecting regexp '[Pp]assword:' or line 'Are you sure you want to continue connecting'" % options.next_switch_ip)

    res = child.expect(['#', pexpect.TIMEOUT])
    if res != 0:
        die("Line: %d. Timeout on %s while expecting prompt symbol '#'" % (lineno(), options.next_switch_ip))

    #for hostname
    child.sendline('\n')
    res = child.expect(['#', pexpect.TIMEOUT])
    if res != 0:
        die("Line: %d. Timeout on %s while expecting prompt symbol '#'" % (lineno(), options.next_switch_ip))

    hostname = child.before.lstrip()
    child.sendline("show mac address-table address %s | json" % options.mac)
    res = child.expect(["(\{.*\}).*#", "([Ii]nvalid.*)\r\n", pexpect.TIMEOUT])
    if res == 1:
        die("Error on %s while run 'show mac address-table address %s | json': %s" % (options.next_switch_ip, options.mac, child.match.group(1)))
    if res == 2:
        die("Timeout on %s while expecting regexp '(\{.*\}).*#' from: 'show mac address-table address %s | json'. Probably %s doesn't exist here" % (options.next_switch_ip, options.mac, options.mac))

    out = json.loads(child.match.group(1).replace('\r\n', ''))
    learnedmacport = out['TABLE_mac_address']['ROW_mac_address']["disp_port"]
    print "%d %s (%s) %s" % (num, next_switch_ip, hostname, learnedmacport)

    child.sendline("show mac address-table interface %s | count" % learnedmacport)
    child.expect(["(\d+)\r\n", "([Ii]nvalid.*)\r\n", pexpect.TIMEOUT])
    if res == 1:
        die("Error on %s while run 'show mac address-table interface %s | count': %s" % (options.next_switch_ip, learnedmacport, child.match.group(1)))
    if res == 2:
        die("Timeout on %s while expecting regexp '(\\d+)\\r\\n' from: 'show mac address-table interface %s | count'" % (options.next_switch_ip, learnedmacport))

    mac_count = int(child.match.group(1))
    child.expect(["#", pexpect.TIMEOUT])
    if res == 1:
        die("Line: %d. Timeout on %s while expecting prompt symbol '#'" % (lineno(), options.next_switch_ip))
    if mac_count <= 1:
        sys.exit(0)
    else:
        child.sendline("show cdp neighbors interface %s detail" % learnedmacport)
        res = child.expect(["\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s", "([Ii]nvalid.*)\r\n", pexpect.TIMEOUT])
        if res == 1:
            die("Error on %s while run 'show cdp neighbors interface %s detail': %s" % (options.next_switch_ip, learnedmacport, child.match.group(1)))
        if res == 2:
            die("Timeout on %s while expecting regexp '\s\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s' from: 'show cdp neighbors interface %s detail'" % (options.next_switch_ip, learnedmacport))
        next_switch_ip = child.match.group(1).strip()
