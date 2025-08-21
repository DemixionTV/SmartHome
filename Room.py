import sqlite3
from typing import Dict, List
import json
import time
from threading import Thread
import inspect

from Diamon2.Progr.Config import DIAMON_CONFIG_PATH
from Diamon2.Progr.Net import NetDevice,getOnlineDevices, getSubnet, getLocalIPs, HTTPRequestquestHandler, getLocalIP
from http.server import HTTPServer
from Diamon2.Progr.Colors import bcolors
from Diamon2.Progr.Packages import DiamonPackage, LogType

from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType, DeviceAbility

from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.SmartDevice import SmartDevice

from Diamon2.SmartHome3.Manufacturer.TPLinkTapo import TPLinkTapo
from Diamon2.SmartHome3.Manufacturer.OpenWRT import OpenWRT
from Diamon2.SmartHome3.Manufacturer.Tuya import Tuya
from Diamon2.SmartHome3.Manufacturer.Yeelight import Yeelight
from Diamon2.SmartHome3.Manufacturer.Xigmanas import Xigmanas
from Diamon2.SmartHome3.Manufacturer.Discord import Discord



class Room(DiamonPackage):
    def __init__(self):
        super().__init__('SmartRoom')
        self.connection = sqlite3.connect(DIAMON_CONFIG_PATH + '/SmartHome/Room.db',check_same_thread=False)
        cursor = self.connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute('create table if not exists Manufacturer(id integer primary key autoincrement, name text unique)')
        cursor.execute('create table if not exists DeviceType(id integer primary key autoincrement, name text unique)')
        cursor.execute('create table if not exists Auth_info(id integer primary key autoincrement, name text unique, manufacturer int, auth_info text unique, foreign key(manufacturer) references Manufacturer(id) ON DELETE CASCADE)')
        cursor.execute('create table if not exists Device(id integer primary key autoincrement, name text unique not null, auth_info int, ip_address text, mac_address text unique, device_type int, foreign key(auth_info) references Auth_info(id) ON DELETE CASCADE, foreign key(device_type) references DeviceType(id) ON DELETE CASCADE) ')
        cursor.execute('create table if not exists NotSmartDevice(id integer primary key autoincrement, name text, ip_address text unique, mac_address text unique)')
        cursor.execute('create table if not exists RealName(id integer primary key autoincrement, name text unique, mac_address text unique, real_name text)')
        self.connection.commit()
        for manufacturer in ManufacturerType:
            cursor.execute('insert into Manufacturer(name) values (?) on conflict do nothing',(manufacturer.value,))
        for device_type in DeviceType:
            cursor.execute('insert into DeviceType(name) values (?) on conflict do nothing',(device_type.name,))
        self.connection.commit()
        self.log(LogType.DatabaseInit,"SmartHome",DIAMON_CONFIG_PATH + '/SmartHome/Room.db')


        self.subnets = [0,1]
        self.devices:Dict[str,SmartDevice] = {}
        self.manufacturers:Dict[str, Manufacturer] = {}
        self.manufacturers_db = {}
        self.register_info = {}
        cursor.execute('select id, name from Manufacturer')
        for manufacturer_id, manufacturer_name in cursor.fetchall():
            self.manufacturers_db[ManufacturerType(manufacturer_name)] = manufacturer_id
        self.device_types_db = {}
        cursor.execute('select id, name from DeviceType')
        for dt_id, dt_name in cursor.fetchall():
            self.device_types_db[DeviceType[dt_name]] = dt_id


        self.func_abilities:Dict[DeviceAbility,str] = {}
        for func in SmartDevice.__dict__.keys():
            if hasattr(getattr(SmartDevice,func),"device_ability"):
                self.func_abilities[getattr(getattr(SmartDevice,func),"device_ability")] = func
        


        self.generate_device_parameter("get_ip_address")
        self.generate_device_parameter("get_mac_address")
        self.generate_device_parameter("get_device_type")
        self.generate_device_parameter("get_abilities")
        self.generate_device_parameter("is_online")
        for f in self.func_abilities.values():
            if f not in ['get_online_devices']:
                self.generate_device_parameter(f[:])

        self.loaded = False
        self.load_saved_manufacturers()
        self.online_devices:List[NetDevice] = self.get_online_devices()
        self.not_smart_devices:List[NetDevice] = self.get_not_smart_devices()
        self.offline_devices:Dict[str, bool] = {}
        self.load_saved_devices()
        self.rescan_devices()
        self.loaded = True
        self.check_offline_devices()

        server_address = (getLocalIP(), 11511)
        httpd = HTTPServer(server_address, HTTPRequestquestHandler)
        httpd.handler = self.on_http_request
        httpd.title = "Diamon2 SmartHome"
        th = Thread(target=lambda:httpd.serve_forever(), daemon=True)
        th.start()
        self.log(LogType.WebServerStarted,f'{httpd.title}', f'{server_address[0]}:{server_address[1]}')
        self.room_tick_thread = Thread(target=self.room_tick, daemon=True)
        self.room_tick_thread.start()
        self.log(LogType.Init,'Initialized')



    def on_http_request(self, path,params):
        self.log(LogType.WebServerRequest,'HTTP Request',f'{path}\n{params}')
        if path == '/device_list':
            if (params['ip'][0] in [d[0] for d in self.offline_devices.values()] or params['mac'][0].upper() in [d[1] for d in self.offline_devices.values()]) and params['event'][0] in ['add','update']:
                for name, (device_ip, mac, manufacturer_name) in self.offline_devices.items():
                    if manufacturer_name in self.manufacturers:
                        try:
                            self.register_device(self.manufacturers[manufacturer_name].create_device(device_ip))
                        except Exception as e:
                            self.error_log(e)
            elif (params['ip'][0] in self.get_ip_address().values() or params['mac'][0].upper() in self.get_mac_address().values()) and params['event'][0] == 'remove':
                for device in self.get_device_list():
                    if self.devices[device].get_ip_address() == params['ip'][0] or self.devices[device].get_mac_address() == params['mac'][0].upper():
                        self.unregister_device(device)
                        


                    
        return ""

    def room_tick(self):
        while True:
            self.log(LogType.ProgramInfo,'Room tick started')
            online = self.is_online()
            for device in list(online.keys()).copy():
                if not online[device]:
                    self.unregister_device(device)
            time.sleep(10)
            self.log(LogType.ProgramInfo,'Room tick ended')

    def check_offline_devices(self):
        cursor = self.connection.cursor()
        cursor.execute('select Device.name, ip_address, mac_address, Auth_info.name from Device inner join Auth_info on Auth_info.id = Device.auth_info')
        self.offline_devices = {}
        for device_name, ip_address, mac_address, manufacturer_name in cursor.fetchall():
            if device_name not in self.devices:
                self.offline_devices[device_name] = (ip_address, mac_address, manufacturer_name)
        self.log(LogType.ProgramInfo,'Checked offline devices',f'{self.offline_devices}')


    def generate_device_parameter(self,parameter_name):
        def device_method(device = None, *args, **kwargs):
            result = {}
            for d in self.get_device_list(device):
                result[d] = getattr(self.devices[d],parameter_name)(*args,**kwargs)
            return result
        setattr(self,parameter_name,device_method)
        self.log(LogType.ProgramInfo,"Generated device parameter",parameter_name)


    def load_saved_manufacturers(self):
        cursor = self.connection.cursor()
        cursor.execute('select Auth_info.name, Manufacturer.name, auth_info from Auth_info inner join Manufacturer on Auth_info.manufacturer = Manufacturer.id')
        for auth_name, manufacturer_name, auth_info in cursor.fetchall():
            self.register_manufacturer(auth_name, ManufacturerType(manufacturer_name), **json.loads(auth_info))
    
    def load_saved_devices(self):
        cursor = self.connection.cursor()
        cursor.execute('select auth_info.name, Device.ip_address, Device.name from Device inner join Auth_info on Device.auth_info = Auth_info.id')
        for manufacturer_name, device_ip, device_name in cursor.fetchall():
            if device_name not in self.devices:
                if manufacturer_name in self.manufacturers:
                    try:
                        self.register_device(self.manufacturers[manufacturer_name].create_device(device_ip))
                    except Exception as e:
                        self.error_log(e)
        
    
    def get_online_devices(self):
        device_list_with_children_ips = self.get_device_list(DeviceAbility.GetOnlineDevices)
        if len(device_list_with_children_ips) == 0:
            return getOnlineDevices(self.subnets)
        else:
            devs = []
            for d in device_list_with_children_ips:
                online_devs = self.devices[d].get_online_devices()
                devs += online_devs
            return devs
    
    
    
    def get_device_list(self, device_lst = None):
        if device_lst == None:
            return list(self.devices.keys())
        if type(device_lst) == list:
            r = []
            for lst in device_lst:
                r += self.get_device_list(lst)
            return r
        elif type(device_lst) == str:
            return [device_lst]
        device_list = []
        for device in self.devices:
            if type(device_lst) == DeviceType:
                if self.devices[device].control_device.get_device_type() == device_lst:
                    device_list.append(device)
            elif type(device_lst) == DeviceAbility:
                if self.devices[device].control_device.has_ability(device_lst):
                    device_list.append(device)
            elif type(device_lst) == ManufacturerType:
                if self.devices[device].control_device.get_manufacturer_type() == device_lst:
                    device_list.append(device)
        return device_list

    def get_not_smart_devices(self):
        cursor = self.connection.cursor()
        cursor.execute('select NotSmartDevice.name, NotSmartDevice.ip_address, NotSmartDevice.mac_address from NotSmartDevice')
        devices = []
        for name, ip, mac in cursor.fetchall():
            devices.append(NetDevice(hostname = name,ip_address=ip,mac_address=mac))
        return devices



    def detect_manufacturer(self, device:NetDevice):
        for manufacturer in self.manufacturers:
            if self.manufacturers[manufacturer].is_my_device(device.ip_address):
                print(f'{bcolors.WARNING}{manufacturer}{bcolors.ENDC} {bcolors.OKGREEN}{device.ip_address}{bcolors.ENDC} {bcolors.PURPLE}is my device{bcolors.ENDC}')
                return manufacturer
            else:
                print(f'{bcolors.WARNING}{manufacturer}{bcolors.ENDC} {bcolors.FAIL}{device.ip_address}{bcolors.ENDC} {bcolors.PURPLE}is not my device{bcolors.ENDC}')
        return None

    
    def rescan_devices(self):
        for device in self.online_devices:
            if device.ip_address in self.get_ip_address().values() or device.mac_address in self.get_mac_address().values() or device.ip_address in getLocalIPs() or device.ip_address in self.not_smart_devices or (device.mac_address in self.not_smart_devices and device.mac_address != None) or (device.ip_address in [i[0] for i in self.offline_devices.values()]):
                continue
            manufacturer = self.detect_manufacturer(device)
            if manufacturer != None:
                cursor = self.connection.cursor()
                cursor.execute('delete from NotSmartDevice where ip_address=?',(device.ip_address,))
                if device.mac_address != None:
                    cursor.execute('delete from NotSmartDevice where mac_address=?',(device.mac_address,))

                self.register_device(self.manufacturers[manufacturer].create_device(device.ip_address))
            else:
                cursor = self.connection.cursor()
                cursor.execute('insert into NotSmartDevice(name, ip_address, mac_address) values (?, ?, ?) on conflict do nothing', (device.hostname or None, device.ip_address, device.mac_address))
                self.not_smart_devices.append(device)
        for manufacturer in self.manufacturers:
            for dev in self.manufacturers[manufacturer].create_noip_devices():
                self.register_device(dev)
        self.connection.commit()
