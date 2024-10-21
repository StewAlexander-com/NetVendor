#!/usr/bin/env python3

#####################################
#                                   #
#      Created by Stew Alexander    #
#                2021               #
#                                   #
#####################################

import os
import sys
import csv
import time
import subprocess
import shutil

def check_module_installed(module_name):
    try:
        __import__(module_name)
        print(f"The module '{module_name}' is installed.")
    except ImportError:
        print(f"The module '{module_name}' is not installed, this is required to run NetVendor.")
        #end the program
        sys.exit()

# List of modules to check
modules_to_check = ["requests", "plotly", "tqdm", "rich"]

# Check each module in the list
for module in modules_to_check:
    check_module_installed(module)

# After handling modules should now safely be able to use the imported modules
import plotly.graph_objs as go
from rich import print

OUI_list = [] 
OUI_list_final = []
company_list =[]
company_list_final = []
vlan_list = []
vlan_list_final = []
word_list = []

print('''[yellow]
888888ba             dP   dP     dP                         dP                   
88    `8b            88   88     88                         88                   
88     88 .d8888b. d8888P 88    .8P .d8888b. 88d888b. .d888b88 .d8888b. 88d888b. 
88     88 88ooood8   88   88    d8' 88ooood8 88'  `88 88'  `88 88'  `88 88'  `88 
88     88 88.  ...   88   88  .d8P  88.  ... 88    88 88.  .88 88.  .88 88       
dP     dP `88888P'   dP   888888'   `88888P' dP    dP `88888P8 `88888P' dP       
[/yellow]''')


print('''[bright_blue]
 ┌─────────────────────────────────────────────────────┐
 │  [white]This app takes the output of a MAC Address Table[/white]   │
 │  [white]or IP ARP and finds all the vendors.[/white]               │
 │                                                     │
 │  [bright_red]Plus:[/bright_red]                                              │
 │  [white]It also collects the Apples, Ciscos, Dells, HPs[/white]    │
 │  [white]and Mitel Phones in your network into csv files[/white]    │
 │  [white]that you can easily import into a spreadsheet[/white]      │
 └─────────────────────────────────────────────────────┘
[/bright_blue]''')



# Get the current working directory and store it in a variable called "cwd"
cwd = os.getcwd()

# Show the contents of the current directory
print("\nPlease select the [italic green]ARP[/italic green] or [italic green]MAC[/italic green] Data text file from [cyan]"+cwd+"[/cyan] \n")
print(os.listdir(), "\n")

# while the file name is not valid, ask the user to input the file name again
while True:
    ip_arp_file = input("Please enter the file name: ")
    if os.path.isfile(ip_arp_file):
        break
    else:
        print("\n[italic yellow]The file name is not valid, please try again[/italic yellow]\n")

#Ask the user to input which word containts the MAC_Element
print("Please enter the column in the file that contains the [cyan]Mac Addresses[/cyan]:")
mac_temp = input("> ")

#convert the input to an int and subtract 1 to match the column number
mac_column = int(mac_temp)
mac_word = mac_column - 1

#Ask the user to input which word containts the VLAN_Element
print("\nPlease enter the column in the file that contains the [cyan]VLANs[/cyan]:")
vlan_temp = input("> ")

#convert the input to an int and subtract 1 to match the column number
vlan_column = int(vlan_temp)
vlan_word = vlan_column - 1


with open(ip_arp_file, 'r') as f:
        for line in f:
            #split the line into words
            words = line.split()
            #send words[mac_word] to a list
            MAC_Element = words[mac_word]
            #copy the first 7 characters to a new list called OUI_list
            OUI_ELEMENT= MAC_Element[0:7]
            #split oui_list into different elements
            OUI_ELEMENT = OUI_ELEMENT.split()
            #append OUI_ELEMENT to a list called OUI_list
            OUI_list.append(OUI_ELEMENT)

#sort OUI_list
OUI_list.sort()

# Deduplicate the list by leveraging set properties if the list is unordered.
OUI_list_final = [OUI_list[i] for i in range(len(OUI_list)) if i == 0 or OUI_list[i] != OUI_list[i-1]]

