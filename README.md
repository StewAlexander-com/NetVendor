# IP-ARP-Vendor_lookup
This program ingests a Cisco "sh ip arp" as a text file and produces the list of vendors seen in the file 
## Why?
* Answers the question what are the different vendors seen in a Cisco ```#sh ip arp```
* Helps to understand what is in a network
## Requirements:
* This uses a restful API to search for the vendors, so it needs an internet connection
* This needs the output of a "#sh ip arp", as it is using this to do the lookup
## Output:
* Program Output:
![image](https://user-images.githubusercontent.com/48565067/144515835-c257c887-d154-468e-82ce-535992a6d1c9.png)
* Vendor_list.txt Output:
![image](https://user-images.githubusercontent.com/48565067/144516045-d56d824e-2f7f-4bd0-808c-b0e17b70da61.png)
