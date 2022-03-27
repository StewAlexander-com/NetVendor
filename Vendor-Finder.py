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
import json

#check if the rich module exists, if not, install it
try:
    from rich import print
    from rich import pretty
except ImportError:
    subprocess.call([sys.executable, "-m", "pip", "install", "rich"])
    import rich
    time.sleep (1)
     #tell the user the library is installed
    print("[!] Rich module is now installed")
    #Tell the user to please restart the program
    print("Please restart the program")
    time.sleep(3)
    sys.exit()

#check if the tqdm module exists, if not install it
try :
    from tqdm import tqdm
except ImportError:
    subprocess.call([sys.executable, "-m", "pip", "install", "tqdm"])
     #tell the user the library is installed
    print("[!] The tqdm library is now installed")
    #tell the user to please restart the program
    print("Please restart the program")
    time.sleep(3)
    sys.exit()

#check if the plotly module exists, if not install it
try :
    import plotly
    import plotly.graph_objs as go
except ImportError:
    print("[!] Plotly library not installed, Installing...")
    os.system("pip3 install plotly")
    time.sleep(1)
     #tell the user the library is installed
    print("[!] Plotly library is now installed")
    #tell the user to please restart the program
    print("Please restart the program")
    time.sleep(3)


#if the library requests is not installed, install it via pip
try:
    import requests
except ImportError:
    print("[!] The requests library is not installed. Installing...")
    os.system("pip install requests")
    time.sleep(1)
    #tell the user the library is installed
    print("[!] The requests library is now installed")
    #tell the user to please restart the program
    print("Please restart the program")
    time.sleep(3)
    sys.exit()

#if the csv library is not installed, install it via pip
try:
    import csv
except ImportError:
    print("[!] The csv library is not installed. Installing...")
    os.system("pip install csv")
    print("[!] The csv library has been installed.")
    time.sleep(1)
    #tell the user to please restart the program
    print("Please restart the program")
    time.sleep(3)
    sys.exit()
   

#if the shutil library is not installed, install it via pip
try:
    import shutil
except ImportError:
    print("[!] The shutil library is not installed. Installing...")
    os.system("pip install shutil")
    print("[+] The shutil library has been installed.")
    #tell the user to please restart the program
    print("Please restart the program")
    time.sleep(3)
    sys.exit()

OUI_list = [] 
OUI_list_final = []
company_list =[]
company_list_final = []
vlan_list = []
vlan_list_final = []
word_list = []

#Get the current working directory and store it in a variable called "cwd"
cwd = os.getcwd()

#Show the contents of the current directory
print("\nPlease select the [italic green]ARP[/italic green] or [italic green]MAC[/italic green] Data text file from [cyan]"+cwd+"[/cyan] \n")
print(os.listdir(), "\n")

#while the file name is not valid, ask the user to input the file name again
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

#compare each element to the previous element, if the element is different, save the element
for i in range(len(OUI_list)):
    if OUI_list[i] != OUI_list[i-1]:
        #save each different element to a new list called OUI_list_final
        OUI_list_final.append(OUI_list[i])

#save oui list final to a file called oui_list_final.txt
with open('oui_list_final.txt', 'w') as f:
    for i in range(len(OUI_list_final)):
        f.write(OUI_list_final[i][0] + '\n')

#close the file
f.close()

#Check each line of the file oui_list_final.txt if it is 'MAC' delete it
with open('oui_list_final.txt', 'r') as f:
    lines = f.readlines()
with open('oui_list_final.txt', 'w') as f:
    for line in lines:
        if line.strip("\n") != 'MAC':
            f.write(line)
#close the file
f.close()

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
    r = requests.get("https://macvendors.co/api/vendorname/" + vendor_list[i])
    time.sleep(0.1)
    #if the request is successful, print the vendor name
    if r.status_code == 200:
        #save the vendor name to a file called vendor_list.txt
        with open('oui_name_result.txt', 'a') as f:
            f.write(r.text + '\n')
    #else if the request is not successful, print the error message
    else:
        print("\nError:", r.status_code, r.reason)

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

