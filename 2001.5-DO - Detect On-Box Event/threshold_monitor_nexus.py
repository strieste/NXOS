#!/isan/bin/python
import cli
import json
import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run show interfaces and check tresholds in output')
    parser.add_argument('-c', action='store', dest='config', help='Path to config with tresholds',
                        metavar="config", required=True)
    args = parser.parse_args()
    with open(args.config, 'r') as content_file:
        content = content_file.readlines()

    params = {}
    for line in content:
        (param, threshold) = line.split(":")
        params[param] = threshold

    interfaces = json.loads(cli.clid("show interface"))
    ifaces_data = []
    for iface in interfaces["TABLE_interface"]["ROW_interface"]:
        data = {}
        thresh_reached = False
        for p in params:
            threshold = params[p]
            if p == "input rate" or p == "output rate":
                key = "vdc_lvl_in_avg_bits" if p == "input rate" else "vdc_lvl_out_avg_bits"
                value = iface.get(key)
                if not value:
                    key = "eth_inrate1_bits" if p =="input rate" else "eth_outrate1_bits"
                    value = iface.get(key)
                if value:
                    if long(value) >= long(threshold):
                        thresh_reached = True
                        data[p] = value
            elif p == "txload" or p == "rxload":
                key = "eth_txload" if p == "txload" else "eth_rxload"
                value = iface.get(key)
                if value:
                    if long(value) >= long(threshold):
                        thresh_reached = True
                        data[p] = value
            elif p == "packets input" or p == "packets output" or p == "input packets" or p == "output packets":
                keys = ["vdc_lvl_in_pkts", "eth_inpkts"] if p.find("input") != -1 else ["vdc_lvl_out_pkts", "eth_outpkts"]
                value = iface.get(keys[0])
                if not value:
                    value = iface.get(keys[1])
                if value:
                    if long(value) >= long(threshold):
                        thresh_reached = True
                        data[p] = value
        if thresh_reached:
            data["name"] = iface["interface"]
            ifaces_data.append(data)

    json.dump(ifaces_data, sys.stdout)

