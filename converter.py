#!/usr/bin/python
import sys
import re
import yaml
# ls -1 ./old/ | xargs -l1 -P1 ./converter.py 
# eth_pat = re.compile(r'interface Ethernet1\/0\/(?P<Eth>\d+)\D+(?P<vlan_t>.+)\stagged\D+(?P<vlan_u>.+)\suntagged\D+1\D+(?P<vlan_p>.+)')
eth_pat = re.compile(r'interface Ethernet1\/0\/(?P<Eth>\d+)\D+(?:(?P<vlan_t>.+)\stagged)?\D+(?:(?P<vlan_u>.+)\suntagged)?\D+\D1?\n\D+(?:(?P<vlan_p>\d{3,}))?')
vlan_batch_pat = re.compile(r'vlan\s(?P<start>\d+)\sto\s(?P<end>\d+)')
sys_loc_pat = re.compile(r'location\s(?P<sysloc>.+)')
ip_pat = re.compile(r'address\s(?P<ip>10\.43\.\d+\.\d+)')
gateway_pat = re.compile(r'0.0.0.0\s(?P<gate>10\.43\.\d+\.\d+)')

# !!!!!!
path = '///////'

if len(sys.argv) == 2:
    bsw = sys.argv[1]
else:
    sys.exit(1)

with open(path + 'hostnames.yaml', 'r') as y:
    hostnames = yaml.load(y)

with open(path + 'old/' + bsw, 'r') as old:
    old_cfg = old.read()

with open(path + 'template.cfg', 'r') as tmp:
    tmp_cfg = tmp.readlines()

eth_list = [m.groupdict() for m in re.finditer(eth_pat, old_cfg) if m]


def get_vlan_batch(block):
    match = re.search(vlan_batch_pat, block)
    if match:
        return match.group('start') + '-' + match.group('end')


def get_sysloc(block):
    match = re.search(sys_loc_pat, block)
    if match:
        return match.group('sysloc')
    else:
        return 'no sysloc!'


def get_ip(block):
    match = re.search(ip_pat, block)
    if match:
        return match.group('ip')


def get_gateway(block):
    match = re.search(gateway_pat, block)
    if match:
        return match.group('gate')


def get_vlan_p(block):
    result = ''
    i = int(re.search('\d+', line).group()) - 1

    vlan_u = eth_list[i].get('vlan_u')
    if vlan_u and ' ' in vlan_u:
        vlan_u = vlan_u.replace(' ', ';')
    vlan_t = eth_list[i].get('vlan_t')
    if vlan_t and ' ' in vlan_t:
        vlan_t = vlan_t.replace(' ', ';')
    vlan_p = eth_list[i].get('vlan_p')

    if vlan_u and vlan_t and vlan_p:
        result += 'switchport hybrid allowed vlan ' + vlan_t + ' tag\n'
        result += ' switchport hybrid allowed vlan ' + vlan_u + ' untag\n'
        result += ' switchport hybrid native vlan ' + vlan_p
    elif vlan_u and vlan_p:
        result += 'switchport hybrid allowed vlan ' + vlan_u + ' untag\n'
        result += ' switchport hybrid native vlan ' + vlan_p
    elif vlan_t:
        result += ' switchport hybrid allowed vlan ' + vlan_t + ' tag\n'
    elif vlan_p:
        result += 'switchport hybrid allowed vlan ' + vlan_p + ' untag\n'
        result += ' switchport hybrid native vlan ' + vlan_p
    return result


bsw = hostnames.get(bsw[:-4], bsw[:-4]) + '.cfg'
new_cfg = open(path + 'new/' + bsw, 'w+')
for line in tmp_cfg:
    if '$HOSTNAME' in line:
        line = line.replace('$HOSTNAME', bsw)
    elif '$VLAN_BATCH' in line:
        line = line.replace('$VLAN_BATCH', get_vlan_batch(old_cfg))
    elif '$SYSLOC' in line:
        line = line.replace('$SYSLOC', get_sysloc(old_cfg))
    elif '$IP_ADDR' in line:
        line = line.replace('$IP_ADDR', get_ip(old_cfg))
    elif '$GATEWAY' in line:
        line = line.replace('$GATEWAY', get_gateway(old_cfg))
    elif '$VLAN_P' in line:
        line = re.sub(r'\$VLAN_P\d+', get_vlan_p(line), line)
    new_cfg.write(line)

new_cfg.close()

# $HOSTNAME
# $VLAN_BATCH (x2)
# $SYSLOC
# $VLAN_T1 - 24
# $VLAN_U1 - 24
# $VLAN_P1 - 24
# $IP_ADDR
# $GATEWAY (x2)