#compare each element to the previous element, if the element is different, print the element
for i in range(len(company_list)):
    if company_list[i] != company_list[i-1]:
        #save each different element to a new list called company_list_final
        company_list_final.append(company_list[i])

print("\n\nThe companies seen in the [italic green]"+ ip_arp_file + "[/italic green] data file are:\n")

#save the company list final to a file called company_list.txt
with open('company_list.txt', 'w') as f:
    for i in range(len(company_list_final)):
        f.write(company_list_final[i])

#print the list company_list one element a t time
for i in range(len(company_list_final)):
    #remove the new line character from the end of the line
    company_list_final[i] = company_list_final[i].rstrip()
    #print the element in cyan
    print("[cyan]" + company_list_final[i] + "[/cyan]")

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
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f, colour="cyan"):
       #split the line into words
        words = line.split()
        #if words[mac_word] starts with Apple OUI add it to the Apple-Devices.txt file 
        if words[mac_word].startswith("0c4d.e9") or words[mac_word].startswith("109a.dd") or words[mac_word].startswith("10dd.b1") or words[mac_word].startswith("28ff.3c") or words[mac_word].startswith("38c9.86") or words[mac_word].startswith("3c7d.0a") or words[mac_word].startswith("501f.c6")or words[mac_word].startswith("685b.35") or words[mac_word].startswith("7cd1.c")or words[mac_word].startswith("8866.5a") or words[mac_word].startswith("9c20.7b") or words[mac_word].startswith("a860.b6") or words[mac_word].startswith("d081.7a") or words[mac_word].startswith("cc29.f5"):
            with open('Apple-Devices.txt', 'a') as f:
                f.write(line)
                time.sleep(0.1)
#close the files
f.close()

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

#For every line in the file check the MAC address, if it is a Dell Address, add it the Dell-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f, colour="cyan"):
       #split the line into words
        words = line.split()
        #if words[mac_word] starts with a Dell OUI add the line to the Dell-Devices.txt file 
        if words[mac_word].startswith("001a.a0") or words[mac_word].startswith("004e.01") or words[mac_word].startswith("14b3.1f") or words[mac_word].startswith("14fe.b5") or words[mac_word].startswith("1866.da") or words[mac_word].startswith("28f1.0e") or words[mac_word].startswith("484d.7e")or words[mac_word].startswith("509a.4c") or words[mac_word].startswith("5448.10")or words[mac_word].startswith("54bf.64") or words[mac_word].startswith("6400.6a") or words[mac_word].startswith("6c2b.59") or words[mac_word].startswith("782b.cb") or words[mac_word].startswith("8cec.4b") or words[mac_word].startswith("a41f.72") or words[mac_word].startswith("a4bb.6d") or words[mac_word].startswith("b083.fe") or words[mac_word].startswith("b885.84") or words[mac_word].startswith("b8ca.3a") or words[mac_word].startswith("bc30.5b") or words[mac_word].startswith("c81f.66") or words[mac_word].startswith("d4be.d9") or words[mac_word].startswith("d89e.f3") or words[mac_word].startswith("e454.e8") or words[mac_word].startswith("e4f0.04") or words[mac_word].startswith("f04d.a2") or words[mac_word].startswith("f402.70") or words[mac_word].startswith("f48e.38") or words[mac_word].startswith("f8bc.12") or words[mac_word].startswith("0006.5b") or words[mac_word].startswith("0008.74") or words[mac_word].startswith("000b.db") or words[mac_word].startswith("000d.56") or words[mac_word].startswith("000f.1f") or words[mac_word].startswith("0011.43")  or words[mac_word].startswith("0012.3f") or words[mac_word].startswith("0013.72") or words[mac_word].startswith("0014.22") or words[mac_word].startswith("0015.c5") or words[mac_word].startswith("0016.f0") or words[mac_word].startswith("0018.8b") or words[mac_word].startswith("0019.b9") or words[mac_word].startswith("01c2.3") or words[mac_word].startswith("001d.09") or words[mac_word].startswith("001e.4f")  or words[mac_word].startswith("001e.c9") or words[mac_word].startswith("0021.70") or words[mac_word].startswith("0021.9b") or words[mac_word].startswith("0022.19")  or words[mac_word].startswith("0023.ae") or words[mac_word].startswith("0024.e8") or words[mac_word].startswith("0025.64") or words[mac_word].startswith("0026.b9") or words[mac_word].startswith("00b0.d0") or words[mac_word].startswith("00be.43") or words[mac_word].startswith("00c0.4f") or words[mac_word].startswith("0892.04") or words[mac_word].startswith("0c29.ef") or words[mac_word].startswith("1065.30") or words[mac_word].startswith("107d.1a") or words[mac_word].startswith("1098.36") or words[mac_word].startswith("1418.77") or words[mac_word].startswith("149e.cf") or words[mac_word].startswith("1803.73") or words[mac_word].startswith("185a.58") or words[mac_word].startswith("18a9.9b") or words[mac_word].startswith("18db.f2") or words[mac_word].startswith("18fb.7b") or words[mac_word].startswith("1c40.24") or words[mac_word].startswith("1c72.1d")  or words[mac_word].startswith("2004.0f") or words[mac_word].startswith("246e.96") or words[mac_word].startswith("2471.52") or words[mac_word].startswith("24b6.fd") or words[mac_word].startswith("2cea.7f") or words[mac_word].startswith("30d0.42") or words[mac_word].startswith("3417.eb") or words[mac_word].startswith("448e.db") or words[mac_word].startswith("3473.5a") or words[mac_word].startswith("18db.f2") or words[mac_word].startswith("18fb.7b") or words[mac_word].startswith("1c40.24") or words[mac_word].startswith("1c72.1d") or words[mac_word].startswith("2004.0f") or words[mac_word].startswith("2047.47") or words[mac_word].startswith("246e.96") or words[mac_word].startswith("2471.52") or words[mac_word].startswith("24b6.fd") or words[mac_word].startswith("2cea.7f") or words[mac_word].startswith("30d0.42") or words[mac_word].startswith("3417.eb")  :
            with open('Dell-Devices.txt', 'a') as f:
                f.write(line)
                time.sleep(0.1)
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

