from jinja2 import Template
import argparse
import re


ID300 = """
{% if EXTENDED %}
{# STATIC PART #}
{# group #}
set groups filter-RT-BC-BE-in firewall family inet filter <*> accounting-profile fba-vpn-profile
set groups filter-RT-BC-BE-in firewall family inet filter <*> interface-specific
set groups filter-RT-BC-BE-in firewall family inet filter <*> term RT then count 56
set groups filter-RT-BC-BE-in firewall family inet filter <*> term RT then loss-priority high
set groups filter-RT-BC-BE-in firewall family inet filter <*> term RT then forwarding-class realtime
set groups filter-RT-BC-BE-in firewall family inet filter <*> term RT then accept
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BC then count 57
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BC then loss-priority high
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BC then forwarding-class critical-data
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BC then accept
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BE then count 55
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BE then loss-priority low
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BE then forwarding-class low-cost-data
set groups filter-RT-BC-BE-in firewall family inet filter <*> term BE then accept
{# fba-vpn-profile #}
set accounting-options filter-profile fba-vpn-profile file stat-fba
set accounting-options filter-profile fba-vpn-profile interval 5
set accounting-options filter-profile fba-vpn-profile counters 56
set accounting-options filter-profile fba-vpn-profile counters 57
set accounting-options filter-profile fba-vpn-profile counters 55
{# classifiers #}
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class realtime loss-priority high code-points 010
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class realtime loss-priority high code-points 101
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class critical-data loss-priority high code-points 001
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class low-cost-data loss-priority high code-points 000
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class low-cost-data loss-priority high code-points 011
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class low-cost-data loss-priority high code-points 100
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class low-cost-data loss-priority high code-points 110
set class-of-service classifiers inet-precedence vpn-ipp-in forwarding-class low-cost-data loss-priority high code-points 111
{# RED #}
set class-of-service drop-profiles 50-95-drop interpolate fill-level 0
set class-of-service drop-profiles 50-95-drop interpolate fill-level 50
set class-of-service drop-profiles 50-95-drop interpolate fill-level 95
set class-of-service drop-profiles 50-95-drop interpolate drop-probability 0
set class-of-service drop-profiles 50-95-drop interpolate drop-probability 10
set class-of-service drop-profiles 50-95-drop interpolate drop-probability 100
{% endif %}
{# DYNAMIC PART #}
{# Defining input firewall family inet filter #}
set firewall family inet filter profile-id300-{{BW_RATE}}-{{PROFILE_NAME}}-in apply-groups filter-RT-BC-BE-in
set firewall family inet filter profile-id300-{{BW_RATE}}-{{PROFILE_NAME}}-in term RT from precedence 5
set firewall family inet filter profile-id300-{{BW_RATE}}-{{PROFILE_NAME}}-in term RT from precedence 2
set firewall family inet filter profile-id300-{{BW_RATE}}-{{PROFILE_NAME}}-in term RT then policer lim{{RT_RATE}}-RT
set firewall family inet filter profile-id300-{{BW_RATE}}-{{PROFILE_NAME}}-in term BC from precedence 1
set firewall family inet filter profile-id300-{{BW_RATE}}-{{PROFILE_NAME}}-in term BC then policer lim{{BC_RATE}}-BC-remap-to-be
{# Defining input policer #}
set firewall policer lim{{BW_RATE}}-drop if-exceeding bandwidth-limit {{BW_RATE}}
set firewall policer lim{{BW_RATE}}-drop if-exceeding burst-size-limit {{BW_BSL}}
set firewall policer lim{{BW_RATE}}-drop then discard
{# Defining FF policer for RT traffic #}
set firewall policer lim{{RT_RATE}}-RT if-exceeding bandwidth-limit {{RT_RATE}}
set firewall policer lim{{RT_RATE}}-RT if-exceeding burst-size-limit {{RT_BSL}}
set firewall policer lim{{RT_RATE}}-RT then discard
{# Defining FF policer for BC traffic #}
set firewall policer lim{{BC_RATE}}-BC-remap-to-be if-exceeding bandwidth-limit {{BC_RATE}}
set firewall policer lim{{BC_RATE}}-BC-remap-to-be if-exceeding burst-size-limit {{BC_BSL}}
set firewall policer lim{{BC_RATE}}-BC-remap-to-be then loss-priority low
set firewall policer lim{{BC_RATE}}-BC-remap-to-be then forwarding-class low-cost-data
{# Applying scheduler-map and and shaping rate  #}
set class-of-service traffic-control-profiles profile-{{BW_RATE}}-{{PROFILE_NAME}} scheduler-map profile-{{PROFILE_NAME}}
set class-of-service traffic-control-profiles profile-{{BW_RATE}}-{{PROFILE_NAME}} shaping-rate {{BW_RATE}}
{# Defining scheduler-map #}
set class-of-service scheduler-maps profile-{{PROFILE_NAME}} forwarding-class realtime scheduler {{RT}}p-prio
set class-of-service scheduler-maps profile-{{PROFILE_NAME}} forwarding-class critical-data scheduler {{BC}}p-drop
set class-of-service scheduler-maps profile-{{PROFILE_NAME}} forwarding-class low-cost-data scheduler remainder-drop
{# Defining scheduler for RT traffic #}
set class-of-service schedulers {{RT}}p-prio transmit-rate percent {{RT}}
set class-of-service schedulers {{RT}}p-prio buffer-size temporal 50k
set class-of-service schedulers {{RT}}p-prio priority high
{# Defining scheduler for BC traffic #}
set class-of-service schedulers {{BC}}p-drop transmit-rate percent {{BC}}
set class-of-service schedulers {{BC}}p-drop buffer-size percent {{BC}}
set class-of-service schedulers {{BC}}p-drop drop-profile-map loss-priority high protocol any drop-profile 50-95-drop
{# scheduler - remainder #}
set class-of-service schedulers remainder-drop transmit-rate remainder
set class-of-service schedulers remainder-drop buffer-size remainder
set class-of-service schedulers remainder-drop priority low
set class-of-service schedulers remainder-drop drop-profile-map loss-priority any protocol any drop-profile 50-95-drop
{% if INTF %}
{# INTERFACE PART #}
set interfaces {{INTF}} family inet filter input profile-id300-{{BW_RATE}}-{{PROFILE_NAME}}-in
set interfaces {{INTF}} family inet policer input lim{{BW_RATE}}-drop
set class-of-service interfaces {{INTF}} output-traffic-control-profile profile-{{BW_RATE}}-{{PROFILE_NAME}}
set class-of-service interfaces {{INTF}} classifiers inet-precedence vpn-ipp-in
{% endif %}
"""

