from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.Progr.SSH import SSH, ArpStatus
from Diamon2.Progr.Net import NetDevice
import re
import json

class OpenWRTCD(ControlDevice):
    def __init__(self, ip_address, login, password, port):
        super().__init__(locals().copy())
        self.ip_address = ip_address
        self.login = login
        self.password = password
        self.port = port
        self.client = SSH()
        self.client.connect(self.ip_address, port, login, password)
        self.mac_address = self.client._exec_ssh_cmd("ifconfig | grep br-lan | awk '{ print $5 }'").upper().replace('.',':')
        self.device_type = DeviceType.Router
        self.manufacturer_type = ManufacturerType.OpenWRT
        self.toggle_ability(DeviceAbility.GetOnlineDevices)
        self.toggle_ability(DeviceAbility.OnlineDeviceUpdate)
        self.toggle_ability(DeviceAbility.GetServices)
        self.toggle_ability(DeviceAbility.ToggleService)
        self.toggle_ability(DeviceAbility.GetServiceStatus)
        self.toggle_ability(DeviceAbility.RestartService)
        self.led_names = {}
        for i in self.client._exec_ssh_cmd("ls /sys/class/leds").strip().split('\n'):
            max_bright = self.client._exec_ssh_cmd(f"cat /sys/class/leds/{i}/max_brightness").strip()
            if max_bright != '' and max_bright != None:
                self.led_names[i] = int(max_bright)
        if len(self.led_names) > 0:
            self.toggle_ability(DeviceAbility.GetLeds, led_names = list(self.led_names.keys()))
            self.toggle_ability(DeviceAbility.SetBrightness,min_brightness = {name:0 for name in self.led_names.keys()},max_brightness = self.led_names)
            self.toggle_ability(DeviceAbility.GetBrightness)
            self.toggle_ability(DeviceAbility.GetColor)
    def online_device_update(self, target_ip_address, port = 11511):
        if not target_ip_address:
            return
        ip_addresses = self.client._exec_ssh_cmd("cat /etc/config/smart_home_targets")
        targets_changed = False
        if target_ip_address not in ip_addresses:
            self.client._exec_ssh_cmd(f'echo "{target_ip_address}:{port}" >> /etc/config/smart_home_targets')
            targets_changed = True
        hotplug_devices = self.client._exec_ssh_cmd('cat /etc/hotplug.d/dhcp/00-detect_new_device.sh')
        hotplug_string = f'''#!/bin/sh\n
TARGETS=\\"/etc/config/smart_home_targets\\"
IP_ADDRESS=\\"\$IPADDR\\"
MAC_ADDRESS=\\"\$MACADDR\\"
EVENT=\\"\$ACTION\\"
HOSTNAME=\\"\$HOSTNAME\\"
[ -f \\"\$TARGETS\\" ] || exit 0
while IFS= read -r address || [ -n \\"\$address\\" ]; do
    echo \\"http://\$address/device_list?ip=\$IP_ADDRESS&mac=\$MAC_ADDRESS&event=\$EVENT&from={self.ip_address}\\"
    [ -z \\"\$address\\" ] && continue
    wget -qO- \\"http://\$address/device_list?ip=\$IP_ADDRESS&mac=\$MAC_ADDRESS&event=\$EVENT&from={self.ip_address}\\" >/dev/null 2>&1
done < \\"\$TARGETS\\"'''
        if hotplug_devices.strip() != hotplug_string.replace('\\','').strip() or targets_changed:
            self.client._exec_ssh_cmd(f'echo "{hotplug_string}" > /etc/hotplug.d/dhcp/00-detect_new_device.sh')
            self.client._exec_ssh_cmd(f'chmod +x /etc/hotplug.d/dhcp/00-detect_new_device.sh')
            self.client._exec_ssh_cmd(f'/etc/init.d/dnsmasq restart')

    def parse_dhcp(self):
        res = self.client._exec_ssh_cmd("cat /tmp/dhcp.leases")+'\n'
        pattern = re.compile(
            r'(?P<TimeStamp>\b(\d+)\b)\s+'
            r'(?P<MAC>[0-9a-fA-F:]+)\s+'
            r'(?P<IP>\b(?:\d{1,3}\.){3}\d{1,3}\b)\s+'
            r'(?P<Hostname>\S+)\s+'
            r'(?P<IPv6>\S+)\s+'
        )
        matches = pattern.finditer(res)
        result = []
        for match in matches:
            r = match.groupdict()
            result.append(r)
        return result
    def parse_arp_table(self):
        res = self.client._exec_ssh_cmd("ip neigh show")+'\n'
        pattern = re.compile(
            r'^(?P<IP>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'          # IP-адрес
            r'\s+dev\s+(?P<DEV>\S+)'                                 # <<== Добавили dev
            r'\s+lladdr\s+(?P<MAC>[0-9a-fA-F:]{17})'                 # MAC-адрес
            r'(?:\s+(?P<STATUS>REACHABLE|STALE|DELAY|PROBE|FAILED|NOARP|PERMANENT))?\b',  # Статус (опционально)
            re.MULTILINE
        )
        matches = pattern.finditer(res)
        result = []
        for match in matches:
            r = match.groupdict()
            result.append(r)
        return result
    
    def get_wireless_interfaces(self):
        result = []
        data = self.client._exec_ssh_cmd('iw dev')
        pattern = re.compile(
            r"""
            \s*Interface\s+(?P<interface>\S+)                      \s*
            \s*ifindex\s+(?P<ifindex>\d+)                          \s*
            \s*wdev\s+(?P<wdev>0x[0-9a-fA-F]+)                     \s*
            \s*addr\s+(?P<addr>(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})\s*
            \s*ssid\s+(?P<ssid>\S.*?)                              \s*
            \s*type\s+(?P<type>\S+)                                \s*
            \s*channel\s+(?P<channel>\d+)\s+\((?P<frequency>\d+)\s+MHz\),\s+
                width:\s+(?P<width>\d+)\s+MHz,\s+
                center1:\s+(?P<center1>\d+)\s+MHz                   \s*
            \s*txpower\s+(?P<txpower>[\d.]+)\s+dBm
            """,
            re.VERBOSE
        )

        for match in pattern.finditer(data):
            result.append(match.groupdict())
        return result
    
    def get_wireless_clients(self):
        result = {}
        for i in self.get_wireless_interfaces():
            clients = json.loads(self.client._exec_ssh_cmd(f'ubus call hostapd.{i["interface"]} get_clients'))['clients']
            for client in clients:
                result[client.upper()] = f'{i["ssid"]} {i["frequency"]} MHz'
        return result
    
    def get_wired_interfaces(self):
        wired_info = json.loads(self.client._exec_ssh_cmd('ubus call network.interface dump'))['interface']
        result = {}
        for i in wired_info:
            result[i['device']] = i['interface']
        return result
    
    def get_clients_interface(self):
        result = {}
        wired_interfaces = self.get_wired_interfaces()
        for i in self.parse_arp_table():
            result[i['MAC'].upper()] = i['DEV'] + ' (' + wired_interfaces[i['DEV']] + ')'
        return result
            

    def get_online_devices(self):
        children_devices = []
        wireless_clients = self.get_wireless_clients()
        client_interfaces = self.get_clients_interface()
        for i in self.parse_dhcp():
            children_devices.append(NetDevice(ip_address=i['IP'],mac_address=i['MAC'].upper(),ipv6_address=i['IPv6'],hostname=i['Hostname'],connection_type=wireless_clients.get(i['MAC'].upper()) or client_interfaces.get(i['MAC'].upper())))
        for i in self.parse_arp_table():
            if i['IP'] not in [device.ip_address for device in children_devices] or i['MAC'].upper() not in [device.mac_address for device in children_devices]:
                children_devices.append(NetDevice(ip_address=i['IP'],mac_address=i['MAC'].upper(),connection_type=wireless_clients.get(i['MAC'].upper()) or client_interfaces.get(i['MAC'].upper())))

            #children_devices[i['IP']] = i['MAC'].upper()
        return children_devices

    def get_device_name(self):
        return f'OpenWRT {self.ip_address}'
    def is_online(self):
        return self.client._exec_ssh_cmd('echo "Hello world"').strip() == 'Hello world'
    def get_brightness(self):
        result = {}
        for led_name in self.led_names:
            result[led_name] = int(self.client._exec_ssh_cmd(f"cat /sys/class/leds/{led_name}/brightness").strip())
        return result
    def set_brightness(self, led_name, brightness):
        self.client._exec_ssh_cmd(f"echo {brightness} > /sys/class/leds/{led_name}/brightness")
    def get_color(self):
        result = {}
        brightness = self.get_brightness()
        for led_name in self.led_names:
            if 'red' in led_name:
                result[led_name] = (255,0,0)
            elif 'orange' in led_name:
                result[led_name] = (255,185,0)
            elif 'green' in led_name:
                result[led_name] = (0,255,0)
            elif 'blue' in led_name:
                result[led_name] = (0,0,255)
            else:
                result[led_name] = (0,255,0)
        return result
    def get_control_device(self):
        return self.client._exec_ssh_cmd("cat /etc/*-release | grep PRETTY_NAME -w | cut -d '\"' -f 2")
    
    def get_services(self):
        pattern = re.compile(
            r'^([\-dlrwxst]{10})\s+'                    # Права
            r'(\d+)\s+'                                  # Ссылки
            r'(\w+)\s+'                                  # Владелец
            r'(\w+)\s+'                                  # Группа
            r'(\d+)\s+'                                  # Размер
            r'(\w{3})\s+'                                # Месяц
            r'(\d{1,2})\s+'                              # День
            r'(\S+)\s+'                                  # Время или год
            r'(.+)$'                                     # Имя файла (может содержать пробелы)
        )
        res = self.client._exec_ssh_cmd("ls -l /etc/init.d/")
        result = []
        for line in res.splitlines():
            match = pattern.match(line.strip())
            permissions, links, owner, group, size, month, day, time_or_year, filename = match.groups()
            if permissions.endswith('x'):
                result.append(filename)
        return result
    def get_service_status(self, service_name):
        return self.client._exec_ssh_cmd('/etc/init.d/'+service_name+' status').strip()
    def restart_service(self, service_name):
        return self.client._exec_ssh_cmd('/etc/init.d/'+service_name+' restart')
    def toggle_service(self, service_name, status):
        if status:
            return self.client._exec_ssh_cmd('/etc/init.d/'+service_name+' start')
        else:
            return self.client._exec_ssh_cmd('/etc/init.d/'+service_name+' stop')