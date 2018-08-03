# Reverse-Engineering a Bluetooth-Enabled Radar Detector
This document outlines the process I went through to reverse-engineer the Bluetooth protocol of my Cobra iRAD 900 radar detector. My initial goal was to have my Raspberry Pi 3 interface with the device via bluetooth to handle alerts *without* having to use the iOS/Android application, eventually to serve as a nice interface with my Raspberry Pi "carputer."

It's important to note that I had no initial experience with the Bluetooth protocol, but it was a pretty fun learning experience overall.

## Getting Started
When I first started this project, I had no idea where to begin but with Google. I knew how to sniff regular web traffic, but bluetooth was a bit of a black box to me. With some quick searching, I found the PyBluez library as well as examples on communicating through RFCOMM. I also found several good resources, including an interesting blog post by Travis Goodspeed.

However, will little guidance on the subject, I also spent a good amount of time on resources such as [this](https://learn.adafruit.com/reverse-engineering-a-bluetooth-low-energy-light-bulb/), thinking that Bluetooth LE was what I was looking for.

## Intercepting the Data
Playing around with my old jailbroken iPhone 5, I was able to use BTserver to log the bluetooth traffic sent and received by my iPhone. Being surrounded by multiple bluetooth devices, the log files grew quickly, though it was not much of an issue. Thankfully, the logs were outputted as a .pklg file, making it easy to filter the relevant packets in WireShark.

Using the packet filter `bluetooth.src == B8:92:1D:00:3F:61`, I could see the raw packets the iOS app was sending to the radar detector. I took a few sample recordings of the communication between my phone and the radar detector, some with alerts being generated, and some without.

## Analyzing the Protocol
The bluetooth data is transfered over the RFCOMM protocol. When the devices first connect, they send some information back and forth, probably just syncing settings (more on this later). Afterwards, the two devices follow a predictable pattern between one another. The radar detector will sends an RFCOMM packet through Bluetooth at regular 1/2 second intervals. With some time and patience, I was able to decipher the payload structure sent from the radar detector to the iPhone.

**Payload Structure:** Radar Detector → iPhone

| Item          | Value (hex)    | Size |
| ------------- |:--------------:| ---- |
| Preamble | 55 | 1 byte |
| Payload size | xx xx | 2 bytes |
| Action | xx | 1 byte |
| Reserved | 00 | 1 byte |
| SEQ | xx  | 1 byte |
| Reserved | xx xx xx xx xx xx | 6 bytes |
| Alert | xx | 1 byte |
| Alert Type | xx | 1 byte |
| ... | ... | ... |


As the radar detector is running, it will be sending packets in the above format. Though computer networking isn't my area of expertise, I'll try to explain as best as I could.

The preamble byte sent is always sent with the value `0x55`. This specifies that it is the beginning of a new payload message from the device, rather than continuing from a previous packet. Afterwards is a 2-byte value containing the size of the rest of the message (everything after the first 3 bytes). The action value specifies the type of information the packet is sending.

The SEQ number is where things start to get interesting. If you took a class on networking, or know a bit about TCP, you probably already know what it's for. The radar detector will send a 1-byte value to the iPhone, and the iOS application *must* respond with an ACK number of the same value. Otherwise, the radar detector will realize something is awry and disconnect itself.

The `Alert` byte specifies if an alert is being triggered. If so, it is set of value `0x41`, and the following byte is used to specify the type of alert is being sent. I couldn't find out too much about the values since I don't own an actual radar gun. Though, a guy on Instructables made a [LIDAR gun simulator](http://www.instructables.com/id/Test-your-radar-detector-or-laser-jammer-with-this/) using an Arduino. That helped a lot in analyzing the packets.

## Simulating a Response
In order to the iOS app to maintain the connection to the device, it needs to send a response in the correct format. Thankfully, the response to the radar detector is a lot more simple, and is only 9 bytes.

**Response:** iPhone → Radar Detector

| Item          | Value (hex)    | Size |
| ------------- |:--------------:| ---- |
| Preamble | 55 | 1 byte |
| Payload size | xx xx | 2 bytes |
| Action | 02 | 1 byte |
| Reserved | 00 | 1 byte |
| ACK | xx | 1 byte |
| Reserved | 00 42 | 2 bytes |
| Counter | xx | 1 byte |

As mentioned earlier, the ACK value must be the same value as the previously received SEQ value, otherwise the connection will be disconnected. That was easy enough. Some other protocols may have *much* less obvious methods of client checking; thankfully this was not the case. Interestingly, there is another `counter` variable that is used. I never really figured out what the byte is for, but it decrements by 1 for each response to the device. Both these values were easy enough to code into a Python script and didn't take too much work at all.

## What about the initial sync?
As I mentioned earlier, when the iOS app first connects to the radar detector, some settings and data are synchronized back and forth. It was not really a priority of mine to figure out and break down those packets, and I did not want to spend too much time on this. I exported the entire packet log in WireShark as an XML file (data.xml), then used a Python script (parseData.py) to process and store the information for later use.

## The Replay Attack
When loaded, radar.py will open the pre-processed data within the packetData.dat file. It then scans for the radar detector via Bluetooth and attempt to connect to it. Once connected, the radar detector will send over a few packets of data to the connected device. Thankfully, they are the same exact packets in the same exact sequence each time. The Python script will look through the data from the packetData.dat file for the packet that it received. Once the main Python script finds a maching packet, it sends the corresponding previously-recorded response to the radar detector.

Surprisingly, it worked out just fine. Though, I'd imagine I would need to update the data file if I changed any settings within the iOS app. It wasn't too much of an issue, since I would just need to configure the device once, and probably never use the app again.

## Putting Everything Together
Given all the information I found out, I was able to write a Python script that emulates the connection of the iPhone. If a packet is not found within the database of recorded responses, it constructs a response packet with the structure I previously detailed above.

Looking back, it was a really fun project doing something that I never really had experience with. As a Computer Science major, it was interesting doing something with hardware for once that's more or less out-of-the-ordinary.

## Files Included
* BTServerCaptures/*.pklg - data captured with BTServer
* data.xml - packet data exported by WireShark
* parseData.py - parses data.xml and saves it as packetData.dat
* radar.py - rough proof of concept to interface with radar detector

## Contact
Brandon Asuncion // <me@brandonasuncion.tech>

Any comments/feedback is appreciated!

## References and Further Reading
* [PyBluez](https://github.com/karulis/pybluez/) - Bluetooth Python library
* [PyBluez RFCOMM example](https://github.com/karulis/pybluez/blob/master/examples/simple/rfcomm-client.py) - example using PyBluez to communicate over Bluetooth
* [Bluetooth RFCOMM Reverse Engineering](http://travisgoodspeed.blogspot.com/2011/12/introduction-to-bluetooth-rfcomm.html) - Blog post by Travis Goodspeed
* [BTServer](https://www.theiphonewiki.com/wiki/Bluetooth#BTServer) - iOS Bluetooth stack daemon / How to Enable Bluetooth Logging

## License
* [MIT License](https://choosealicense.com/licenses/mit/)
