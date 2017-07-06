'''
    Takes an XML packet log exported from WireShark, parses it, then saves it
    into a serialized format within packetData.dat

    Brandon Asuncion <me@brandonasuncion.tech>
'''

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
                    
            
            self.packets.append({'num': num, 'data': data, 'raw': raw, 'size': size, 'direction': sent})
        
            
    def getResponse(self, received, direction = False):

        for i, packet in enumerate(self.packets):			
            if received == packet['raw']:
                j = i + 1
                while j < len(self.packets):
                    if self.packets[j]['direction'] != direction:
                        return self.packets[j]['data']
                    j = j + 1

    def generateSerializedFile(self, filename):
        with open(filename, 'wb') as fh:
            pickle.dump(self.packets, fh, protocol=2)
        
        
def main():
    parser = PacketParser('data.xml')

    # To test:
    # print(parser.getResponse(binascii.a2b_hex('550400380000c4')))
    
    parser.generateSerializedFile('packetData.dat')
    
if __name__ == "__main__":
    main()