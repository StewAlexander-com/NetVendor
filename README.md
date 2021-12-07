# IP-ARP-Vendor_lookup
This program reads a Cisco ARP table ("```sh ip arp```"), and produces information on what it contains, including:
* How many different vendors (as in companies) exist witin the ARP table
* How many OUIs (MAC Address hardware types) exist within the ARP table
* A list (and total) of all the Apple, Cisco, Dell and HP products exist in the ARP table

Table of Contents:
  - [Why?](#why)
  - [Requirements:](#requirements)
  - [Input:](#input)
  - [Output:](#output)
  - [To Do ...](#to-do-)

## Why?
* Answers the question what are the different vendors seen in a Cisco ```#sh ip arp```
* Helps to understand what is in a network
## Requirements:
* This uses a restful API to search for the vendors, so it needs an internet connection
* This needs the output of a "#sh ip arp", as it is using this to do the lookup
## Input:
* Contents of a text file with the Cisco ```#sh ip arp``` output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144638643-f26b64fe-e992-4163-a0a9-a1c90b0b6028.png)
## Output:
* Program output: </br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144634065-582c1eec-2576-4866-8057-112bf1f5e06d.png)
 ![image](https://user-images.githubusercontent.com/48565067/145064215-3486de68-051f-42ac-afb3-62472f5b4532.png)
* Created text file "company_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633574-5bc13c04-a712-490d-b186-a30b4d9d8a73.png)
* Created text file "oui_final_list.txt" output:</br></br>
 ![image](https://user-images.githubusercontent.com/48565067/144633706-24bbe2ef-6965-4847-b3a9-0f22242ff95f.png)
* Created Vendor-Devices.txt file:</br></br>
  ![image](https://user-images.githubusercontent.com/48565067/144880526-74cc7658-ae97-4841-812e-24f4f274525d.png)
## To Do ...
- [ ] Add a progress bar for collecting oui info via “tqdm”
- [x] Collect counts of Apple, Cisco, Dell, HP, & Other devices seen using this meta code
``` python
#For every line in the file check the MAC address
with open(ip_arp_file, 'r') as f:
    for line in f:
       #split the line into words
        words = line.split()
        #if words[2] is equal to the word "<address>”, print the line
        if words[2] == "<address>":
            #save the line to a file called "<vendor>-devices.txt"
            with open("Apple-Devices.txt", "a") as f:
                f.write(line)
#close the files
f.close()
```
- [x] If the device files are empty, delete them, else sort the lines by IP address (word 1) and count the lines
- [x] Print to the user there are “count” devices in the “ip_arp_file”, see the “<vendor> Device File” for the items
- [x] While “<vendor> Device File” exists, add the “count” to a variable “total-vendor-count”
- [x] “Other-count” = “total-arp-line-count” - “total-vendor-count”
- [x] Print to the user “there are ‘other-count’ other devices in the ‘ip_arp_file’ 
