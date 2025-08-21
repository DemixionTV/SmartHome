from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.Progr.SSH import SSH, ArpStatus
from Diamon2.Progr.Net import NetDevice
from Diamon2.Progr.Colors import bcolors
import paramiko
import re
from threading import Thread

import time

class XigmanasCD(ControlDevice):
    def __init__(self, ip_address, login, password, port):
        super().__init__(locals().copy())
        self.ip_address = ip_address
        self.login = login
        self.password = password
        self.port = port
        self.client = SSH()
        self.client.connect(self.ip_address, port, login, password)
        self.mac_address = self.client._exec_ssh_cmd("ifconfig | grep ether | awk '{ print $2 }'").upper().replace('.',':')
        self.device_type = DeviceType.Nas_Server
        self.manufacturer_type = ManufacturerType.Xigmanas

    def get_device_name(self):
        return f'Xigmanas {self.ip_address}'
    
    def is_online(self):
        if not self.client.connected:
            return True

        return self.client._exec_ssh_cmd('echo Hello world!').strip() == 'Hello world!'
