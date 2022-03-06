# Vendor_lookup
This program reviews an ARP or MAC Addreess table (Such as a Cisco IOS ```sh ip arp``` or ```sh mac add``` output), and produces information on what it contains, including:
* How many different vendors (as in companies) exist witin the ARP / MAC table
* How many OUIs (MAC Address hardware types) exist within the ARP  / MAC table
* A list (and total) of all the Apple, Cisco, Dell, HP, and Mitel products that exist in the ARP / MAC table
* A list (and total) of all the VLANs within the ARP table

Table of Contents:
  - [Why?](#why)
  - [Requirements](#requirements)
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

## Requirements
* This uses a restful API to search for the vendors, so it needs a working internet connection
* This needs the output of an ARP or MAC Address table as a text file (such as the Cisco IOS ```#sh ip arp ``` format seen below), as it is using this to do the lookup
## Input
* Contents of a ARP or MAC Address table as a text file (such as a Cisco ```#sh ip arp``` output, like below):</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144638643-f26b64fe-e992-4163-a0a9-a1c90b0b6028.png)
## Output
* Program output: </br></br>
 ![Screenshot from 2021-12-22 19-01-08](https://user-images.githubusercontent.com/48565067/147168300-38ffcb63-7c46-4abf-a188-0b6744e0bd35.png)
 ![Screenshot from 2021-12-22 19-03-29](https://user-images.githubusercontent.com/48565067/147168385-6488f96f-5946-4785-87b7-47e2a1245d6a.png)

 - If Chrome or Firefox is available (on a Windows, Mac or Linux system), it will create an interactive pie chart and display it in the browser:
 ![image](https://user-images.githubusercontent.com/48565067/145288325-e4daa630-ce3f-4487-99ec-5e0402f8edaf.png)
 * Created text file "company_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633574-5bc13c04-a712-490d-b186-a30b4d9d8a73.png)
* Created text file "oui_final_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633706-24bbe2ef-6965-4847-b3a9-0f22242ff95f.png)
* Created Vendor-Devices.txt file:</br></br>
  ![image](https://user-images.githubusercontent.com/48565067/144880526-74cc7658-ae97-4841-812e-24f4f274525d.png)
## To Do 
- [x] Added lookup for Mitel Corperation Phones (02/11/2022)
- [x] Streamlined API call, add support for Apple Macs (supporting Windows, Linux or Mac computers; Added 02/10/2022)
- [x] Add a progress bar for collecting oui info via “tqdm” (added 12/22/2021)
- [ ] Use the [rich](https://github.com/Textualize/rich) library to colorize cli output
- [ ] Use the sanitized OUI list [here](https://linuxnet.ca/ieee/oui/), to increase filtering (on-going)
