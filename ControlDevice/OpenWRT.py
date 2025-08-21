from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.Progr.SSH import SSH, ArpStatus
from Diamon2.Progr.Net import NetDevice
import re

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
            r'^(?P<IP>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'\s+dev\s+\S+'
            r'\s+lladdr\s+(?P<MAC>[0-9a-fA-F:]{17})'
            r'(?:\s+.*?\s+)?(?P<STATUS>REACHABLE|STALE|DELAY|PROBE|FAILED|NOARP|PERMANENT)\b',
            re.MULTILINE
        )
        matches = pattern.finditer(res)
        result = []
        for match in matches:
            r = match.groupdict()
            result.append(r)
        return result
    def get_online_devices(self):
        children_devices = []
        for i in self.parse_dhcp():
            children_devices.append(NetDevice(ip_address=i['IP'],mac_address=i['MAC'].upper(),ipv6_address=i['IPv6'],hostname=i['Hostname']))
        for i in self.parse_arp_table():
            if i['IP'] not in [device.ip_address for device in children_devices] or i['MAC'].upper() not in [device.mac_address for device in children_devices]:
                children_devices.append(NetDevice(ip_address=i['IP'],mac_address=i['MAC'].upper()))

            #children_devices[i['IP']] = i['MAC'].upper()
        return children_devices

    def get_device_name(self):
        return f'OpenWRT {self.ip_address}'