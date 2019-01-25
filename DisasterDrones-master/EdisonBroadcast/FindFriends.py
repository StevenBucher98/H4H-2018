import os
from sys import stdout
import sys
import time
import re
import subprocess
import socket

STATE_DIR = '/var/lib/edison_config_tools'

def list_networks():
    os.popen("systemctl stop hostapd").close()
    time.sleep(2)
    os.popen("systemctl start wpa_supplicant").close()
    print("Stoped hostapd and started wpa supplicant")
    time.sleep(5)
    os.popen("wpa_cli scan").close()
    time.sleep(5)
    pipe = os.popen("wpa_cli scan_results")
    found = [l.split("\t") for l in pipe.read().split("\n")]
    pipe.close()
    networks = {}

    found_open = []

    WPAPSK_REGEX=re.compile(r'\[WPA[2]?-PSK-.+\]')
    WPAEAP_REGEX=re.compile(r'\[WPA[2]?-EAP-.+\]')
    WEP_REGEX=re.compile(r'\[WEP.*\]')

    for n in found:
        if (len(n) == 5):
            ssid = n[-1]
        else:
            continue
        if ssid not in networks and not ssid == "" and "\\x00" not in ssid:
            flags = n[-2]
            networks[ssid] = {
                'mac': n[0]
            }
            if WPAPSK_REGEX.search(flags):
                networks[ssid]["sec"] = "WPA-PSK"
            elif WPAEAP_REGEX.search(flags):
                networks[ssid]["sec"] = "WPA-EAP"
            elif WEP_REGEX.search(flags):
                networks[ssid]["sec"] = "WEP"
            else:
                networks[ssid]["sec"] = "OPEN"
    
    return networks

def connect_wifi(ssid):
    if not os.path.isfile('/etc/wpa_supplicant/wpa_supplicant.conf.original'):
        subprocess.call("cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.original", shell=True)

    wpa_supplicant = open('/etc/wpa_supplicant/wpa_supplicant.conf','w') #Will not take care of duplicates at the moment.
    header = """
ctrl_interface=/var/run/wpa_supplicant
ctrl_interface_group=0
config_methods=virtual_push_button virtual_display push_button keypad
update_config=1
fast_reauth=1
device_name=Edison
manufacturer=Intel
model_name=Edison
"""
    wpa_supplicant.write(header)
    wpa_supplicant.write('''
network={{
  ssid="{0}"
  {1}
  key_mgmt=NONE
}}
'''.format(ssid, ""))
    wpa_supplicant.close()

    print("Updated supplicant file")

    try:
        if int(subprocess.check_output("systemctl status wpa_supplicant | grep 'active (running)' | wc -l", shell=True)) == 0:
            subprocess.call("systemctl stop hostapd &> /dev/null", shell=True)
            subprocess.call("systemctl start wpa_supplicant &> /dev/null", shell=True)
            time.sleep(10)
        else:
            subprocess.call("wpa_cli reconfigure &> /dev/null && sleep 2", shell=True)

        print("Completed reconfigure")

        network_count = int(subprocess.check_output('wpa_cli list_networks | wc -l', shell=True))
        subprocess.call("wpa_cli select_network " + str(network_count - 2 - 1) + " &> /dev/null", shell=True)
        time.sleep(5)

        print("Selected")

        ifarray = subprocess.check_output("wpa_cli ifname", shell=True).split()
        subprocess.call("udhcpc -i " + str(ifarray[len(ifarray)-1]) + " -n &> /dev/null", shell=True)
    except Exception as e:
        print(e)
        print("Sorry. Could not get an IP address.")

    time.sleep(1)

    pipe = os.popen("iwgetid -r")
    ssid = pipe.read().rstrip()
    pipe.close()
    return ssid

def get_current_config():
    pipe = os.popen("iwgetid -r")
    ssid = pipe.read().rstrip()
    pipe.close()

    conf = {}
    cssid = None

    line = ""

    wpa_supplicant = open('/etc/wpa_supplicant/wpa_supplicant.conf','r')
    line = wpa_supplicant.readline()
    while line != "":
        if "network" in line and "{" in line:
            while "}" not in line:
                if "ssid" in line:
                    bits = line.split('"')
                    cssid = bits[1]
                if "wep_key0" in line or "psk" in line or "password" in line:
                    bits = line.split('"')
                    conf["password"] = bits[1]
                    if "wep_key0" in line:
                        conf["sec"] = "WEP"
                    elif "psk" in line:
                        conf["sec"] = "WPA-PSK"
                    elif "password" in line:
                        conf["sec"] = "WPA-EAP"
                elif "identity" in line:
                    bits = line.split('"')
                    conf["user"] = bits[1]
                line = wpa_supplicant.readline()
            if cssid == ssid:
                if "password" not in conf:
                    conf["sec"] = "OPEN"
                conf["ssid"] = ssid
                wpa_supplicant.close()
                return conf
        line = wpa_supplicant.readline()
    wpa_supplicant.close()
    return None
    

# hack4humanity OPEN
# NiceMeme.jpg WPA-PSK datboi12345!!
# dd-wrt WPA-PSK c242wifi
# c242-router-1

n = sys.argv[1]

if len(sys.argv) > 2:
    new_address = connect_wifi(n)
    print("addr:", new_address)
    sys.exit(0)
    
# sec = sys.argv[3]
# passwd = sys.argv[2]

old_network = get_current_config()

networks = {}

while n not in networks:
    networks = list_networks()

if networks[n]["sec"] != "OPEN":
    print("Only open wifi networks can be hot swapped")
    sys.exit(1)

print("network found, swapping")
new_address = connect_wifi(n)
print("Networks swapped, data will be pushed")
print("new ssid:", new_address)

broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

broadcast.sendto(
    b"Req Dump",
    ('255.255.255.255',(242*106)^(1337))
)

com = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
com.bind(('',(242*106)^(1337)))

data = com.recvfrom(1024)
while data[0].decode('ascii')[0] != "~":
    data = com.recvfrom(1024)
    
com.close()

print("Got dump:", data[0].decode('ascii'))

recv_data = open('data_file.dat','r')

broadcast.sendto(
    b"~" + str.encode(''.join(recv_data.readlines())),
    (data[1][0],(242*106)^(1337))
)

recv_data.close()

recv_data = open('data_file.dat','a+')

recv_data.write(data[0].decode('ascii') + '\n')

recv_data.close()
broadcast.close()

print(old_network)
new_address = connect_wifi(old_network["ssid"])
print("Network back")
print("returned ssid:", new_address)