# Write the final list to a file, each element on a new line.
with open('oui_list_final.txt', 'w') as f:
    f.writelines(f'{item}\n' for item in OUI_list_final)

#Check each line of the file oui_list_final.txt if it is 'MAC' delete it
with open('oui_list_final.txt', 'r') as f:
    lines = f.readlines()
with open('oui_list_final.txt', 'w') as f:
    for line in lines:
        if line.strip("\n") != 'MAC':
            f.write(line)

#Check each line of the file oui_list_final.txt if it is 'INCOMPL' delete it
with open('oui_list_final.txt', 'r') as f:
    lines = f.readlines()
with open('oui_list_final.txt', 'w') as f:
    for line in lines:
        if line.strip("\n") != 'INCOMPL':
            f.write(line)

#close the file
f.close()

#print please be patient the vendor information is being retrieved
print("\n[italic yellow]Please be patient while the [cyan]company[/cyan] information is being retrieved[/italic yellow]\n")

#for each line in the file oui_list_final.txt, store this in a list called vendor_list
vendor_list = []
with open('oui_list_final.txt', 'r') as f:
    for line in f:
        vendor_list.append(line)

#for each element in vendor_list do a request to the OUI database
for i in tqdm (range(len(vendor_list)), colour="cyan"):
    #make each element uppercase
    vendor_list[i] = vendor_list[i].upper()
    #try to get the vendor for 2 seconds
    try:
        r = requests.get("https://macvendors.co/api/vendorname/" + vendor_list[i], timeout=2)
        #if the request is successful, print the vendor name
        if r.status_code == 200:
        #save the vendor name to a file called vendor_list.txt
            with open('oui_name_result.txt', 'a') as f:
                f.write(r.text + '\n')
        #else if the request is not successful, print the error message
        else:
            print("\nError:", r.status_code, r.reason)
    except requests.exceptions.Timeout:
        print("\nRequest Timed Out")

#close the file
f.close()

#Check each line of the file vendor_list.txt if it is "No vendor" delete it

with open('oui_name_result.txt', 'r') as f:
    lines = f.readlines()
with open('oui_name_result.txt', 'w') as f:
  for line in lines:
      if line.strip("\n") != 'No vendor':
          f.write(line)

#close the file
f.close()

time.sleep(1)

#open the text file oui_name_result.txt and read it, look for company name
with open('oui_name_result.txt', 'r') as f:
    for line in f:
        #load the line into a list called company_list
        company_list.append(line)

#close the file
f.close()

#sort company_list
company_list.sort()

# Initialize the final list with the first element if the list is not empty
company_list_final = [company_list[0]] if company_list else []

# Iterate over the company list starting from the second element
for current_company, previous_company in zip(company_list[1:], company_list[:-1]):
    if current_company != previous_company:
        company_list_final.append(current_company)

print(f"\n\nThe companies seen in the [italic green]{ip_arp_file}[/italic green] data file are:\n")

# Save the deduplicated company list to a file
with open('company_list.txt', 'w') as f:
    for company in company_list_final:
        f.write(company)

# Print the list of companies with formatting
for company in company_list_final:
    # Using .rstrip() to remove the newline character
    print(f"[cyan]{company.rstrip()}[/cyan]")

#Collecting the output of the command sh ip arp
print ("\n\n[italic yellow]Please be patient, while information is being retrieved[/italic yellow]\n")

#######################################################################################

#Finding all the Apple ARP Entries ....

#Delete the file Apple-Devices.txt if it exists
if os.path.exists('Apple-Devices.txt'):
    os.remove('Apple-Devices.txt')
else :
    pass

print ("\nFinding any [cyan]Apple[/cyan] devices in the [italic green]" + ip_arp_file + "[/italic green] file....")

#For every line in the file check the MAC address, if it is an Apple Address, add it the Apple-Devices.txt

# Define Apple OUIs
apple_ouis = {"0c4d.e9", "109a.dd", "10dd.b1", "28ff.3c", "38c9.86", 
              "3c7d.0a", "501f.c6", "685b.35", "7cd1.c3", "8866.5a", 
              "9c20.7b", "a860.b6", "d081.7a", "cc29.f5"}

