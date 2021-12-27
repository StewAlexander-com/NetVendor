#!/usr/bin/env python3
import os
import sys
import csv
import time
import subprocess
import json

#check if the tqdm module exists, if not install it
try :
    from tqdm import tqdm
except ImportError:
    subprocess.call([sys.executable, "-m", "pip", "install", "tqdm"])
    time.sleep(10)
    from tqdm import tqdm

#check if the plotly module exists, if not install it
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

OUI_list = [] 
OUI_list_final = []
company_list =[]
company_list_final = []
vlan_list = []
vlan_list_final = []

#Show the contents of the current directory
print("\nPlease select the ARP or MAC Data text file from the current directory\n")
print(os.listdir(), "\n")

#while the file name is not valid, ask the user to input the file name again
while True:
    ip_arp_file = input("Please enter the file name: ")
    if os.path.isfile(ip_arp_file):
        break
    else:
        print("\nThe file name is not valid, please try again\n")

#Ask the user to input which word containts the MAC_Element
mac_temp = input("\nPlease enter the column in the file that contains the MAC Addresses: ")

#convert the input to an int and subtract 1 to match the column number
mac_column = int(mac_temp)
mac_word = mac_column - 1

#Ask the user to input which word containts the VLAN_Element
vlan_temp = input("\nPlease enter the column in the file that contains the VLANs: ")

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
for i in tqdm (range(len(vendor_list))):
    #make each element uppercase
    vendor_list[i] = vendor_list[i].upper()
    r = requests.get("https://macvendors.co/api/" + vendor_list[i])
    time.sleep(0.1)
    #if the request is successful, print the vendor name
    if r.status_code == 200:
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

print("\n\nThe companies seen in the "+ ip_arp_file + " data file are:\n")

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

print ("\nFinding any Apple devices in the " + ip_arp_file + " file....")
#For every line in the file check the MAC address, if it is an Apple Address, add it the Apple-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f):
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

print ("\nFinding any Dell devices in the " + ip_arp_file + " file....")

#For every line in the file check the MAC address, if it is an Dell Address, add it the Dell-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f):
       #split the line into words
        words = line.split()
        #if words[mac_word] starts with a Dell OUI add the line to the Dell-Devices.txt file 
        if words[mac_word].startswith("001a.a0") or words[mac_word].startswith("004e.01") or words[mac_word].startswith("14b3.1f") or words[mac_word].startswith("14fe.b5") or words[mac_word].startswith("1866.da") or words[mac_word].startswith("28f1.0e") or words[mac_word].startswith("484d.7e")or words[mac_word].startswith("509a.4c") or words[mac_word].startswith("5448.10")or words[mac_word].startswith("54bf.64") or words[mac_word].startswith("6400.6a") or words[mac_word].startswith("6c2b.59") or words[mac_word].startswith("782b.cb") or words[mac_word].startswith("8cec.4b") or words[mac_word].startswith("a41f.72") or words[mac_word].startswith("a4bb.6d") or words[mac_word].startswith("b083.fe") or words[mac_word].startswith("b885.84") or words[mac_word].startswith("b8ca.3a") or words[mac_word].startswith("bc30.5b") or words[mac_word].startswith("c81f.66") or words[mac_word].startswith("d4be.d9") or words[mac_word].startswith("d89e.f3") or words[mac_word].startswith("e454.e8") or words[mac_word].startswith("e4f0.04") or words[mac_word].startswith("f04d.a2") or words[mac_word].startswith("f402.70") or words[mac_word].startswith("f48e.38") or words[mac_word].startswith("f8bc.12") or words[mac_word].startswith("a44c.c8"):
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

print ("\nFinding any Cisco Meraki devices in the " + ip_arp_file + " file....")

#For every line in the file check the MAC address, if it is an Cisco-Meraki Address, add it the Cisco-Meraki-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f):
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

print ("\nFinding any other Cisco devices in the " + ip_arp_file + " file....")

#For every line in the file check the MAC address, if it is an Other-Cisco Address, add it the Other-Cisco-Devices.txt
with open(ip_arp_file, 'r') as f:
    for line in tqdm(f):
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
# Find all the unique vlans in the ip_arp_file

with open(ip_arp_file, 'r') as f:
        for line in f:
            #split the line into words
            vlanwords = line.split()
            #send words[3] to a list
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
elif os.path.exists('/usr/bin/google-chrome') or os.path.exists('/usr/bin/firefox'):
    fig =go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.show()   
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
