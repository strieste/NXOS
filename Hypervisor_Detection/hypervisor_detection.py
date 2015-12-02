import re
import json
import cisco
import argparse
import cli

global pars

pars = argparse.ArgumentParser(description="Hypervisor detection", epilog="Thank you for using!", prog="Hypervisor detector")
pars.add_argument('-a', '--all' ,  action="store_true", help="show full script output information")
pars.add_argument('-c', '--cdp',  action="store_true", help="show only CDP detected hypervisors" )
pars.add_argument('-l', '--lldp', action="store_true",  help="show only LLDP detected hypervisors")
pars.add_argument('-i', '--info', action="store_true", help=" show information about current device")
pars.add_argument('-p', '--port', action="store_true", help="show ports in 'UP' state with connected links")
pars.add_argument('-v', '--version', action='version', version='%(prog)s 0.2')

arg = vars(pars.parse_args())


class color():

    u""" This class we will use for colored output """

    CYAN = '\033[36m'
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDCOLOR = '\033[0m'

def deviceinfo():

	u"""Getting information about current device"""

	info=json.loads(cli.clid('show version'))
	print (color.CYAN + '\nSwitch information:\n' + color.ENDCOLOR)
	try:
		if 'kickstart_ver_str' in info.keys() and 'host_name' in info.keys() and 'kern_uptm_mins' in info.keys():
			print ('NXOS version: '.upper() + info.get('kickstart_ver_str') )
			print ('Device name: '.upper() + info.get('host_name') + '\n\t')
		else: 
			print ('General device info: ')
			for k in info.keys():
				print "%30s = %s" % (k, out[k])			
	except AttributeError:
			print ('No such attribute...')
		


def protocol_check():

	u"""Checking  running protocols"""

	cmd_lldp = "show feature | egrep lldp"
	proto_lldp = re.findall(r'enabled', cli.cli(cmd_lldp))
	cmd_cdp = "show cdp global | sed -n 2p"
	proto_cdp = re.findall(r'enabled', cli.cli(cmd_cdp))
	proto = {"cdp":str(proto_cdp), "lldp":str(proto_lldp)}
	counter = 2	
	print ('\nChecking CDP/LLDP protocols...')

	for key, value in proto.items():
		try:
			if re.search(r'enabled', value):
				print (key.upper() + ' protocol is' + color.GREEN +' enabled' + color.ENDCOLOR)
				if key == 'cdp':
					counter = counter + 1
				elif key == 'lldp':
					counter = counter - 1
			else:
				counter = 0
				print (key.upper() + ' protocol is' + color.RED + ' disabled' + color.ENDCOLOR)
		except AttributeError:
			print ('Check device. Need to be Nexus 7000/9000.')

	return counter

		 
def connports():

	u"""Gathering information about connected ports"""

	cmd = 'show interface brief'
	out = json.loads(cli.clid(cmd))
	i=0
	connectedports = []

	while i < len(out['TABLE_interface']['ROW_interface']):
		interf=out['TABLE_interface']['ROW_interface'][i]
		i=i+1
		if interf['state'] == 'up':
			connectedports.append(interf['interface'])

	return connectedports

def cdpneigh():

	u"""Getting CDP neighbours information """

	cmd = 'show cdp neighbor'
	cdp_dict = {}
	cdp = json.loads(cli.clid(cmd))['TABLE_cdp_neighbor_brief_info']['ROW_cdp_neighbor_brief_info']
	patern = re.compile('xen|kvm|esx|ubuntu|vmware', re.IGNORECASE)

	for row in cdp:
		if (re.search(patern, str(row)) != None):
			int_id = row['intf_id']
			if int_id not in cdp_dict:
				cdp_dict[int_id] = {}
			cdp_dict[int_id]['intf_id'] = int_id
			cdp_dict[int_id]['platform_id'] = row['platform_id']
			cdp_dict[int_id]['port_id'] = row['port_id']
			try:
				for key, value in cdp_dict.items():
					if 'port_id' in value and 'device_id' in value and 'intf_id' in value:
						continue
			except AttributeError:
				print ('There are not such attributes')
			finally:
				for key, value in cdp_dict.items():
					neighbour = cli.cli('show cdp neighbors interface ' + value['intf_id'] + ' detail')
					ip = re.findall(r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})', neighbour)[0]
					ipadd = str(ip)
					print ('{0:15} \t\t {1:10}  {2:25}  {3:10}  {4:15}'.format (value['platform_id'].ljust(15), value['port_id'].ljust(29) , str(ip).ljust(34), 'CDP'.ljust(27), value['intf_id']))
	

def lldpneigh():

	u"""Getting LLDP neighbours information"""

	cmd  = 'show lldp neighbors detail'

	infolist = ['System Description', 'Port Description', 'Management Address:', 'Local Port', 'System Name']
	g = lambda x,y: cli.cli (cmd + ' | egrep \\"' + x + '\\"' + ' | awk \\"{print $' + str(y) + '}\\"' )
	
	tuple1 = []
	for idx, val in enumerate (infolist):

		if idx == 0:
			list1 = (cli.cli (cmd + ' | egrep \\"' + val + '\\"' + ' | sed \\"s/' + val + '//g\\"')).split('\n')
			tuple1.append(list1)
		elif idx == 1:
			list2 = g(val,3).split('\n')
			tuple1.append(list2)
		elif idx ==2 :
			list3 = g(val,3).split('\n')
			tuple1.append(list3)
		elif idx == 3:
			list4 = g(val,4).split('\n')
			tuple1.append(list4)
		elif idx == 4:
			list5 = g(val,3).split('\n')
			tuple1.append(list5)
	
	patern = re.compile('xen|kvm|esx|ubuntu|vmware', re.IGNORECASE)
	i = 0

	while i < (len(list1) - 1):

		if (re.search(patern, list1[i]) != None):

			hyperv_patern =  list1[i].split(': ')[0] + list1[i].split(': ')[1].split(' ')[0]
			hyperv = re.sub(u'[^A-Za-z\s]*', u'', hyperv_patern)
			portid = list2[i]
			ipaddr = list3[i]
			interf = list4[i]
			print ('{0:15} \t\t {1:10}  {2:25}  {3:10}  {4:15}'.format (hyperv.ljust(15), portid.ljust(29) , ipaddr.ljust(34), 'LLDP'.ljust(27), interf))
		
		i=i+1
	


if __name__ == "__main__" :

	u"""Main function"""

	
	if arg['info']: 
		deviceinfo()

	if arg['cdp'] or arg['lldp'] or arg['all']:
		if arg['all']:
			deviceinfo()
		protocheck = protocol_check()
		print ('\n')
		print ('Hypervisor' +'\t\t\t' + 'Connected Port' + '\t\t\t' + 'IP address' + '\t\t\t' + 'Neighbor Type' + '\t\t\t' + 'Local Port')
		print ('--------------------------------------------------------------------------------------------------------------------------------------------------')
		if (protocheck == 3) or (arg['cdp']):
			cdpneigh()
		elif (protocheck == 1) or (arg['lldp']):
			lldpneigh()
		elif protocheck == 2:
			cdpneigh()
			lldpneigh()
		elif protocheck == 0:
			print ('\nNo CDP/LLDP protocol running on this switch!')
	
	if arg['port']:
		print ('\nPorts on "UP" state on this switch:\n')
		for port in connports():
			print (color.BLUE + port + color.ENDCOLOR)
		print ('\n')

	