#For every line in the file check the MAC address, if it is an Cisco-Meraki Address, add it the Cisco-Meraki-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f,colour='cyan'):
       #split the line into words
        words = line.split()
        #if words[mac_word] starts with a Cisco-Meraki OUI add the line to the Cisco-Meraki-Devices.txt file 
        if words[mac_word].startswith("ac17.c8") or words[mac_word].startswith("f89e.28"):
            with open('Cisco-Meraki-Devices.txt', 'a') as f:
                f.write(line)
                time.sleep(0.1)
#close the files
f.close()

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

#For every line in the file check the MAC address, if it is an Other-Cisco Address, add it the Other-Cisco-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f, colour='cyan'):
       #split the line into words
        words = line.split()
        #if words[mac_word] starts with a Other-Cisco OUI add the line to the Other-Cisco-Devices.txt file 
        if words[mac_word].startswith("0007.7d") or words[mac_word].startswith("0008.2f") or words[mac_word].startswith("0021.a0") or words[mac_word].startswith("0022.bd") or words[mac_word].startswith("0023.5e") or words[mac_word].startswith("003a.99") or words[mac_word].startswith("005f.86") or words[mac_word].startswith("00aa.6e") or words[mac_word].startswith("0cf5.a4") or words[mac_word].startswith("1833.9d") or words[mac_word].startswith("1ce8.5d") or words[mac_word].startswith("30e4.db") or words[mac_word].startswith("40f4.ec") or words[mac_word].startswith("4403.a7") or words[mac_word].startswith("4c4e.35") or words[mac_word].startswith("544a.00") or words[mac_word].startswith("5486.bc") or words[mac_word].startswith("588d.09") or words[mac_word].startswith("58bf.ea") or words[mac_word].startswith("6400.f1") or words[mac_word].startswith("7c21.0d") or words[mac_word].startswith("84b5.17") or words[mac_word].startswith("8cb6.4f") or words[mac_word].startswith("ac17.c8") or words[mac_word].startswith("ac7e.8a") or words[mac_word].startswith("bc67.1c") or words[mac_word].startswith("c4b3.6a") or words[mac_word].startswith("d4ad.71") or words[mac_word].startswith("e0d1.73") or words[mac_word].startswith("e8b7.48") or words[mac_word].startswith("f09e.63") or words[mac_word].startswith("f866.f2") or words[mac_word].startswith("0025.45") or words[mac_word].startswith("002a.6a") :
            with open('Other-Cisco-Devices.txt', 'a') as f:
                f.write(line)
                time.sleep(0.1)
