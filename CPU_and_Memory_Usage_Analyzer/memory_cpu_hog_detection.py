import cli
import json
import os
import argparse
import subprocess
import time
import re
import datetime
from difflib import Differ


def is_dir(dirname):
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check the nexus for overall health')
    parser.add_argument('--cpu_hogs_limit', action='store', type=int, help='How many CPU hogs save to log', default=5)
    parser.add_argument('--mem_hogs_limit', action='store', type=int, help='How many memory hogs save to log', default=5)
    parser.add_argument('--cpu_threshold', action='store', type=int, help='CPU hog\'s threshold, %', default=50)
    parser.add_argument('--mem_threshold', action='store', type=int, help='Memory hog\'s threshold, %', default=70)
    parser.add_argument("--logdir", help="Where logs store", action="store", required=True, type=is_dir)
    parser.add_argument("--threshold_script", help="Where threshold_monitor_nexus.py script located", action="store", default = "./threshold_monitor_nexus.py", required=True)
    parser.add_argument("--threshold_script_conf", help="Where config located", default = "./config.txt", action="store" )
    args = parser.parse_args()

    sys_res = json.loads(cli.clid("show system resources"))
    user_cpu = sys_res["cpu_state_user"]
    kernel_cpu = sys_res["cpu_state_kernel"]
    cpu_load = float(user_cpu) + float(kernel_cpu)

    cpu_hogs = []
    if cpu_load > args.cpu_threshold:
        proc_cpu = json.loads(cli.clid("show processes cpu sort"))
        rows = proc_cpu["TABLE_process_cpu"]["ROW_process_cpu"]
        i = 0
        while i < len(rows):
            cpu_hogs.append( rows[i]["process"] )
            i += 1
            if i > args.cpu_hogs_limit:
                break

    used_mem = int(sys_res["memory_usage_used"])
    total_mem = int(sys_res["memory_usage_total"])
    mem_hogs = []
    if (used_mem * 100 / float(total_mem)) > args.mem_threshold:
        proc_mem = json.loads(cli.clid("show processes memory"))
        rows = proc_mem["TABLE_process_memory"]["ROW_process_memory"]
        i = 0
        while i < len(rows):
            mem_hogs.append( rows[i]["process"] )
            i += 1
            if i > args.mem_hogs_limit:
                break


    lldp_detail = json.loads(cli.clid("show lldp ne detail"))
    rows = lldp_detail["TABLE_nbor_detail"]["ROW_nbor_detail"]
    lldp_ifaces = []
    if isinstance(rows, dict):
        lldp_ifaces.append( rows["l_port_id"] )
    else:
        for r in rows:
            lldp_ifaces.append( r["l_port_id"] )

    cdp_detail = json.loads(cli.clid("show cdp ne detail"))
    rows = cdp_detail["TABLE_cdp_neighbor_detail_info"]["ROW_cdp_neighbor_detail_info"]
    cdp_ifaces = []
    if isinstance(rows, dict):
        cdp_ifaces.append( rows["intf_id"] )
    else:
        for r in rows:
            cdp_ifaces.append( r["intf_id"] )

    data = {"CPUCHECK" : [], "MEMCHECK" : [], "NEIGHBORCHECK" : [{}], "THRESHOLDCHECK" : []}

    new_logfile = "SystemCheck%s.check" % time.strftime("%d-%m-%H")
    log_pattern = re.compile("SystemCheck(\d{1,2}-\d{1,2}-\d{1,2})\.check")
    logfiles = [f for f in os.listdir(args.logdir) if os.path.isfile(os.path.join(args.logdir, f)) and log_pattern.match(f)]
    logfiles = sorted(logfiles)
    if logfiles:
        last_logfile = logfiles[-1]
        with open(os.path.join(args.logdir, last_logfile)) as file:
            content = json.load(file)
            if len(content["CPUCHECK"]) < 60:
                new_logfile = last_logfile

    new_logfile = os.path.join(args.logdir, new_logfile)
    if os.path.isfile(new_logfile):
        with open(new_logfile) as file:
            data = json.load(file)

    data["CPUCHECK"].append({"hogs" : cpu_hogs,
                             "usage" : {
                                            "processes_total" : sys_res["processes_total"],
                                            "processes_running" : sys_res["processes_running"],
                                            "cpu_state_user" : sys_res["cpu_state_user"],
                                            "cpu_state_kernel" : sys_res["cpu_state_kernel"],
                                            "cpu_state_idle" : sys_res["cpu_state_idle"]
                                        }
                            })
    data["MEMCHECK"].append({
                                "hogs" : mem_hogs
                            })

    prev_cdp_ifaces = data["NEIGHBORCHECK"][-1].get("cdp", [])
    prev_lldp_iface = data["NEIGHBORCHECK"][-1].get("lldp", [])
    cdp_ifaces = sorted(cdp_ifaces)
    lldp_ifaces = sorted(lldp_ifaces)

    nei_dict = {
                    "cdp" : cdp_ifaces,
                    "lldp": lldp_ifaces
    }

    if prev_cdp_ifaces and prev_cdp_ifaces != cdp_ifaces:
        nei_dict["cdp_diff"] = {"prev" : prev_cdp_ifaces, "new" : cdp_ifaces}

    if prev_lldp_iface and prev_lldp_iface != lldp_ifaces:
        nei_dict["lldp_diff"] = {"prev" : prev_lldp_iface, "new" : lldp_ifaces}

    data["NEIGHBORCHECK"].append(nei_dict)

    thresholds = json.loads( subprocess.Popen(["python", args.threshold_script, "-c", args.threshold_script_conf], stdout = subprocess.PIPE).communicate()[0] )
    prev_thresholds = None
    if len(data["THRESHOLDCHECK"]) > 0:
        prev_thresholds = data["THRESHOLDCHECK"][-1]

    data["THRESHOLDCHECK"].append( thresholds )
    if prev_thresholds:
        thresh_dif = {}
        if prev_thresholds:
            for prev_thresh_item in prev_thresholds:
                for thresh_item in thresholds:
                    if thresh_item["name"] == prev_thresh_item["name"]:
                        iface_name = thresh_item["name"]
                        for key in prev_thresh_item:
                            if key in thresh_item and key != "name":
                                cur_thresh = thresh_item[key]
                                prev_thresh = prev_thresh_item[key]
                                need_update = False
                                if (float(prev_thresh) <= 0):
                                    if float(prev_thresh) != float(cur_thresh):
                                        need_update = True
                                else:
                                    need_update = abs( float(cur_thresh) - float(prev_thresh) ) * 100 / float(prev_thresh) > 25
                                if need_update:
                                    thresh_dif.setdefault(iface_name, {})
                                    thresh_dif[iface_name][key] = {"prev" : float(prev_thresh), "new" : float(cur_thresh)}
                        break
        if thresh_dif:
            data["THRESHOLDDIFF"] = thresh_dif

    logs = cli.cli("show logging").split('\n')
    logs_variables = {}
    for line in logs:
        if line.find("TRACEBACK") != -1:
            logs_variables.setdefault("TRACEBACK", []).append(line)
        elif line.find("authentication failed") != -1:
            logs_variables.setdefault("AUTHFAIL", []).append(line)
        elif line.find("neighbor down") != -1:
            logs_variables.setdefault("NEIDOWN", []).append(line)

    if logs_variables:
        data["LOGS"] = logs_variables

    with open(new_logfile, 'w+') as outfile:
        json.dump(data, outfile)

