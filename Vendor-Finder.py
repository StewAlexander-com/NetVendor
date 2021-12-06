#!/usr/bin/env python3
import os
import sys
import csv
import time
import subprocess
import json

#if the library requests is not installed, install it via pip
try:
    import requests
except ImportError:
    print("[!] The requests library is not installed. Installing...")
    os.system("pip install requests")
    print("[+] The requests library has been installed.")
    time.sleep(1)
    import requests

# if the library requests is not installed, install it via pip
try:
    import tqdm
except ImportError:
    print("[!] The requests library is not installed. Installing...")
    os.system("pip install tqdm")
    print("[+] The requests library has been installed.")
    time.sleep(1)
    import tqdm 

from tqdm import tqdm

OUI_list = [] 
OUI_list_final = []
company_list =[]
company_list_final = []

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

#compare each element to the previous element, if the element is different, print the element
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
        #save each different element to a new list called OUI_list_final
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

# count the lines in the file oui_list_final.txt and print the number of lines
with open('oui_list_final.txt', 'r') as f:
    count = 0
    for line in f:
        count += 1
    print("\n\n++ There are", count, "different OUIs in the", ip_arp_file, "file")

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

print("\n>>> Please see the oui_list_final.txt file in the current directory for the list of OUIs\n")
print(">>> Please see the company_list.txt file in the current directory for the list of companies seen\n")
print ("# The number of Apple devices in the", ip_arp_file, "file is", Apple_count)
print ("# The number of Dell devices in the", ip_arp_file, "file is", Dell_count)

if os.path.exists('Apple-Devices.txt'):
    print("\n >>> Please see the Apple-Devices.txt file in the current directory for the list of Apple devices\n")
else:
    pass

if os.path.exists('Dell-Devices.txt'):
    print(">>> Please see the Dell-Devices.txt file in the current directory for the list of Dell devices\n")
else:
    pass

#tell the user to press enter to quit
input("\nPress enter to quit: ")
#exit the program
sys.exit()





        