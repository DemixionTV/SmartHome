from typing import List

from Diamon2.SmartHome3.SmartDevice import SmartDevice

class Manufacturer:
    def __init__(self, manufacturer_type, room):
        self.manufacturer_type = manufacturer_type
        self.registered_devices = []
        self.manufacturer_name = None
        self.room = room
        self.auth_info = None
    

    
    def auth(self, **args):
        self.auth_info = args

    def is_my_device(self, ip_address) -> bool:
        return False
    
    def create_device(self, ip_address) -> SmartDevice:
        return None
    
    def create_noip_devices(self) -> List[SmartDevice]:
        return []
    
