# Reverse-Engineering a Bluetooth-Enabled Radar Detector
This document outlines the process I went through to reverse-engineer the Bluetooth protocol of my Cobra iRAD 900 radar detector. My initial goal was to have my Raspberry Pi 3 interface with the device via bluetooth to handle alerts *without* having to use the iOS/Android application, eventually to serve as a nice interface with my Raspberry Pi "carputer."

It's important to note that I had no initial experience with the Bluetooth protocol, but it was a pretty fun learning experience overall.

## Getting Started
When I first started this project, I had no idea where to begin but with Google. I knew how to sniff regular web traffic, but bluetooth was a bit of a black box to me. With some quick searching, I found the PyBluez library as well as examples on communicating through RFCOMM. I also found several good resources, including an interesting blog post by Travis Goodspeed.

However, will little guidance on the subject, I also spent a good amount of time on resources such as [this](https://learn.adafruit.com/reverse-engineering-a-bluetooth-low-energy-light-bulb/), thinking that Bluetooth LE was what I was looking for.

## Analyzing the Protocol
Playing around with my old jailbroken iPhone 5, I was able to use BTserver to log the bluetooth traffic sent and received by my iPhone. Being surrounded by multiple bluetooth devices, the log files grew quickly, though it was not much of an issue. Thankfully, the logs were outputted as a .pklg file, making it easy to filter the relevant packets in WireShark.

Using the packet filter `bluetooth.src == B8:92:1D:00:3F:61`, I could see the raw packets the iOS app was sending to the radar detector. I took a few sample recordings of the communication between my phone and the radar detector, some with alerts being generated, and some without.

The bluetooth data is transfered over the RFCOMM protocol. When the devices first connect, they send some information back and forth (most likely syncing settings with the iOS App). Afterwards, the two devices follow a predictable pattern between one another. With some time and patience, I was able to decipher the payloads sent from the radar detector to the iPhone.

**Packet Data:** Radar dector -> iPhone

| Item          | Value (hex)    | Size |
| ------------- |:--------------:| ---- |
| Preamble | 55 | 1 byte |
| Payload size | xx xx | 2 bytes |
| Action | xx | 1 byte |
| Reserved | 00 | 1 byte |
| SEQ | xx  |1 byte |
| Reserved | xx xx xx xx xx xx | 6 bytes |
| Alert | xx | 1 byte |
| Alert Type | xx | 1 byte |
| ... | ... | ... |

It's important noting that the payload size does not include the first 3 bytes. Also, the SEQ packet increments each time, and the response packet must include an ACK of the same value.

### Forming a Response
After the two devices connect and synchronize settings, the radar detector sends a packet at regular 1/2 second intervals. The response to the radar detector is a lot more simple, and is only 9 bytes.

**Response:** iPhone -> Radar detector

| Item          | Value (hex)    | Size |
| ------------- |:--------------:| ---- |
| Preamble | 55 | 1 byte |
| Payload size | xx xx | 2 bytes |
| Action | 02 | 1 byte |
| Reserved | 00 | 1 byte |
| ACK | xx | 1 byte |
| Reserved | 00 42 | 2 bytes |
| Counter | xx | 1 byte |

The ACK byte should be the same value as the previously received SEQ value. Interestingly, there is another "counter" variable that is used. I never really figured out what the byte is for, but it decrements by 1 for every response back.

## What about the initial sync?
As I mentioned earlier, when the iOS app first connects to the radar detector, some settings and data are synchronized back and forth. It was not really a priority of mine to figure out and break down those packets, so I ended up doing a simple replay attack. I exported the entire packet log in WireShark as an XML file (data.xml), then used a Python script (parseData.py) to store the packet information for further use (within packetData.dat). Once the main Python script finds a maching packet, it sends a corresponding response to the radar detector.

Surprisingly, it worked out just fine. Though, I'd imagine I would need to update the data file if I changed any settings within the iOS app.

## Files Included
* BTServerCaptures/*.pklg - data captured with BTServer
* data.xml - packet data exported by WireShark
* parseData.py - parses data.xml and saves it as packetData.dat
* radar.py - rough proof of concept to interface with radar detector

## Contact
Brandon Asuncion - me@brandonasuncion.tech

If you have any feedback, please let me know!

## References and Further Reading
* [PyBluez](https://github.com/karulis/pybluez/) - Bluetooth Python library
* [PyBluez RFCOMM example](https://github.com/karulis/pybluez/blob/master/examples/simple/rfcomm-client.py) - example using PyBluez to communicate over Bluetooth
* [Bluetooth RFCOMM Reverse Engineering](http://travisgoodspeed.blogspot.com/2011/12/introduction-to-bluetooth-rfcomm.html) - Blog post by Travis Goodspeed
* [BTServer](https://www.theiphonewiki.com/wiki/Bluetooth) - iOS Bluetooth stack daemon