with open(ip_arp_file, 'r') as input_file, open('Apple-Devices.txt', 'a') as output_file:
    for line in tqdm(input_file, colour="cyan"):
        words = line.split()
        if any(words[mac_word].startswith(oui) for oui in apple_ouis):
            output_file.write(line)

if os.path.exists('Apple-Devices.txt'):
#read the file Apple-Devices.txt and store the total number of lines in a variable called Apple-count
    with open('Apple-Devices.txt', 'r') as f:
        Apple_count = 0
        for line in f:
            Apple_count += 1
else:
    Apple_count = 0
    pass

#######################################################################################

#Finding all the Dell ARP Entries ....

#Delete the file Dell-Devices.txt if it exists
if os.path.exists('Dell-Devices.txt'):
    os.remove('Dell-Devices.txt')
else :
    pass

print ("\nFinding any [cyan]Dell[/cyan] devices in the [italic green]" + ip_arp_file + "[/italic green] file....")

from tqdm import tqdm

# Define the list of Dell OUIs (Organizationally Unique Identifiers)
dell_ouis = {
    "001a.a0", "004e.01", "14b3.1f", "14fe.b5", "1866.da", "28f1.0e", "484d.7e", "509a.4c",
    "5448.10", "54bf.64", "6400.6a", "6c2b.59", "782b.cb", "8cec.4b", "a41f.72", "a4bb.6d",
    "b083.fe", "b885.84", "b8ca.3a", "bc30.5b", "c81f.66", "d4be.d9", "d89e.f3", "e454.e8",
    "e4f0.04", "f04d.a2", "f402.70", "f48e.38", "f8bc.12", "0006.5b", "0008.74", "000b.db",
    "000d.56", "000f.1f", "0011.43", "0012.3f", "0013.72", "0014.22", "0015.c5", "0016.f0",
    "0018.8b", "0019.b9", "001c.23", "001d.09", "001e.4f", "001e.c9", "0021.70", "0021.9b",
    "0022.19", "0023.ae", "0024.e8", "0025.64", "0026.b9", "00b0.d0", "00be.43", "00c0.4f",
    "0892.04", "0c29.ef", "1065.30", "107d.1a", "1098.36", "1418.77", "149e.cf", "1803.73",
    "185a.58", "18a9.9b", "18db.f2", "18fb.7b", "1c40.24", "1c72.1d", "2004.0f", "2047.47",
    "246e.96", "2471.52", "24b6.fd", "2cea.7f", "30d0.42", "3417.eb", "3473.5a", "448e.db"
}

# Function to check if a MAC address belongs to Dell
def is_dell_mac(mac):
    return any(mac.lower().startswith(oui) for oui in dell_ouis)

# Read the file and write Dell MAC addresses to the output file
with open(ip_arp_file, 'r') as f, open('Dell-Devices.txt', 'a') as dell_file:
    for line in tqdm(f, colour="cyan"):
        words = line.split()
        if is_dell_mac(words[mac_word]):
            dell_file.write(line)


#close the files
f.close()

if os.path.exists('Dell-Devices.txt'):
#read the file Dell-Devices.txt and store the total number of lines in a variable called Dell-count
    with open('Dell-Devices.txt', 'r') as f:
        Dell_count = 0
        for line in f:
            Dell_count += 1
else:
    Dell_count = 0
    pass

#######################################################################################
#Finding all the Cisco Meraki ARP Entries ....

#Delete the file Cisco-Meraki-Devices.txt if it exists
if os.path.exists('Cisco-Meraki-Devices.txt'):
    os.remove('Cisco-Meraki-Devices.txt')
else :
    pass

print ("\nFinding any [cyan]Cisco Meraki[/cyan] devices in the [italic green]" + ip_arp_file + "[/italic green] file....")

from tqdm import tqdm

# Define the list of Cisco-Meraki OUIs
meraki_ouis = {"ac17.c8", "f89e.28"}

# Function to check if a MAC address belongs to Cisco-Meraki
def is_meraki_mac(mac):
    return any(mac.lower().startswith(oui) for oui in meraki_ouis)

