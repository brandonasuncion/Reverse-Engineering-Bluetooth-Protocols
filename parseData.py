import xml.etree.ElementTree as ET
import binascii
import pickle

class PacketParser:
	def __init__(self, filename):
		tree = ET.parse(filename)
		root = tree.getroot()
		
		self.packets = []
		
		for i, packet in enumerate(root):
			num = packet[0][0].attrib['show']
			
			sent = packet[2][3].attrib['show'] == "b8:92:1d:00:3f:61"	# True:  phone -> radar detector
			
			data = b''
			
			if packet[-1].attrib['name'] == 'fake-field-wrapper':
				data = packet[-1][0].attrib['value']
			else:
				continue
			
			
			raw = binascii.a2b_hex(data)
			size = raw[1]
					
			if raw[0] != 0x55:
				continue
				
			j = i + 1
			while len(raw) < size + 3:
				if (root[j][2][3].attrib['show'] == packet[2][3].attrib['show']) and (root[j][-1].attrib['name'] == 'fake-field-wrapper'):
					data = data + root[j][-1][0].attrib['value']
					raw = raw + binascii.a2b_hex(root[j][-1][0].attrib['value'])
					if len(raw) != size + 3:
						print("ERROR: REST OF DATA IS MISSING")
						continue
				j = j + 1
				
				if j >= len(root):
					print("CANNOT FIND REST OF DATA")
					continue
					
			#self.packets[num] = {'num': num, 'data': data, 'raw': raw, 'size': size, 'direction': sent}	# dictionary
			self.packets.append({'num': num, 'data': data, 'raw': raw, 'size': size, 'direction': sent})	# list
			#print("{}\t{} ({}):\t{}".format(num, "SENT" if sent else "RECV", size, data))
		
			
	def getResponse(self, received, direction = False):
		"""
		# dictionary
		found = False
		for num, packet in self.packets.items():
			if found:
				print("{}: {}".format(packet['num'], packet['data']))
				return packet['data']
			if packet['raw'] == received:
				found = True
			print(num)
		"""
		
		# using lists
		for i, packet in enumerate(self.packets):			
			if received == packet['raw']:
				j = i + 1
				while j < len(self.packets):
					if self.packets[j]['direction'] != direction:
						return self.packets[j]['data']
					j = j + 1

	def generateSerializedFile(self, filename):
		"""
		fileData = {}
		
		for i, packet in enumerate(self.packets):			
			if not packet['direction']:
				j = i + 1
				while j < len(self.packets):
					if self.packets[j]['direction']:
						fileData[packet['raw']] = self.packets[j]['raw']
						break
					j = j + 1
		
		with open(filename, 'wb') as fh:
			pickle.dump(fileData, fh, protocol=2)
		"""
		with open(filename, 'wb') as fh:
			pickle.dump(self.packets, fh, protocol=2)
		
		
def main():
	parser = PacketParser('data.xml')
	
	#response = parser.getResponse(binascii.a2b_hex('550400380000c4'))
	#print(response)
	
	parser.generateSerializedFile('packetData.dat')
	
	
if __name__ == "__main__":
	main()