# Vendor_lookup
This program reviews an ARP or MAC Addreess table (Such as a Cisco IOS ```sh ip arp``` or ```sh mac add``` output), and produces information on what it contains, including:
* How many different vendors (as in companies) exist witin the ARP / MAC table
* How many OUIs (MAC Address hardware types) exist within the ARP  / MAC table
* A list (and total) of all the Apple, Cisco, Dell, HP, and Mitel products that exist in the ARP / MAC table
* A list (and total) of all the VLANs within the ARP table

Table of Contents:
  - [Why?](#why)
  - [Dependencies](#dependencies)
  - [Input](#input)
  - [Output](#output)
  - [To Do](#to-do-)

## Why?
Answers the questions:
* What are the different products (companies) seen in the ARP / MAC table?
* How many different hardware types (OUIs) are there in the network? (The less there are, the safer a network is from a security standpoint)
* How many Apples, Ciscos, Dells, HPs, and Mitel's are on the network?
<br>
All of this is useful for understanding what is in a network for security and benchmarking purposes... <br>

## Dependencies 
* This uses a restful API to search for the vendors, so it needs a working internet connection
* This needs the output of an ARP or MAC Address table as a text file (such as the Cisco IOS ```#sh ip arp ``` format seen below), as it is using this to do the lookup
## Input
* Contents of a ARP or MAC Address table as a text file (such as a Cisco ```#sh ip arp``` output, like below):</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144638643-f26b64fe-e992-4163-a0a9-a1c90b0b6028.png)
## Output
* Program output: </br></br>
![program_output1](https://user-images.githubusercontent.com/48565067/156947568-60770c6b-f270-4087-abbc-7c7c40043439.png)
![program_output2](https://user-images.githubusercontent.com/48565067/156942018-807a5762-dcb8-49b0-b8df-fc33dec61433.png)
![program_output3](https://user-images.githubusercontent.com/48565067/156946968-1ab3e081-5925-43dd-a012-b65c85d53b3a.png)

 - If Chrome or Firefox is available (on a Windows, Mac or Linux system), it will create an interactive pie chart and display it in the browser:
 ![2022-03-06 18 43 25](https://user-images.githubusercontent.com/48565067/156947443-4510c608-b49f-4f3c-a8c9-60da13627ba6.png)
 * Created text file "company_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633574-5bc13c04-a712-490d-b186-a30b4d9d8a73.png)
* Created text file "oui_final_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633706-24bbe2ef-6965-4847-b3a9-0f22242ff95f.png)
* Created Vendor-Devices.txt file:</br></br>
  ![image](https://user-images.githubusercontent.com/48565067/144880526-74cc7658-ae97-4841-812e-24f4f274525d.png)
## To Do 
- [x] Use the [rich](https://github.com/Textualize/rich) library to colorize cli output (added 03/06/2022)
- [x] Correct minor style issues [on-going,fix applied 03/06/2022]
- [x] Added lookup for Mitel Corperation Phones (02/11/2022)
- [x] Streamlined API call, add support for Apple Macs (supporting Windows, Linux or Mac computers (Added 02/10/2022)
- [x] Add a progress bar for collecting oui info via “tqdm” (added 12/22/2021)
- [ ] Use the sanitized OUI list [here](https://linuxnet.ca/ieee/oui/), to increase filtering (on-going)