# Read the input file and write Cisco-Meraki MAC addresses to the output file
with open(ip_arp_file, 'r') as f, open('Cisco-Meraki-Devices.txt', 'a') as meraki_file:
    for line in tqdm(f, colour='cyan'):
        words = line.split()
        if is_meraki_mac(words[mac_word]):
            meraki_file.write(line)
            # Removed the time.sleep(0.1) to improve efficiency

if os.path.exists('Cisco-Meraki-Devices.txt'):
#read the file Cisco-Meraki-Devices.txt and store the total number of lines in a variable called Cisco-Meraki-count
    with open('Cisco-Meraki-Devices.txt', 'r') as f:
        CiscoMeraki_count = 0
        for line in f:
            CiscoMeraki_count += 1
else:
    CiscoMeraki_count = 0
    pass

#######################################################################################
#Finding all the Other Cisco ARP Entries ....

#Delete the file Other-Cisco-Devices.txt if it exists
if os.path.exists('Other-Cisco-Devices.txt'):
    os.remove('Other-Cisco-Devices.txt')
else :
    pass

print ("\nFinding any other [cyan]Cisco[/cyan] devices in the [italic green]" + ip_arp_file + "[/italic green] file....")


# Define the list of Other-Cisco OUIs
other_cisco_ouis = {
    "0007.7d", "0008.2f", "0021.a0", "0022.bd", "0023.5e",
    "003a.99", "005f.86", "00aa.6e", "0cf5.a4", "1833.9d",
    "1ce8.5d", "30e4.db", "40f4.ec", "4403.a7", "4c4e.35",
    "544a.00", "5486.bc", "588d.09", "58bf.ea", "6400.f1",
    "7c21.0d", "84b5.17", "8cb6.4f", "ac17.c8", "ac7e.8a",
    "bc67.1c", "c4b3.6a", "d4ad.71", "e0d1.73", "e8b7.48",
    "f09e.63", "f866.f2", "0025.45", "002a.6a"
}

# Function to check if a MAC address belongs to Other-Cisco
def is_other_cisco_mac(mac):
    return any(mac.lower().startswith(oui) for oui in other_cisco_ouis)

# Read the input file and write Other-Cisco MAC addresses to the output file
with open(ip_arp_file, 'r') as f, open('Other-Cisco-Devices.txt', 'a') as cisco_file:
    for line in tqdm(f, colour='cyan'):
        words = line.split()
        if is_other_cisco_mac(words[mac_word]):
            cisco_file.write(line)
            # Removed the time.sleep(0.1) to improve efficiency

if os.path.exists('Other-Cisco-Devices.txt'):
#read the file Other-Cisco-Devices.txt and store the total number of lines in a variable called Other-Cisco-count
    with open('Other-Cisco-Devices.txt', 'r') as f:
        OtherCisco_count = 0
        for line in f:
            OtherCisco_count += 1
else:
    OtherCisco_count = 0
    pass

#######################################################################################

#sleep for 1 second
time.sleep(1)

#Finding all the Mitel Corperation Entries ....

#Delete the file Mitel-Devices.txt if it exists
if os.path.exists('Mitel-Devices.txt'):
    os.remove('Mitel-Devices.txt')
else :
    pass

print ("\nFinding any [cyan]Mitel[/cyan] devices in the [italic green]" + ip_arp_file + "[/italic green] file....")


# Function to check if a MAC address belongs to Mitel
def is_mitel_mac(mac):
    return mac.lower().startswith("0800.0f")

# Read the input file and write Mitel MAC addresses to the output file
with open(ip_arp_file, 'r') as f, open('Mitel-Devices.txt', 'a') as mitel_file:
    for line in tqdm(f, colour='cyan'):
        words = line.split()
        if is_mitel_mac(words[mac_word]):
            mitel_file.write(line)
            # Removed the time.sleep(0.1) to improve efficiency

if os.path.exists('Mitel-Devices.txt'):
#read the file Mitel-Devices.txt and store the total number of lines in a variable called Mitel-count
    with open('Mitel-Devices.txt', 'r') as f:
        Mitel_count = 0
        for line in f:
            Mitel_count += 1
