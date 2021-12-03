# IP-ARP-Vendor_lookup
This program ingests a Cisco "sh ip arp" as a text file and produces the list of vendors seen in the file 
## Why?
* Answers the question what are the different vendors seen in a Cisco ```#sh ip arp```
* Helps to understand what is in a network
## Requirements:
* This uses a restful API to search for the vendors, so it needs an internet connection
* This needs the output of a "#sh ip arp", as it is using this to do the lookup
## Input:
* Contents of a text file with the Cisco ```#sh ip arp``` output:
* ![image](https://user-images.githubusercontent.com/48565067/144638643-f26b64fe-e992-4163-a0a9-a1c90b0b6028.png)
## Output:
* Program output:
* ![image](https://user-images.githubusercontent.com/48565067/144634065-582c1eec-2576-4866-8057-112bf1f5e06d.png)
* Created text file "company_list.txt" output:
* ![image](https://user-images.githubusercontent.com/48565067/144633574-5bc13c04-a712-490d-b186-a30b4d9d8a73.png)
* Created text file "oui_final_list.txt" output:
* ![image](https://user-images.githubusercontent.com/48565067/144633706-24bbe2ef-6965-4847-b3a9-0f22242ff95f.png)


