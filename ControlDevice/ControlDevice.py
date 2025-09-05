


class ControlDevice:
    def __init__(self, auth_info = {}, no_save = False):
        self.device_type = None
        self.device_abilities = []
        self.auth_info = auth_info
        if 'self' in auth_info:
            del auth_info['self']
        if '__class__' in auth_info:
            del auth_info['__class__']
        self.ip_address = None
        self.mac_address = None
        self.manufacturer_type = None
        self.room = None
        self.manufacturer = None
        self.no_save = no_save
        self.locked = False
    def has_ability(self, ability):
        return ability in [ab[0] for ab in self.device_abilities]
    def toggle_ability(self, ability, **params):
        self.device_abilities.append((ability,params))
    def get_abilities(self):
        return self.device_abilities
    def get_device_type(self):
        return self.device_type
    def get_manufacturer_type(self):
        return self.manufacturer_type
    def get_device_name(self):
        pass
    def is_online(self):
        return True
    
    def on_register(self, register_info = None):
        pass

    def lock(self,lock):
        self.locked = lock
    def is_locked(self):
        return self.locked
    
    def get_control_device(self):
        pass



    def get_online_devices(self):
        pass
    def on(self):
        pass
    def off(self):
        pass
    def get_power(self):
        return True
    def online_device_update(self,target_ip_address,port = 11511):
        pass