else:
    Mitel_count = 0
    pass

#######################################################################################

#Finding all the HP ARP Entries ....

#Delete the file HP-Devices.txt if it exists
if os.path.exists('HP-Devices.txt'):
    os.remove('HP-Devices.txt')
else :
    pass

print ("\nFinding any [cyan]HP[/cyan] devices in the [italic green]" + ip_arp_file + "[/italic green] file....")


# A set of HP OUIs for faster membership testing
hp_ouis = {
    "0017.a4", "001b.78", "0023.7d", "0030.6e", "009c.02", "1062.e5",
    "3024.a9", "308d.99", "30e1.71", "3822.e2", "38ea.a7", "40b0.34",
    "68b5.99", "6cc2.17", "80ce.62", "80e8.2c", "8434.97", "98e7.f4",
    "9cb6.54", "a08c.fd", "a0d3.c1", "a45d.36", "b00c.d1", "e4e7.49",
    "ec8e.b5", "f092.1c", "f430.b9", "fc15.b4"
}

# Function to check if a MAC address belongs to HP
def is_hp_mac(mac):
    return any(mac.startswith(oui) for oui in hp_ouis)

# Read the input file and write HP MAC addresses to the output file
with open(ip_arp_file, 'r') as source_file, open('HP-Devices.txt', 'a') as hp_file:
    for line in tqdm(source_file, colour='cyan'):
        words = line.split()
        if is_hp_mac(words[mac_word]):
            hp_file.write(line)
            # Removed the time.sleep(0.1) to improve efficiency

if os.path.exists('HP-Devices.txt'):
#read the file HP-Devices.txt and store the total number of lines in a variable called HP-count
    with open('HP-Devices.txt', 'r') as f:
        HP_count = 0
        for line in f:
            HP_count += 1
else:
    HP_count = 0
    pass

#######################################################################################
# Find all the unique vlans in the ip_arp_file
print("\n[bold yellow]Misc details about the [italic green]" + ip_arp_file + "[/italic green] file....[/bold yellow]")

with open(ip_arp_file, 'r') as f:
        for line in f:
            #split the line into words
            vlanwords = line.split()
            #send words[vlanword] to a list
            vlan_Element = vlanwords[vlan_word]
            #split vlan_Element into different elements
            vlan_Element = vlan_Element.split()
            #append vlan_Element to a list called vlan_list
            vlan_list.append(vlan_Element)

#sort the vlan_list
vlan_list.sort()

# Initialize the final list with the first element from the original list if it's not empty
vlan_list_final = [vlan_list[0]] if vlan_list else []

# Compare each element to the previous one and save if different
for current, previous in zip(vlan_list[1:], vlan_list[:-1]):
    if current != previous:
        vlan_list_final.append(current)

# Save the final list to a file
with open('vlan_list_final.txt', 'w') as f:
    for vlan in vlan_list_final:
        f.write(vlan[0] + '\n')

#Check each line of the file vlan_list.txt if it is "Interface" delete it
with open('vlan_list.txt', 'r') as f:
    lines = f.readlines()
with open('vlan_list.txt', 'w') as f:
  for line in lines:
      if line.strip("\n") != "Interface":
          f.write(line)

# count the lines in the file vlan_list_final.txt and print the number of lines
with open('vlan_list.txt', 'r') as f:
    vlan_count = 0
    for line in f:
        vlan_count += 1
    print ("\n[bold yellow]++[/bold yellow] [bright_red]" + str(vlan_count) + "[/bright_red] unique [cyan]VLANs[/cyan]")
    

#######################################################################################


# count the lines in the file oui_list_final.txt and print the number of lines

with open('oui_list_final.txt', 'r') as f:
    OUI_count = 0
    for line in f:
        OUI_count += 1
    print ("[bold yellow]++[/bold yellow] [bright_red]" + str(OUI_count) + "[/bright_red] unique [cyan]OUI's[cyan]  ")
    f.close()
    

