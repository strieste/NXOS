#!/isan/bin/python
import cli
import time
import argparse


VERBOSITY = None


def run(cmd):
        res = cli.cli("run guestshell bash -c 'sudo %s'" % cmd)
        if VERBOSITY:
            print res
        return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get TOP talkers via netflow')
    parser.add_argument('-t', action='store', type=int, dest='time', help='How long collect flows', default=30, metavar="30")
    parser.add_argument("-v", dest="verbosity", help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    VERBOSITY = args.verbosity
    try:
        run("yum install epel-release -y")
        run("yum install gcc gcc-c++ psmisc libtool automake autoconf python-devel libpcap-devel flow-tools -y")
        run("mkdir /tmp/flow-tools")
        run("flow-capture 0/0/6999 -w /tmp/flow-tools/")
        run("wget https://softflowd.googlecode.com/files/softflowd-0.9.9.tar.gz ; tar -xzvf softflowd-0.9.9.tar.gz ; cd softflowd-0.9.9; ./configure ; make ; sudo ./softflowd -i any -n localhost:6999")
        time.sleep(args.time)
        run("softflowd-0.9.9/softflowctl expire-all")
        time.sleep(3)
        run("killall softflowd flow-capture")

        result = run("flow-cat -p /tmp/flow-tools | flow-stat -f10  -S4")
        if not VERBOSITY:
            print result
    finally:
        run("yum remove epel-release -y")
        run("yum remove gcc gcc-c++ psmisc libtool automake autoconf python-devel libpcap-devel flow-tools -y")
        run("rm -rf softflowd-0.9.9*")
        run("rm -rf /tmp/flow-tools")