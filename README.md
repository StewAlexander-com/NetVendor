# IP-ARP-Vendor_lookup
This program reads a Cisco ARP table ("```sh ip arp```"), and produces information on what it contains, including:
* How many different vendors (as in companies) exist witin the ARP table
* How many OUIs (MAC Address hardware types) exist within the ARP table
* A list (and total) of all the Apple, Cisco, Dell and HP products that exist in the ARP table
* A list (and total) of all the VLANs within the ARP table

Table of Contents:
  - [Why?](#why)
  - [Requirements](#requirements)
  - [Input](#input)
  - [Output](#output)
  - [To Do](#to-do-)

## Why?
Answers the questions:
* What are the different companies seen in the ARP table?
* How many different hardware types (OUIs) are there in the network?
* How many Apples, Ciscos, Dells, and HPs does this equipment / network see?
<br>
All Of this is useful for understanding what is in a network for security purposes... <br>

## Requirements
* This uses a restful API to search for the vendors, so it needs an internet connection
* This needs the output of an ARP table (in the format seen below), as it is using this to do the lookup
## Input
* Contents of a ARP table as a text file (such as a Cisco ```#sh ip arp``` output):</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144638643-f26b64fe-e992-4163-a0a9-a1c90b0b6028.png)
## Output
* Program output: </br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144634065-582c1eec-2576-4866-8057-112bf1f5e06d.png)
 ![image](https://user-images.githubusercontent.com/48565067/145101360-d6cf7cf1-bb5e-4608-bf20-f2b9fddfc63f.png)
 * Created text file "company_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633574-5bc13c04-a712-490d-b186-a30b4d9d8a73.png)
* Created text file "oui_final_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633706-24bbe2ef-6965-4847-b3a9-0f22242ff95f.png)
* Created Vendor-Devices.txt file:</br></br>
  ![image](https://user-images.githubusercontent.com/48565067/144880526-74cc7658-ae97-4841-812e-24f4f274525d.png)
## To Do 
- [ ] Add a progress bar for collecting oui info via “tqdm”

