#!/usr/bin/env python3
import os
import sys
import csv
import time
import subprocess
import json

try :
    import plotly
    import plotly.graph_objs as go
except ImportError:
    print("[!] Plotly library not installed, Installing...")
    os.system("pip3 install plotly")
    time.sleep(30)
    import plotly
    import plotly.graph_objs as go

#if the library requests is not installed, install it via pip
try:
    import requests
except ImportError:
    print("[!] The requests library is not installed. Installing...")
    os.system("pip install requests")
    print("[+] The requests library has been installed.")
    time.sleep(1)
    import requests

# if the library tqdm is not installed, install it via pip  -- future development
# try:
#     import tqdm
# except ImportError:
#     print("[!] The requests library is not installed. Installing...")
#     os.system("pip install tqdm")
#     print("[+] The requests library has been installed.")
#     time.sleep(1)
#     import tqdm 
# 
# from tqdm import tqdm

OUI_list = [] 
OUI_list_final = []
company_list =[]
company_list_final = []
vlan_list = []
vlan_list_final = []

#Show the contents of the current directory
print("\nPlease select the #SH IP ARP Data text file from the current directory\n")
print(os.listdir(), "\n")

#while the file name is not valid, ask the user to input the file name again
while True:
    ip_arp_file = input("Please enter the file name: ")
    if os.path.isfile(ip_arp_file):
        break
    else:
        print("\nThe file name is not valid, please try again\n")

with open(ip_arp_file, 'r') as f:
        for line in f:
            #split the line into words
            words = line.split()
            #send words[2] to a list
            MAC_Element = words[2]
            #copy the first 7 characters to a new list called OUI_list
            OUI_ELEMENT= MAC_Element[0:7]
            #split oui_list into different elements
            OUI_ELEMENT = OUI_ELEMENT.split()
            #append OUI_ELEMENT to a list called OUI_list
            OUI_list.append(OUI_ELEMENT)

#sort OUI_list
OUI_list.sort()

def loads(txt):
    txt = txt.encode("utf-8")
    value = json.loads(txt)

    return value

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
print("\nPlease be patient, the vendor information is being retrieved\n")

#for each line in the file oui_list_final.txt, store this in a list called vendor_list
vendor_list = []
with open('oui_list_final.txt', 'r') as f:
    for line in f:
        vendor_list.append(line)

#for each element in vendor_list do a request to the OUI database
for i in range(len(vendor_list)):
    #make each element uppercase
    vendor_list[i] = vendor_list[i].upper()
    r = requests.get("https://macvendors.co/api/" + vendor_list[i])
    time.sleep(0.1)
    #if the request is successful, print the vendor name
    if r.status_code == 200:
        #add the tqdm code here?
        print(".", end="")
        #save the vendor name to a file called vendor_list.txt
        with open('raw_vendor_list.json', 'a') as f:
            f.write(r.text + '\n')
    #else if the request is not successful, print the error message
    else:
        print("\nError:", r.status_code, r.reason)

#close the file
f.close()

#Check each line of the file vendor_list.txt if it is "{"result":{"error":"no result"}}" delete it

with open('raw_vendor_list.json', 'r') as f:
    lines = f.readlines()
with open('raw_vendor_list.json', 'w') as f:
  for line in lines:
      if line.strip("\n") != '{\"result\":{\"error\":\"no result\"}}':
          f.write(line)

#close the file
f.close()

time.sleep(1)

#open the json file raw_vendor_list.json and read it, look for company name
with open('raw_vendor_list.json', 'r') as f:
    for line in f:
        #load the json file
        data = loads(line)
        #get the company name
        company = data['result']['company']
        #append the company name to a list called company_list
        company_list.append(company)

#close the file
f.close()

#sort company_list
company_list.sort()

#compare each element to the previous element, if the element is different, print the element
for i in range(len(company_list)):
    if company_list[i] != company_list[i-1]:
        #save each different element to a new list called vlan_list_final
        company_list_final.append(company_list[i])

print("\n\nThe companies seen in the <<# sh ip arp>> data file are:\n")

#save the company list final to a file called company_list.txt
with open('company_list.txt', 'w') as f:
    for i in range(len(company_list_final)):
        f.write(company_list_final[i] + '\n')