#                print(f'{bcolors.WARNING}{manufacturer}{bcolors.ENDC} {bcolors.FAIL}{device.ip_address}{bcolors.ENDC} {bcolors.PURPLE}is not my device{bcolors.ENDC}')


    def unregister_manufacturer(self, manufacturer_name):
        if manufacturer_name in self.manufacturers:
            for device in list(self.devices.keys()).copy():
                if self.devices[device].manufacturer == self.manufacturers[manufacturer_name]:
                    del self.devices[device]
            del self.manufacturers[manufacturer_name]
            cursor = self.connection.cursor()
            cursor.execute('delete from Auth_info where name=?',(manufacturer_name,))
            self.connection.commit()
            print(f'{bcolors.FAIL}Unregistered manufacturer{bcolors.ENDC} {bcolors.PURPLE}{manufacturer_name}{bcolors.ENDC}')

            

    def register_manufacturer(self, manufacturer_name, manufacturer_type, **kargs):
        if manufacturer_name in self.manufacturers:
            self.unregister_manufacturer(manufacturer_name)
        if manufacturer_type == ManufacturerType.TP_Link_Tapo:
            self.manufacturers[manufacturer_name] = TPLinkTapo(self)
        elif manufacturer_type == ManufacturerType.OpenWRT:
            self.manufacturers[manufacturer_name] = OpenWRT(self)
        elif manufacturer_type == ManufacturerType.Tuya:
            self.manufacturers[manufacturer_name] = Tuya(self)
        elif manufacturer_type == ManufacturerType.Yeelight:
            self.manufacturers[manufacturer_name] = Yeelight(self)
        elif manufacturer_type == ManufacturerType.Xigmanas:
            self.manufacturers[manufacturer_name] = Xigmanas(self)
        elif manufacturer_type == ManufacturerType.Discord:
            self.manufacturers[manufacturer_name] = Discord(self)
        else:
            self.log(LogType.ProgramWarning,'Manufacturer register failed',f'{manufacturer_name} {manufacturer_type.value}')
            return
        self.manufacturers[manufacturer_name].manufacturer_name = manufacturer_name
        self.log(LogType.Program_OK,f'Registered manufacturer',f'{manufacturer_name} {manufacturer_type.value}')
