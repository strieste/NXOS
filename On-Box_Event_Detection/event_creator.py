import cli
import json
import os
import argparse
import re
import datetime
import time
import sys
import smtplib
import collections

def is_dir(dirname):
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check the last log file and create events')
    parser.add_argument("--logdir", help="Where logs store", action="store", required=True, type=is_dir)
    parser.add_argument("--email", help="Send report to this email", action="store", required=True)
    parser.add_argument("--verbosity", help="Increase output verbosity", action="store_true")
    args = parser.parse_args()

    log_pattern = re.compile("SystemCheck(\d{1,2}-\d{1,2}-\d{1,2})\.check")
    logfiles = [f for f in os.listdir(args.logdir) if os.path.isfile(os.path.join(args.logdir, f)) and log_pattern.match(f)]
    maxdata = None
    lastfile = None
    for l in logfiles:
        match = log_pattern.search(l)
        if match:
            data = datetime.datetime.strptime( match.group(1), "%d-%m-%H" )
            if not maxdata:
                maxdata = data
                lastfile = l
            if data > maxdata:
                maxdata = data
                lastfile = l

    cpu_hogs = set()
    mem_hogs = set()
    cdp_diff = []
    lldp_diff = []
    thresh_diff = []
    logs = []

    with open(os.path.join(args.logdir, lastfile)) as file:
        data = json.load(file)
        if "CPUCHECK" in data and data["CPUCHECK"]:
            cpuchecks = data["CPUCHECK"][-12:]
            for item in cpuchecks:
                if "hogs" in item:
                    cpu_hogs.update( item["hogs"] )
        if "MEMCHECK" in data and data["MEMCHECK"]:
            memchecks = data["MEMCHECK"][-12:]
            for item in memchecks:
                if "hogs" in item:
                    mem_hogs.update( item["hogs"] )
        if "NEIGHBORCHECK" in data and data["NEIGHBORCHECK"]:
            neigh = data["NEIGHBORCHECK"][-12:]
            for item in neigh:
                if item.get("cdp_diff"):
                    cdp_diff.append( item["cdp_diff"] )
                if item.get("lldp_diff"):
                    lldp_diff.append( item["lldp_diff"] )
        if data.get("THRESHOLDDIFF"):
            thresh_diff.append( data["THRESHOLDDIFF"] )
        if data.get("LOGS"):
            logs.extend( data["LOGS"] )

    cpu_hogs = list(cpu_hogs)
    mem_hogs = list(mem_hogs)
    report = collections.OrderedDict()
    report["DATE"] = time.ctime()
    report["CPU_HOGS"] = cpu_hogs
    report["MEM_HOGS"] = mem_hogs
    report["CDP_DIFF"] = cdp_diff
    report["LLDP_DIFF"] = lldp_diff
    report["THRESH_DIFF"] = thresh_diff
    report["LOGS"] = logs

    if args.verbosity:
        json.dump(report, sys.stdout, indent=4, separators=(',', ': '))

    sender = 'report@report.repotr'
    receivers = [args.email]

    message = """From: %s
    To: %s
    Subject: Report
    %s
    """ % (sender, ' '.join(str(s) for s in receivers), json.dumps(report, indent=4, separators=(',', ': ')) )

    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, message)
        if args.verbosity:
            print "Successfully sent email"
            print message
    except smtplib.SMTPException:
        print "Error: unable to send email"
