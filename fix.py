import pexpect
import sys

host = sys.argv[1].strip()

payload = ['login',
           'password',
           'sys',
           'undo dhcp snooping enable ipv6',
           'return',
           'save',
           'y']

expects = ['Password:',
           '[Y/N]',
           host,
           pexpect.TIMEOUT]

fout = open('/var/noc/scripts/bsw/python_scripts/fix/logs_undo_dhcpv6/' + host, 'w+')
child = pexpect.spawn('telnet ' + host)
child.logfile = fout

child.expect_exact('Username:')


for cmd in payload:
    child.sendline(cmd)
    child.expect_exact(expects, timeout=5)

child.close()
fout.close()