#        print(f'{bcolors.OKGREEN}Registered manufacturer{bcolors.ENDC} {bcolors.PURPLE}{manufacturer_name}{bcolors.ENDC} {bcolors.WARNING}{manufacturer_type.value}{bcolors.ENDC}')
        self.auth_manufacturer(manufacturer_name,**kargs)


    def get_needed_auth_parameters(self):
        result = {}
        info = globals().copy()
        for name, obj in info.items():
            if isinstance(obj, type):  # Это действительно класс
                if issubclass(obj, Manufacturer):
                    try:
                        o = obj(None)
                        result[o.manufacturer_type] = [i for i,_ in inspect.signature(o.auth).parameters.items() if i != 'self' and i != 'args']
                    except:
                        pass
        return result

            
    
    def auth_manufacturer(self, manufacturer_name, **kargs):
        if manufacturer_name in self.manufacturers:
            self.manufacturers[manufacturer_name].auth(**kargs)
#            print(f'{bcolors.OKGREEN}Authed manufacturer{bcolors.ENDC} {bcolors.PURPLE}{manufacturer_name}{bcolors.ENDC}')
            self.log(LogType.ProgramInfo,f'Authed manufacturer',manufacturer_name)
            cursor = self.connection.cursor()
            manuf_type = self.manufacturers[manufacturer_name].manufacturer_type
            cursor.execute('insert into Auth_info(name, manufacturer, auth_info) values (?, ?, ?) on conflict do update set auth_info=?', (manufacturer_name, self.manufacturers_db[manuf_type], json.dumps(kargs), json.dumps(kargs)))
            self.connection.commit()
            cursor.execute('select ip_address from Device inner join Auth_info on Device.auth_info = Auth_info.id where Auth_info.name=?', (manufacturer_name,))
            for ip_address, in cursor.fetchall():
                try:
                    self.register_device(self.manufacturers[manufacturer_name].create_device(ip_address))
                except:
                    pass
            if self.loaded:
                self.not_smart_devices = []
                self.rescan_devices()
                self.not_smart_devices = self.get_not_smart_devices()


    def update_real_name(self, device, mac_address, name):
        cursor = self.connection.cursor()
        cursor.execute('insert into RealName(name, mac_address, real_name) values (?, ?, ?) on conflict do update set real_name=?', (device, mac_address, name, name))
        self.connection.commit()
    
    def get_real_names(self):
        cursor = self.connection.cursor()
        cursor.execute('select name, mac_address, real_name from RealName')
        return cursor.fetchall()



    def register_device(self, device:SmartDevice):
        try:
            if device == None:
                return
            cursor = self.connection.cursor()
            cursor.execute('select id from Auth_info where name=?',(device.manufacturer.manufacturer_name,))
            auth_id = cursor.fetchone()[0]
            cursor.execute('insert into Device(name, auth_info, ip_address, mac_address, device_type) values (?, ?, ?, ?, ?) on conflict(name) do update set auth_info = ?, ip_address = ?, mac_address = ?, device_type = ?', (device.device_name, auth_id, device.control_device.ip_address, device.control_device.mac_address, self.device_types_db[device.device_type],                                                                                                                                                                auth_id, device.control_device.ip_address, device.control_device.mac_address, self.device_types_db[device.device_type]))
            self.connection.commit()
            if device.device_name in self.devices:
                self.log(LogType.ProgramWarning,f'Device already exists',str(self.devices[device.device_name]))
