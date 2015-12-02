import cli
import json
import argparse
import sys
import time
import re
import smtplib

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check icmp-echo from IP SLA')
    parser.add_argument("--email", help="Send alert to this email", action="store", required=True)
    parser.add_argument("--smtp_server", help="SMTP server for email", action="store", default="192.168.1.2")
    parser.add_argument('--threshold', action='store', type=int, help='Number of failed attempts before shutdown the interface', default=100)
    parser.add_argument("--verbosity", help="Increase output verbosity", action="store_true")
    parser.add_argument("--dest_ip", help="IP-adders to ping", action="store", required=True)
    args = parser.parse_args()

    res = json.loads( cli.clid("show ip sla configuration") )
    maxindex = 0
    for r in res["TABLE_oper"]:
        row = r["ROW_oper"]
        if "index" in row:
            indx = int(row["index"])
            if indx > maxindex:
                maxindex = indx
            # if row["oper-type"] == "icmp-echo" and row["dest-ip"] == args.dest_ip:
            #     print "ip sla operaion already exists"
            #     sys.exit(1)
    maxindex += 1
    cli.cli("configure terminal ; feature sla sender ; ip sla %d ; icmp-echo %s ; threshold 1 ; timeout 1 ; frequency 1 ; end" % (maxindex, args.dest_ip) )
    cli.cli("configure terminal ; ip sla schedule %d life forever start-time now" % maxindex )
    try:
        time.sleep(args.threshold)
        res = cli.cli("show ip sla statistics %s" % maxindex)
        pattern = re.search("number\s+of\s+failures\s*:\s*(\d+)", res, re.IGNORECASE | re.M)
        if not pattern:
                raise ValueError("can't find 'number of failures' from %s" % res);
        num_fail = int(pattern.group(1))
        if num_fail >=  args.threshold:
            print "threshold is reached"
            iface_info = json.loads( cli.clid("show routing ip %s" % args.dest_ip) )
            iface_name = iface_info.get("TABLE_vrf",{}).get("ROW_vrf",{}).get("TABLE_addrf",{}).get("ROW_addrf", {}).get("TABLE_prefix",{}).get("ROW_prefix",{}).get("TABLE_path",{}).get("ROW_path",[{}])[0].get("ifname")
            if not iface_name:
                raise ValueError("can't find route for ip %s" % args.dest_ip)
            cli.cli("configure terminal ; interface %s ; shutdown" % iface_name)

            sender = 'ipsla@ipsla.py'
            receivers = [args.email]
            report = "Threshold reached for ip: %s. The interface %s was down" % (args.dest_ip, iface_name)
            message = """From: %s
            To: %s
            Subject: Report ipsla.py
            %s
            """ % (sender, ' '.join(str(s) for s in receivers), json.dumps(report, indent=4, separators=(',', ': ')) )

            try:
                smtpObj = smtplib.SMTP(args.smtp_server)
                smtpObj.sendmail(sender, receivers, message)
                if args.verbosity:
                    print "Successfully sent email"
                    print message
            except smtplib.SMTPException:
                print "Error: unable to send email"
    finally:
        cli.cli("configure terminal ; no ip sla schedule %d" % maxindex )
        cli.cli("configure terminal ; no ip sla %d" % maxindex )