#print the list company_list one element a t time
for i in range(len(company_list_final)):
    print(company_list_final[i])

#Collecting the output of the command sh ip arp
print ("\n\nPlease be patient, while information is being retrieved\n")

#######################################################################################

#Finding all the Apple ARP Entries ....

#Delete the file Apple-Devices.txt if it exists
if os.path.exists('Apple-Devices.txt'):
    os.remove('Apple-Devices.txt')
else :
    pass

#For every line in the file check the MAC address, if it is an Apple Address, add it the Apple-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in f:
        print(".", end="")
       #split the line into words
        words = line.split()
        #if words[2] starts with Apple OUI add it to the Apple-Devices.txt file 
        if words[2].startswith("0c4d.e9") or words[2].startswith("109a.dd") or words[2].startswith("10dd.b1") or words[2].startswith("28ff.3c") or words[2].startswith("38c9.86") or words[2].startswith("3c7d.0a") or words[2].startswith("501f.c6")or words[2].startswith("685b.35") or words[2].startswith("7cd1.c")or words[2].startswith("8866.5a") or words[2].startswith("9c20.7b") or words[2].startswith("a860.b6") or words[2].startswith("d081.7a"):
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

#For every line in the file check the MAC address, if it is an Dell Address, add it the Dell-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in f:
        print (".", end="")
       #split the line into words
        words = line.split()
        #if words[2] starts with a Dell OUI add the line to the Dell-Devices.txt file 
        if words[2].startswith("001a.a0") or words[2].startswith("004e.01") or words[2].startswith("14b3.1f") or words[2].startswith("14fe.b5") or words[2].startswith("1866.da") or words[2].startswith("28f1.0e") or words[2].startswith("484d.7e")or words[2].startswith("509a.4c") or words[2].startswith("5448.10")or words[2].startswith("54bf.64") or words[2].startswith("6400.6a") or words[2].startswith("6c2b.59") or words[2].startswith("782b.cb") or words[2].startswith("8cec.4b") or words[2].startswith("a41f.72") or words[2].startswith("a4bb.6d") or words[2].startswith("b083.fe") or words[2].startswith("b885.84") or words[2].startswith("b8ca.3a") or words[2].startswith("bc30.5b") or words[2].startswith("c81f.66") or words[2].startswith("d4be.d9") or words[2].startswith("d89e.f3") or words[2].startswith("e454.e8") or words[2].startswith("e4f0.04") or words[2].startswith("f04d.a2") or words[2].startswith("f402.70") or words[2].startswith("f48e.38") or words[2].startswith("f8bc.12"):
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

#For every line in the file check the MAC address, if it is an Cisco-Meraki Address, add it the Cisco-Meraki-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in f:
        print (".", end="")
       #split the line into words
        words = line.split()
        #if words[2] starts with a Cisco-Meraki OUI add the line to the Cisco-Meraki-Devices.txt file 
        if words[2].startswith("ac17.c8") or words[2].startswith("f89e.28"):
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

#For every line in the file check the MAC address, if it is an Other-Cisco Address, add it the Other-Cisco-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in f:
        print (".", end="")
       #split the line into words
        words = line.split()
        #if words[2] starts with a Other-Cisco OUI add the line to the Other-Cisco-Devices.txt file 
        if words[2].startswith("0007.7d") or words[2].startswith("0008.2f") or words[2].startswith("0021.a0") or words[2].startswith("0022.bd") or words[2].startswith("0023.5e") or words[2].startswith("003a.99") or words[2].startswith("005f.86") or words[2].startswith("00aa.6e") or words[2].startswith("0cf5.a4") or words[2].startswith("1833.9d") or words[2].startswith("1ce8.5d") or words[2].startswith("30e4.db") or words[2].startswith("40f4.ec") or words[2].startswith("4403.a7") or words[2].startswith("4c4e.35") or words[2].startswith("544a.00") or words[2].startswith("5486.bc") or words[2].startswith("588d.09") or words[2].startswith("58bf.ea") or words[2].startswith("6400.f1") or words[2].startswith("7c21.0d") or words[2].startswith("84b5.17") or words[2].startswith("8cb6.4f") or words[2].startswith("ac17.c8") or words[2].startswith("ac7e.8a") or words[2].startswith("bc67.1c") or words[2].startswith("c4b3.6a") or words[2].startswith("d4ad.71") or words[2].startswith("e0d1.73") or words[2].startswith("e8b7.48") or words[2].startswith("f09e.63") or words[2].startswith("f866.f2"):
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
# Find all the unique vlans in the ip_arp_file