ID100="""

"""


def get_bps(rate):

    match = re.search('(\d+)', rate)
    if match:
        num = int(match.group(1))
    else:
        return False
    rate = rate.lower()
    if 'k' in rate:
        return num * 1000
    elif 'm' in rate:
        return num * 1000000
    elif 'g' in rate:
        return num * 1000000000

    return False


def bit_rounder(num):

    if num % 1000000000 == 0:
        return str(int(num / 1000000000)) + 'G'
    elif num % 1000000 == 0:
        return str(int(num / 1000000)) + 'm'
    elif num % 1000 == 0:
        return str(int(num / 1000)) + 'k'

    return num


def get_burst_size_limit(rate):
    result = get_bps(rate) / 1000 / 0.08
    if result < 15000:
        result = 15000

    return bit_rounder(int(result))


def get_profile_name(rt, bc, be):
	
	if rt and bc and be:
		return '{}RT-{}BC-{}BE'.format(rt, bc, be) 
	elif be == 0 and rt and bc:
		return '{}RT-{}BC'.format(rt, bc)
	elif bc == 0 and rt and be:
		return '{}RT-{}BE'.format(rt, be)
	elif rt == 0 and be and bc:
		return '{}BC-{}BE'.format(bc, be)
	elif be == 0 and bc == 0 and rt:
		return '{}RT'.format(rt)
	elif be == 0 and rt == 0 and bc:
		return '{}BC'.format(bc)
	elif be == 0 and bc == 0 and rt:
		return '{}BE'.format(be)

	return False


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
    	description='NOTE: Verify the result here before implementing: box.msk.ip.rostelecom.ru/cfgdb (limited access)',
    	epilog='Example: jcos_gen.py -v -i xe-4/0/0.1234 3500k 35 40 25')

    parser.add_argument(
        '-v', '--verbose', required=False, action='store_true', default=False,
        help='generate full CoS config')
    parser.add_argument(
        '-f', '--file', required=False, action='store_true', default=False,
        help='output to file (.txt) - will be created automatically (default output to console)')
    parser.add_argument(
        '-t', type=str, required=False, default='id300', dest='template', action='store',
        help='H-QoS template id (default: \'id300\'; only \'id300\' is currently supported)') 
    parser.add_argument(
        '-i', type=str, required=False, dest='interface', action='store',
        help='applying config to specified interface; Junipers\'s format required, for ex. \'xe-4/0/0.1234\'' )
    
    parser.add_argument(
        'BW', type=str, action='store',
        help='total rate; legal prefixes are: k, m, G, for ex.: 3500k')
    parser.add_argument(
        'RT', type=int, action='store',
        help='bandwidth reservation for \'real-time\' traffic (percentage)')
    parser.add_argument(
        'BC', type=int, action='store',
        help='bandwidth reservation for \'business-critical\' traffic (percentage)')
    parser.add_argument(
        'BE', type=int, action='store',
        help='bandwidth reservation for \'best-efford\' traffic (percentage)')
     
    args = parser.parse_args()

    if args.RT + args.BC + args.BE is not 100: 
    	print('Ololo! The sum of RT, BC, BE integers should be 100. Try again, dude.')
    	quit()

    params = dict()
    params['PROFILE_NAME'] = get_profile_name(args.RT, args.BC, args.BE)
    params['RT'] = args.RT
    params['BC'] = args.BC
    params['BE'] = args.BE
    params['BW_RATE'] = args.BW
    params['RT_RATE'] = bit_rounder((get_bps(params['BW_RATE']) * params['RT'])/100)
    params['BC_RATE'] = bit_rounder((get_bps(params['BW_RATE']) * params['BC'])/100)
    params['BW_BSL'] = get_burst_size_limit(params['BW_RATE'])
    params['RT_BSL'] = get_burst_size_limit(params['RT_RATE'])
    params['BC_BSL'] = get_burst_size_limit(params['BC_RATE'])
    if args.interface: 
    	params['INTF'] = args.interface.replace('.', ' unit ')
    if args.verbose:
    	params['EXTENDED'] = True

    # with open('id300_template', 'r') as f:
    #     t = Template(f.read())

    if args.template == 'id300':
        result_string = Template(ID300).render(params)
    elif args.template == 'id100':
        # Pochta
        print('Not ready yet')
        quit()
    else:
        print('Unknown profile id. Visit box.msk.ip.rostelecom.ru/cfgdb for more information.')
        quit()
    
    if args.file:
        with open('{}-{}-{}[{}].txt'.format(args.template, args.BW, params['PROFILE_NAME'],\
         'FULL' if args.verbose else 'SHORT'), 'w+') as out:
            out.write(result_string)
    else:
        print(result_string)