#count the lines in the file company_list.txt and print the number of lines
with open('company_list.txt', 'r') as f:
    count = 0
    for line in f:
        count += 1
    print ("[bold yellow]++[/bold yellow] [bright_red]" + str(count) + "[/bright_red] [cyan]companies[/cyan]")
    f.close()
    
#count the lines in the ip_arp_file.txt and print the number of lines
with open( ip_arp_file, 'r') as f:
    count = 0
    for line in f:
        count += 1
    print ("[bold yellow]++[/bold yellow] [bright_red]" + str(count) + "[/bright_red] [cyan]total devices[/cyan] ")
    arpcount = count-1
    f.close()

OtherTotal = arpcount - (Apple_count + Dell_count + CiscoMeraki_count + OtherCisco_count + HP_count + Mitel_count)

#######################################################################################

print("\n")
print ("[bold yellow]Device Counts in the [italic green]" + ip_arp_file + "[/italic green] file:[/bold yellow]\n")
print ("[bright_green]#[/bright_green] [bright_red]" +str(Apple_count)+ "[/bright_red] [cyan]Apple devices[/cyan]")
print ("[bright_green]#[/bright_green] [bright_red]" +str(Dell_count)+ "[/bright_red] [cyan]Dell devices[/cyan]")   
print ("[bright_green]#[/bright_green] [bright_red]" +str(CiscoMeraki_count)+ "[/bright_red] [cyan]Cisco-Meraki devices[/cyan]")
print ("[bright_green]#[/bright_green] [bright_red]" + str(OtherCisco_count)+ "[/bright_red] [cyan]other Cisco devices[/cyan]")
print ("[bright_green]#[/bright_green] [bright_red]"+ str(HP_count)+ "[/bright_red][cyan] HP devices[/cyan]")
print ("[bright_green]#[/bright_green] [bright_red]"+ str (Mitel_count)+ "[/bright_red] [cyan]Mitel devices[/cyan]")
print ("[bright_green]#[/bright_green] [bright_red]"+ str(OtherTotal)+ "[/bright_red] [cyan]other devices[/cyan]")
print("\n")

#######################################################################################

#Plotting the Apple, Dell, Cisco-Meraki, Other Cisco, HP, Mitel and Other devices

labels = ['Apple', 'Dell', 'Cisco-Meraki', 'Other Cisco', 'HP', 'Mitel','Other']
values = [Apple_count, Dell_count, CiscoMeraki_count, OtherCisco_count, HP_count, Mitel_count, OtherTotal]

#check if Google Chrome or Firefox or is installed on Windows, Linux or Mac
if os.path.exists('C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe') or os.path.exists('C:\\Program Files\\Google\\Chrome\\Application\\Firefox.exe'):
    fig =go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.show()
elif os.path.exists('/usr/bin/google-chrome') or os.path.exists('/usr/bin/firefox'):
    fig =go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.show()
elif os.path.exists('/Applications/Google Chrome.app') or os.path.exists('/Applications/Firefox.app'):
    fig =go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.show()
else:
    pass   