with open(ip_arp_file, 'r') as f:
        for line in f:
            #split the line into words
            vlanwords = line.split()
            #send words[3] to a list
            vlan_Element = vlanwords[3]
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
    print("\n\n++ There are", vlan_count, "different vlans in the", ip_arp_file, "file")

#######################################################################################

# count the lines in the file oui_list_final.txt and print the number of lines
with open('oui_list_final.txt', 'r') as f:
    OUI_count = 0
    for line in f:
        OUI_count += 1
    print("++ There are", OUI_count, "different OUIs in the", ip_arp_file, "file")

#count the lines in the file oui_list_final.txt and print the number of lines
with open('company_list.txt', 'r') as f:
    count = 0
    for line in f:
        count += 1
    print("++ There are", count, "different vendors in the", ip_arp_file, "file")

#count the lines in the file oui_list_final.txt and print the number of lines
with open( ip_arp_file, 'r') as f:
    count = 0
    for line in f:
        count += 1
    print("++ There are a total of", count-1, "devices in the", ip_arp_file, "file\n")
    arpcount = count-1

OtherTotal = arpcount - (Apple_count + Dell_count + CiscoMeraki_count + OtherCisco_count)

#######################################################################################


print(">>> Please see the oui_list_final.txt file in the current directory for the list of OUIs")
print(">>> Please see the company_list.txt file in the current directory for the list of companies seen in the", ip_arp_file, "file")
print(">>> Please see the vlan_list.txt file in the current directory for the list of VLANs seen in the", ip_arp_file, "file")
print("\n")
print ("# The number of Apple devices in the", ip_arp_file, "file is", Apple_count)
print ("# The number of Dell devices in the", ip_arp_file, "file is", Dell_count)
print ("# The number of Cisco-Meraki devices in the", ip_arp_file, "file is", CiscoMeraki_count)
print ("# The number of other Cisco devices in the", ip_arp_file, "file is", OtherCisco_count)
print ("# The number of other devices in the", ip_arp_file, "file is", OtherTotal)
print("\n")

#######################################################################################

#Plotting the Apple, Dell, Cisco-Meraki, Other Cisco, and Other devices

labels = ['Apple', 'Dell', 'Cisco-Meraki', 'Other Cisco', 'Other']
values = [Apple_count, Dell_count, CiscoMeraki_count, OtherCisco_count, OtherTotal]

#check if Google Chrome or Firefox or is installed on Windows
if os.path.exists('C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe') or os.path.exists('C:\\Program Files\\Google\\Chrome\\Application\\Firefox.exe'):
    fig =go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.show()
elif os.name == 'Linux':
    #check if Google Chrome or Firefox is installed on Linux
    if os.path.exists('/usr/bin/google-chrome') or os.path.exists('/usr/bin/firefox'):
        fig =go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.show()
    else :
        pass
else:
    pass   

#######################################################################################


if os.path.exists('Apple-Devices.txt'):
    print(">>> Please see the Apple-Devices.txt file in the current directory for the list of Apple devices")
else:
    pass

if os.path.exists('Dell-Devices.txt'):
    print(">>> Please see the Dell-Devices.txt file in the current directory for the list of Dell devices")
else:
    pass

if os.path.exists('Cisco-Meraki-Devices.txt'):
    print(">>> Please see the Cisco-Meraki-Devices.txt file in the current directory for the list of Cisco-Meraki devices")
else:
    pass

if os.path.exists('Other-Cisco-Devices.txt'):
    print(">>> Please see the Other-Cisco-Devices.txt file in the current directory for the list of Other Cisco devices")
else:
    pass


#tell the user to press enter to quit
input("\nPress enter to quit: ")
time.sleep(3)
#exit the program
sys.exit()





        