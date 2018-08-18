#!/usr/bin/python
# -*- coding: utf-8 -*-
from multiprocessing.dummy import Pool
import telnetlib, sys, time, MySQLdb, re

start = time.time()

lo = 'login'
pa = 'password'


# FILL IT (ONLY INSTRUCTIONS HERE - NO CONDITIONS AND AGRUMENTS):
regex = re.compile(r'\s(\d{4})')

payload = [
'config terminal',
'mac-access-list 108 permit any 5ce3.0e00.0000 src-mask ffff.ff00.0000 any',
'policy-map mac-vlan',
'no class-map STB',
'exit',
'class-map STB',
'match mac-access-list 108',
'exit',
'policy-map mac-vlan',
'class-map STB',
'exit',
'exit',
'exit',
'write',
'config terminal',
'schedule-list 0 start date-time 05-20-2017 02:40:00', # ПРОВЕРИТЬ!
'exit',
'reboot now schedule-list 0'
]

err = ['Unknown', 'unsuccessfully']

timeout = 5

# CHOOSE THE SOURCE LIST - COMMENT UNNECESSARY BLOCK:

# A. LIST GENERATOR FROM DATA BASE:
#db = MySQLdb.connect( 'server', 'login', 'password', 'database' );
#cursor = db.cursor( )
#sql = 'SELECT name FROM device_list WHERE key_model="118" AND name LIKE "bsw1450109"'
#cursor.execute( sql )
#bsw_list = [ x[0] for x in cursor.fetchall() ]
#db.close()

# B. LIST GENERATOR FROM FILE:
with open('list.txt', 'r') as f:
	bsw_list = [ x.strip().lower() for x in f.read().split('\n') if x and 'sw' in x ]



ok = open( 'OK.txt', 'w+' )
not_ok = open( 'NOT_OK.txt', 'w+' )

def kung_fu( bsw ):
	try:
		log = open( bsw + '.log', 'w+' )
		response = 0
		try:
			# CONNECTION TO HOST (CHECK IT!):
			tn = telnetlib.Telnet( bsw, 23, timeout )
			expect = tn.expect( [ 'Username:', 'login:', 'Login:' ], timeout )
			log.write( expect[2] )
			if expect[0] == -1:
				raise Exception( 'Unknown_vendor' )
			else:
				tn.write( lo + '\n' )
			expect = tn.expect( [ 'Password:' ], timeout )
			log.write( expect[2] )
			if expect[0] == -1:
				raise Exception( 'Unknown_vendor' )
			else:
				tn.write( pa + '\n' )
			expect = tn.expect( ['#'], timeout )
			log.write( expect[2] )
			if expect[0] == -1:
				raise Exception( 'Bad_TACACS_settings' )
			
			#узнаем vlan
			tn.write ( 'show run | include "set vlan"\n')
			data = tn.read_until( '#', timeout )
			log.write( data )
			
		
			stb_vlan = str(max(list(map(int, regex.findall(data)))))
			print stb_vlan
			log.write( '\nThe STB VLAN was found! It is ' + stb_vlan + '\n')

			
			# PAYLOAD (NO CONDITIONS AND AGRUMENTS):
			for index in xrange(len(payload)):
				if index == 2:
					for x in xrange(1,25):
						tn.write ( 'no service-policy mac-vlan ingress ' + str(x) + '\n' )
						log.write( tn.read_until( '#', timeout ))

				elif index == 12:
					for x in xrange(1,25):
						tn.write ( 'service-policy mac-vlan ingress ' + str(x) + '\n' )
						log.write( tn.read_until( '#', timeout ))

				elif index == 10:
					tn.write ( 'set vlan ' + stb_vlan + '\n' )
					data = tn.read_until( '#', timeout )
					log.write( data )
					# device syntax check
					if any (i in data for i in err):
						raise Exception('Expected_CLI_SyntaxError_catched')
				
				tn.write ( payload[index] + '\n' )
				data = tn.read_all()
				log.write( data )
				# device syntax check
				if any (i in data for i in err):
					raise Exception('Expected_CLI_SyntaxError_catched')


		except:
			print( 'Ooops!!:' + bsw, sys.exc_info() )
			not_ok.write( bsw + '\n' )
		else:
			response = 1
			ok.write( bsw + '\n' )
		finally:
			tn.close()
	finally:
		log.close()
		return response
# MAGIC PART:
pool = Pool( 75 )
total = pool.map( kung_fu, bsw_list )
pool.close()
pool.join()

ok.close()
not_ok.close()

#SUMMARY:
print( 'Done!')
print( 'Success: ' + str( total.count( 1 ) ) )
print( 'Failure: ' + str( total.count( 0 ) ) )
print( 'Total: ' + str( len( total ) ) )
print( 'Time(sec): ' + str( round( time.time() - start ) ) )


