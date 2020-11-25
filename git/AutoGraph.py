import requests
import os
import sqlite3
import configparser

class Autograph_Work:

    def __init__(self, path = 'setting.ini'):
        self.path = path
        self.readConfig()

        self.conn = sqlite3.connect(self.bd)
        self.cursor = self.conn.cursor()

        print(f'File configs: {self.path}')
        self.create_database()
        self.get_token()


    def get_path_db(self):
        # print('Путь базы получен!')
        return self.bd


    def readConfig(self):
        if not os.path.exists(self.path):
            self.createConfig()
            print( 'Файл конфигруации создан в корневой директории, внесите учетные данные!')
            exit(Autograph_Work)

        config = configparser.ConfigParser()
        config.read(self.path)

        self.user = config.get("Connection api Autograph", "username")
        self.password = config.get("Connection api Autograph", "password")
        self.server = config.get("Connection api Autograph", "server")

        self.bd = config.get("Connection local DataBase", "path_db")

        self.db_autograph = config.get("Connection DataBase Autograph", "path_db_autpograph")

        with open(self.path, "w") as config_file:
            config.write(config_file)


    def createConfig(self):
        config = configparser.ConfigParser()
        config.add_section("Connection api Autograph")
        config.set("Connection api Autograph", "userName", "UserName")
        config.set("Connection api Autograph", "password", "Password")
        config.set("Connection api Autograph", "server", "Server Name/ip adress")

        config.add_section("Connection local DataBase")
        config.set("Connection local DataBase", "path_db", "PathToLocalDataBase")

        config.add_section("Connection DataBase Autograph")
        config.set("Connection DataBase Autograph", "path_db_autpograph", "PathToBase Autograph")


        with open(self.path, "w") as config_file:
            config.write(config_file)


    def create_database(self):
        """ Создание таблиц и тригеров"""
        self.conn.execute("create table if not exists api_autograph (type_object, id_object, username)")
        self.conn.execute("create table if not exists api_autograph (type_object, id_object, username)")
        self.conn.execute("create table if not exists groups (id, namegroup, padentid)")
        self.conn.execute("create table if not exists devices (Serial, ID, ParentID, DeviceName, VehicleRegNumber, "
                     "DisplayName, GeoFence, ICCID, MSSID, LLS1, LLS2, LLS3)")
        self.conn.execute("""create table if not exists history_device (dataevent, event, Serial,  ID, ParentID, DeviceName, 
        VehicleRegNumber, DisplayName, GeoFence, ICCID, MSSID, LLS1, LLS2, LLS3)""")
        self.conn.execute("""CREATE TRIGGER if not exists add_device AFTER Insert 
                        on devices
                        BEGIN
                        INSERT INTO history_device(dataevent, event, Serial, ID, ParentID, DeviceName, VehicleRegNumber, 
                        DisplayName, GeoFence, ICCID, MSSID, LLS1, LLS2, LLS3)
                        VALUES ( datetime('now'), 'Insert', NEW.Serial, NEW.ID, NEW.ParentID, NEW.DeviceName, 
                        NEW.VehicleRegNumber, NEW.DisplayName, 
                                NEW.GeoFence, NEW.ICCID, NEW.MSSID, NEW.LLS1, NEW.LLS2, NEW.LLS3);
                        END;""")
        self.conn.execute("""CREATE TRIGGER if not exists del_device BEFORE Delete on devices
            BEGIN
            INSERT INTO history_device (dataevent, event, Serial, ID, ParentID, DeviceName, VehicleRegNumber, DisplayName, GeoFence, ICCID, MSSID, LLS1, LLS2, LLS3)
            VALUES ( datetime('now'), 'Delete', OLD.Serial, OLD.ID, OLD.ParentID, OLD.DeviceName, OLD.VehicleRegNumber, OLD.DisplayName, 
                    OLD.GeoFence, OLD.ICCID, OLD.MSSID, OLD.LLS1, OLD.LLS2, OLD.LLS3);
            END;
            """)
        self.conn.execute("""CREATE TRIGGER if not exists upd_device AFTER Update on devices
            BEGIN
            INSERT INTO history_device(dataevent, event, Serial, ID, ParentID, DeviceName, VehicleRegNumber, DisplayName, GeoFence, ICCID, MSSID, LLS1, LLS2, LLS3)
            VALUES (             datetime('now'),             'Updating',             NEW.Serial,
                Case When  NEW.ID == OLD.ID then null Else new.ID End,
                Case When  NEW.ParentID == OLD.ParentID then null Else new.ParentID End,
                Case When  NEW.DeviceName == OLD.DeviceName then null Else new.DeviceName End,
                Case When  NEW.VehicleRegNumber == OLD.VehicleRegNumber then null Else new.VehicleRegNumber End,
                Case When  NEW.DisplayName == OLD.DisplayName then null Else new.DisplayName End,
                Case When  NEW.GeoFence == OLD.GeoFence then null Else new.GeoFence End,
                Case When  NEW.ICCID == OLD.ICCID then null Else new.ICCID End,
                Case When  NEW.MSSID == OLD.MSSID then null Else new.MSSID End,
                Case When  NEW.LLS1 == OLD.LLS1 then null Else new.LLS1 End,
                Case When  NEW.LLS2 == OLD.LLS2 then null Else new.LLS2 End,
                Case When  NEW.LLS3 == OLD.LLS3 then null Else new.LLS3 End
                ); 
                END;
        """)

        self.conn.commit()


    def get_token(self):
        self.cursor.execute(" SELECT id_object FROM api_autograph where type_object = 'token'")
        token  = self.cursor.fetchone()

        if token == None:
                # print('Токен отсутствует в базе данных...')
                self.post_token_base()
        else:
            self.token = token[0]
            # print(f'Токен получен.')
            self.get_schemas()


    def get_schemas(self):
        self.cursor.execute(" SELECT id_object FROM api_autograph where type_object = 'schemas'")
        schemas = self.cursor.fetchone()

        if schemas == None:
            # print('Схема отсутствует в базе данных...')
            self.post_schemas_base()
        else:
            self.schemas = schemas[0]
            # print(f'Схема получена.')


    def get_items(self):
        items = requests.get(f"http://{self.server}/ServiceJSON/EnumDevices?&schemaID={self.schemas}&session={self.token}").json()['Items']
        return items


    def get_groups(self):
        groups = requests.get(f"http://{self.server}/ServiceJSON/EnumDevices?&schemaID={self.schemas}&session={self.token}").json()['Groups']
        return groups


    def get_id_device(self, device):
        for i in self.get_items():
            if i['Serial'] == device:
                return i['ID']
        print("Устройства нет в схеме!")
        exit()


    def get_device_coordinates(self, device):
        coordinates = requests.get(f"http://{self.server}/ServiceJSON/GetOnlineInfo?session={self.token}&schemaID={self.schemas}&IDs={self.get_id_device(device)}").json()
        return coordinates


    def post_token_base(self):

        token = (requests.get(f'http://{self.server}/ServiceJSON/Login?UserName={self.user}&Password={self.password}'))

        if token.status_code == 200:
            self.token = token.text
        elif token.status_code == 403:
            print("Проверьте имя и пароль пользователя в файле конфигурации, ДОСТУП НЕ ПОЛУЧЕН!")
            exit()

        self.cursor.execute(f"   INSERT INTO api_autograph (type_object, id_object, username) VALUES('token', '{self.token}', '{self.user}')")
        # print('Токен внесен в базу данных...')
        self.conn.commit()
        self.get_token()


    def post_schemas_base(self):
        schemas = requests.get(f'http://{self.server}/ServiceJSON/EnumSchemas?session={self.token}').json()[0]
        self.conn.execute(f"   INSERT INTO api_autograph (type_object, id_object, username) VALUES('schemas', '{schemas['ID']}', '{self.user}')")
        # print(f'Схема "{schemas["Name"]}" внесена в базу данных...')
        self.conn.commit()
        self.get_schemas()


    def post_groups(self, groups):
        self.cursor.execute(f" INSERT INTO groups (id, namegroup , padentid) VALUES('{groups['ID']}', '{groups['Name']}','{groups['ParentID']}' )")
        self.conn.commit()


    def json_items(self):
        self.devices = []

        ins_grops = ['6baaf827-549e-43da-91b4-ae5dd06f4028', '3d7e2b65-89ef-4813-b8e9-d45d87451704'] # исключения

        for el in self.get_items():
                Serial, ID, ParentID, DeviceName, DisplayName, GeoFence, ICCID, MSSID, LLS1, LLS2, LLS3, VehicleRegNumber = '', '', '', '', '', '', '', '', [], [], [], ''
                Serial, ID, ParentID, DeviceName = el['Serial'], el['ID'], el['ParentID'], el['Name']

                for property in el['Properties']:
                    if property['Name'] == 'DisplayName':
                        DisplayName = property['Value']
                    if property['Name'] == 'ICCID':
                        ICCID = property['Value']
                    if property['Name'] == 'LLS1':
                        LLS1 = str([(i['Input'], i['Output']) for i in property['Value']['Items']])
                        # print(LLS1)
                    if property['Name'] == 'LLS2':
                        LLS2 = str([(i['Input'], i['Output']) for i in property['Value']['Items']])
                    if property['Name'] == 'LLS3':
                        LLS3 = str([(i['Input'], i['Output']) for i in property['Value']['Items']])
                    if property['Name'] == 'MSSID':
                        MSSID = property['Value']
                    if property['Name'] == 'VehicleRegNumber':
                        VehicleRegNumber = property['Value']
                    if property['Type'] == 15:
                        GeoFence = property['Name']

                if el['ParentID'] not in ins_grops:
                    self.devices.append({
                        'Serial': Serial,
                        'ID': ID,
                        'ParentID': ParentID,
                        'DeviceName': DeviceName,
                        'VehicleRegNumber': VehicleRegNumber,
                        'DisplayName': DisplayName,
                        'GeoFence': GeoFence,
                        'ICCID': str(ICCID),
                        'MSSID': str(MSSID),
                        'LLS1': str(LLS1),
                        'LLS2': str(LLS1),
                        'LLS3': str(LLS3)
                    })
        return self.devices

