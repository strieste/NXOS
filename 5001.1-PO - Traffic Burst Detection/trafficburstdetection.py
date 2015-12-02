import re
import sys
import argparse
import time
import pexpect


class TresholdReached(Exception):
    def __init__(self, device, port, parameter, value, treshold):
        self.msg = "Device: %s Port: %s Parameter: '%s' has value: %s greater or equal to treshold: %s" % (
            device, port, parameter, value, treshold)

    def __str__(self):
        return self.msg


class ParamNotFound(Exception):
    def __init__(self, device, port, parameter):
        self.msg = "Device: %s Port: %s Parameter: '%s' not found, skip" % (
            device, port, parameter)

    def __str__(self):
        return self.msg


def connect(switch, username, password):
    child = pexpect.spawn('telnet %s' % switch, maxread=30000)
    child.expect('[Uu]sername:\s|[Ll]ogin:\s')
    child.sendline(username)
    child.expect('[Pp]assword: ')
    child.sendline(password)
    child.expect("#")
    child.sendline('terminal length 0')
    child.expect("#")
    prompt = child.before
    prompt = prompt.replace('terminal length 0', '').strip()
    return (prompt, child)


def main(args):
    assert isinstance(args, argparse.Namespace)
    with open(args.config, 'r') as content_file:
        content = content_file.readlines()

    params = {}
    for line in content:
        (param, threshold) = line.split(":")
        params[param] = threshold

    (prompt, child) = connect(args.switch, args.username, args.password)

    while True:
        child.sendline('show interfaces')
        res = child.expect([prompt + "#", "% Invalid", pexpect.EOF])
        data = child.before
        if res == 2:
            (prompt, child) = connect(args.switch, args.username, args.password)
            continue
        if res == 1:
            child.expect(prompt + "#")
            child.sendline('show interface')
            res = child.expect([prompt + "#", "% Invalid"])
            data = child.before
            if res == 1:
                raise Exception("invalid command")
        interfaces = re.split('(\S*[Ee]thernet\S+)\s+is', data)
        # interfaces == ['', 'GigabitEthernet9/5', 'data for GigabitEthernet9/5', 'FastEthernet1/1', 'data for FastEthernet1/1']
        interfaces.pop(0)

        for iface, info in zip(interfaces[0::2], interfaces[1::2]):
            for p in params:
                try:
                    threshold = params[p]
                    if p == "input rate" or p == "output rate":
                        # input rate 1000 bits/sec, 2 packets/sec
                        res = re.search('input\s+rate\s+\d+\s+bits\/sec\,\s+(\d+)\s+packets\/sec', info)
                        if not res:
                            raise ParamNotFound(args.switch, iface, p)
                        value = res.group(1)
                        if long(value) >= long(threshold):
                            raise TresholdReached(args.switch, iface, p, value, threshold)
                    elif p == "txload" or p == "rxload":
                        # txload 1/255, rxload 1/255
                        res = re.search(p + '\s+(\d+)\/(\d+)', info)
                        if not res:
                            raise ParamNotFound(args.switch, iface, p)
                        value = res.group(1)
                        threshold = params[p].split("/")[0]
                        if long(value) >= long(threshold):
                            raise TresholdReached(args.switch, iface, p, value, threshold)
                    elif p == "packets input" or p == "packets output" or p == "input packets" or p == "output packets":
                        # 300114 packets input
                        res = re.search('(\d+)\s+' + p, info)
                        if not res:
                            reverse_variant = p.split()
                            reverse_variant = reverse_variant[1] + " " + reverse_variant[0]
                            res = re.search('(\d+)\s+' + reverse_variant, info)
                            if not res:
                                raise ParamNotFound(args.switch, iface, p)
                        value = res.group(1)
                        if long(value) >= long(threshold):
                            raise TresholdReached(args.switch, iface, p, value, threshold)
                    else:
                        print "Unknown parameter: " + str(p)
                except (TresholdReached, ParamNotFound) as e:
                    print e
        time.sleep(args.interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run show interfaces and check tresholds in output')
    parser.add_argument('-u', action='store', dest='username', help='username for connection to switch', required=True,
                        metavar="username")
    parser.add_argument('-p', action='store', dest='password', help='password for username', required=True,
                        metavar="password")
    parser.add_argument('-c', action='store', dest='config', help='Path to config with tresholds', required=True,
                        metavar="config")
    parser.add_argument('-s', action='store', dest='switch', help='Switch IP-address or hostname', required=True,
                        metavar="ip")
    parser.add_argument('-t', action='store', type=int, dest='interval', help='Time between poll, sec', default=30,
                        metavar="30")
    args = parser.parse_args()
    main(args)