#                print(f'{bcolors.FAIL}Device {bcolors.ENDC}{self.devices[device.device_name]} {bcolors.FAIL}already exists{bcolors.ENDC}')
                return
            self.devices[device.device_name] = device
            self.devices[device.device_name].on_register(self.register_info.get(device.device_name,{}))
            self.register_info[device.device_name] = {}
            self.check_offline_devices()
            self.log(LogType.Program_OK,f'Registered device',str(self.devices[device.device_name]))
            print(f'{bcolors.OKCYAN}Registered device {bcolors.ENDC}{self.devices[device.device_name]}{bcolors.ENDC}')
            if device.has_ability(DeviceAbility.ChildrenDevices):
                for child in device.create_children_devices():
                    self.register_device(child)

        except Exception as e:
            self.error_log(e)
#            print(f'{bcolors.FAIL}Error registering device {bcolors.ENDC}{device.device_name}{bcolors.ENDC}',bcolors.error(e))
    
    def unregister_device(self, device, force = False):
        if device in self.devices:
            del self.devices[device]
            self.check_offline_devices()
            self.log(LogType.ProgramWarning,f'Unregistered device',str(device))
        if force:
            cursor = self.connection.cursor()
            if device in self.offline_devices:
                ip_address, mac_address, manufacturer_name = self.offline_devices[device]
                cursor.execute('delete from NotSmartDevice where ip_address=? or mac_address = ?',(ip_address,mac_address))
                del self.offline_devices[device]
            cursor.execute('delete from Device where name=?',(device,))
            self.connection.commit()
#            print(f'{bcolors.FAIL}Unregistered device {bcolors.ENDC}{device}{bcolors.ENDC}')
        
    
    def use_ability(self, device, ability:DeviceAbility, *args, **kwargs):
        res = {}
        for d in self.get_device_list(device):
            res[d] = getattr(self.devices[d],self.func_abilities[ability])(*args, **kwargs)
        return res


    def update_register_info(self, device, key, value):
        if device not in self.register_info:
            self.register_info[device] = {}
        self.register_info[device][key] = value

    def get_auth_info(self):
        auth_info = {}
        for m in self.manufacturers:
            auth_info[self.manufacturers[m].manufacturer_type,m] = self.manufacturers[m].auth_info
            for auth_info_key in auth_info[self.manufacturers[m].manufacturer_type,m]:
                if auth_info_key.lower() in ['password','api_key','secret_key']:
                    auth_info[self.manufacturers[m].manufacturer_type,m][auth_info_key] = '********'

        return auth_info
    

    def on_bot_command(self, device, command, full_text, channel, user):
        return

            
room = Room()