#close the files
f.close()

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

#For every line in the file check the MAC address, if it is an Mitel Address, add it the Mitel-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f, colour='cyan'):
       #split the line into words
        words = line.split()
        #if words[mac_word] starts with a Mitel OUI add the line to the Mitel-Devices.txt file 
        if words[mac_word].startswith("0800.0f") :
            with open('Mitel-Devices.txt', 'a') as f:
                f.write(line)
                time.sleep(0.1)
#close the files
f.close()

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

#For every line in the file check the MAC address, if it is an HP OUI Address, add it the HP-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f, colour='cyan'):
       #split the line into words
        words = line.split()
        #if words[mac_word] starts with a HP OUI add the line to the HP-Devices.txt file 
        if words[mac_word].startswith("0017.a4") or words[mac_word].startswith("001b.78") or words[mac_word].startswith("0023.7d") or words[mac_word].startswith("0030.6e") or words[mac_word].startswith("009c.02") or words[mac_word].startswith("1062.e5") or words[mac_word].startswith("3024.a9") or words[mac_word].startswith("308d.99") or words[mac_word].startswith("30e1.71") or words[mac_word].startswith("3822.e2") or words[mac_word].startswith("38ea.a7") or words[mac_word].startswith("40b0.34") or words[mac_word].startswith("68b5.99") or words[mac_word].startswith("6cc2.17") or words[mac_word].startswith("80ce.62") or words[mac_word].startswith("80e8.2c") or words[mac_word].startswith("8434.97") or words[mac_word].startswith("98e7.f4") or words[mac_word].startswith("9cb6.54") or words[mac_word].startswith("a08c.fd") or words[mac_word].startswith("a0d3.c1") or words[mac_word].startswith("a45d.36") or words[mac_word].startswith("b00c.d1") or words[mac_word].startswith("e4e7.49") or words[mac_word].startswith("ec8e.b5") or words[mac_word].startswith("f092.1c") or words[mac_word].startswith("f430.b9") or words[mac_word].startswith("fc15.b4") :
            with open('HP-Devices.txt', 'a') as f:
                f.write(line)
                time.sleep(0.1)
#close the files
f.close()

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

#compare each element to the previous element, if the element is different, save the element
for i in range(len(vlan_list)):
    if vlan_list[i] != vlan_list[i-1]:
        #save each different element to a new list called vlan_list_final
        vlan_list_final.append(vlan_list[i])

#save oui list final to a file called vlan_list_final.txt
with open('vlan_list.txt', 'w') as f:
    for i in range(len(vlan_list_final)):
        f.write(vlan_list_final[i][0] + '\n')

#close the files
f.close()

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
    

#count the lines in the file oui_list_final.txt and print the number of lines
with open('company_list.txt', 'r') as f:
    count = 0
    for line in f:
        count += 1
    print ("[bold yellow]++[/bold yellow] [bright_red]" + str(count) + "[/bright_red] [cyan]companies[/cyan]")
    f.close()
    
#count the lines in the file oui_list_final.txt and print the number of lines
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

    #move the csv file to the csv_files folder
    shutil.move(csv_file, 'csv_files')

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
    print("\n[bold yellow]##[/bold yellow] See the [cyan]csv_files[/cyan] folder for the csv files")
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
        shutil.move(file, 'text_files')
    else:
        pass

#close any remainng files
f.close()

#tell the user to press enter to quit
input("\nPress enter to quit: ")
time.sleep(3)
#exit the program
sys.exit()