#######################################################################################
#define a function to convert the text file to a csv file
def make_csv(file): 
    
    # Maybe set word_list to null may help having the CSV issue?
    word_list.clear()

    #open the file in read mode
    with open(file, 'r') as f:
        for line in f:
            words = line.split()
            word_list.append(words)  
    #close the file
    f.close()

    #create a new csv file
    csv_file =file.replace(".txt", ".csv")
    time.sleep(0.5)

    #save the word_list to the csv file
    with open(csv_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(word_list)
    #close the file
    f.close()
    time.sleep(0.5)
    
    #Convert the newline characters to a PC format
    with open(csv_file , 'r') as f:
        data = f.read().replace('\r', '')
    time.sleep(0.5)

    #overwrite the file with the new data
    with open(csv_file, 'w') as f:
        f.write(data)
    #close the file
    f.close()
    time.sleep(0.5)

    #Remove duplicate \n characters from the file
    with open(csv_file, 'r') as f:
        data = f.read().replace('\n\n', '\n')
    #close the file
    f.close()
    time.sleep(0.5)

    #overwrite the file with the new data
    with open(csv_file, 'w') as f:
        f.write(data)
    #close the file
    f.close()
    time.sleep(0.5)

    #if folder csv_files does not exist create it
    if not os.path.exists('csv_files'):
        os.makedirs('csv_files')
    else:
        pass
    time.sleep(0.5) 

    #move the csv file to the csv_files folder, if a copy does not exist
    if not os.path.exists('csv_files/' + csv_file):
        shutil.move(csv_file, 'csv_files/' + csv_file)
    else:
        pass

#######################################################################################
# Created file list

print ("[bold yellow]Created file list in the [cyan]text_files[/cyan] folder:[/bold yellow]\n")
print("[magenta]>>>[/magenta][italic green] oui_list_final.txt[/italic green] file for the list of [cyan]OUIs[/cyan]")
print("[magenta]>>>[/magenta][italic green] company_list.txt[/italic green] file for the list of [cyan]companies[/cyan]") 
print("[magenta]>>>[/magenta][italic green] vlan_list.txt[/italic green] file for the list of [cyan]VLANs[/cyan]")

if os.path.exists('Apple-Devices.txt'):
    print("[magenta]>>>[/magenta][italic green] Apple-Devices.txt[/italic green] file for the list of [cyan]Apple[/cyan] devices")
    #call function make-csv to convert the text file to a csv file
    make_csv('Apple-Devices.txt')
    f.close()
else:
    pass

if os.path.exists('Dell-Devices.txt'):
    print("[magenta]>>>[/magenta][italic green] Dell-Devices.txt[/italic green] file for the list of [cyan]Dell[/cyan] devices")
    #call function make-csv to convert the text file to a csv file
    make_csv('Dell-Devices.txt')
    f.close()
    pass

if os.path.exists('Cisco-Meraki-Devices.txt'):
    print("[magenta]>>>[/magenta][italic green] Cisco-Meraki-Devices.txt[/italic green] file for the list of [cyan]Cisco-Meraki[/cyan] devices")
    #call function make-csv to convert the text file to a csv file
    make_csv('Cisco-Meraki-Devices.txt')
    f.close()   
else:
    pass

if os.path.exists('Other-Cisco-Devices.txt'):
    print("[magenta]>>>[/magenta][italic green] Other-Cisco-Devices.txt[/italic green] file for the list of [cyan]Other Cisco[/cyan] devices")
    #call function make-csv to convert the text file to a csv file
    make_csv('Other-Cisco-Devices.txt')
    f.close()
else:
    pass

if os.path.exists('HP-Devices.txt'):
    print("[magenta]>>>[/magenta][italic green] HP-Devices.txt[/italic green] file for the list of [cyan]HP[/cyan] devices")
    #call function make-csv to convert the text file to a csv file
    make_csv('HP-Devices.txt')
    f.close()
else:
    pass

if os.path.exists('Mitel-Devices.txt'):
    print("[magenta]>>>[/magenta][italic green] Mitel-Devices.txt[/italic green] file for the list of [cyan]Mitel[/cyan] devices")
    #call function make-csv to convert the text file to a csv file
    make_csv('Mitel-Devices.txt')
    f.close()
else:
    pass

#if the folder csv_files exists, then print the following message
if os.path.exists('csv_files'):
    print("\n[bold yellow]##[/bold yellow] See the [cyan]csv_files[/cyan] folder for the csv files\n")
    pass 

#Check if there are any .txt files in the current directory
for file in os.listdir():
    if file.endswith(".txt"):
        if not os.path.exists('text_files'):
            os.makedirs('text_files')
        else:
            pass
    else:
        pass

#move the .txt files to the text_files folder
for file in os.listdir():
    if file.endswith(".txt"):
        #if file does not exist in the text_files folder, then move it
        if not os.path.exists('text_files/' + file):
            shutil.move(file, 'text_files')
        else:
            print("[bold red]##[/bold red] The [cyan]" + file + "[cyan] file already exists in the [cyan]text_files[/cyan] folder")
    else:
        pass

#close any remainng files
f.close()

#tell the user to press enter to quit
input("\nPress enter to quit: ")
time.sleep(3)
#exit the program
sys.exit()
