'''
	Extremely rough proof-of-concept for interfacing with the iRAD 900 via Bluetooth
	Brandon Asuncion <me@brandonasuncion.tech>

	DEPENDENCIES
	- If on a Raspberry Pi:
		$ sudo apt-get install pi-bluetooth
	- For everyone:
		$ sudo apt-get install bluetooth bluez python-bluez
'''

import time
from bluetooth import *
import sys
import pickle

addr = "B8:92:1D:00:3F:61"
uuid = "00000000-deca-fade-deca-deafdecacaff"

with open('packetData.dat', 'rb') as fh:
	packets = pickle.load(fh)
	
service_matches = find_service( uuid = uuid, address = addr )

if len(service_matches) == 0:
    print("couldn't find the service")
    sys.exit(0)

first_match = service_matches[0]
port = first_match["port"]
name = first_match["name"]
host = first_match["host"]

print("Connecting to \"{}\" on {} port {}".format(name, host, port))

try:
	sock=BluetoothSocket( RFCOMM )
	sock.connect((host, port))
except bluetooth.btcommon.BluetoothError:
	print("Unable to connect")
	exit

# receive data until the packet size matches the header
def rx():
	data = None
	try:
		while data == None:
			data = sock.recv(1024)
		while len(data) < 3:
			data = data + sock.recv(1024)
		while len(data) < ord(data[1]) + 3:
			data = data + sock.recv(1024)
	except IOError:
		print("IOError rx()")
	return data
	
def tx(data):
	sock.send(data)
	#print("\tSending:\t{}".format(" ".join([hex(ord(i)) for i in data])))

def sendResponse(data):
	global packets
	
	found = False
	for i, packet in enumerate(packets):			
		if (not packet['direction']) and (data == packet['raw']):
			
			j = i + 1
			
			while packets[j]['direction']:
				tx(packets[j]['raw'])
				j = j + 1
				if j >= len(packets):
					break
			return True
	return False

def replaceChar(data, index, char):
	return data[:index] + char + data[index + 1:]

# See: https://github.com/brandonasuncion/Reverse-Engineering-Bluetooth-Protocols#forming-a-response
CUSTOM_RESPONSE = "5506000200ff0042ff".decode("hex")
	
counter = 0xAE
recv = rx()
while recv:
	#bytes = " ".join([hex(ord(i)) for i in recv])
	size = ord(recv[1])
	#print("size: {}\t{}".format(size, bytes))
	
	if recv[0] == "\x55":
		
		if not sendResponse(recv):
			#print(hex(ord(recv[12])))
			if recv[12] == chr(0x4e):
				pass
			elif recv[12] == chr(0x41):
				print("ALERT: {}".format(hex(ord(recv[13]))))
			else:
				print("UNKNOWN ALERT")
		
			#print("\tSENDING CUSTOM PACKET")
			response = replaceChar(CUSTOM_RESPONSE, 5, recv[5])	# SEQ value
			response = replaceChar(response, 8, chr(counter))	# Counter value
			tx(response)
			
			counter = (counter - 1) % 256

			
	else:
		print("INVALID PACKET")
	
	recv = rx()

sock.close()