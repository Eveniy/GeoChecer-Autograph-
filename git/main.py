from xml.dom import minidom
import os
import sys
import subprocess
import base64,xml.dom.minidom
from xml.dom.minidom import Node
import configparser
import logging
import time
from datetime import datetime
import re


#Получение данных от файла конфигурации
def readConfig(path='settings.ini'):

    if not os.path.exists(path):
        createConfig(path)
        print('Файл списка устройств создан, внесите устройства в список на обработку!')
        exit()

    config = configparser.ConfigParser()
    config.read(path)

    devices = (config.get("Setting", "devices")).split(',')
    list_geo = config.get("Setting", "geofence_path")
    path_conf = config.get("Setting", "path_conf")
    inupt_geo = config.get("Setting", "conf_in_geo")
    output_geo = config.get("Setting", "conf_out_geo")
    path_last_position = config.get("Setting", 'path_last_position')

    return [dev.strip() for dev in devices], list_geo, path_conf, inupt_geo, output_geo, path_last_position

def createConfig(path):
    config = configparser.ConfigParser()
    config.add_section("Setting")
    config.set("Setting", "devices", "Dev1, Dev2, Dev3")
    config.set("Setting", "geofence_path", "Path geofence")
    config.set("Setting", "path_conf", "Path conf AutoGraph")
    config.set("Setting", "conf_in_geo", "Config post input device in geozone")
    config.set("Setting", "conf_out_geo", "Config post output device in geozone")
    config.set("Setting", "path_last_position", "Path to LastPosition in server Autograph")


    with open(path, "w") as config_file:
        config.write(config_file)

#Чтение координат последнего места пребывания устройства
def read_last_position(devices, path_last_position):

    devices = str(devices)

    if len(devices) == 5:
        devices = "00" + devices
    elif len(str(devices)) == 6:
        devices = "0" + devices

    f = open(f"{path_last_position}\{devices}.kml", 'r')
    data = f.read()
    doc = xml.dom.minidom.parseString(data)

    lenth, lon, w = (doc.getElementsByTagName('coordinates')[0].firstChild.nodeValue).split(',')

    cord_dev = {
        "Device": devices,
        "Lon": float(lon),
        "Len": float(lenth)
                }

    return cord_dev


def get_data(device, command, path_dirconf):

    command = command.split(' ')
    pattern_device= r'\d{5,7}'
    pattern_device = re.compile(pattern_device)
    devicesre = re.findall(pattern_device, device)
    devises = ''
    commandas = ''

    res = []

    for dev in devicesre:
        dir_ServerConf = f"{path_dirconf}"

        if len(dev) == 5:
            dev = "00" + str(dev)
        elif len(dev) == 6:
            dev = "0" + str(dev)

        dir_ServerConf = dir_ServerConf + ("\\") + dev + "\\conf.atc"

        folder_path = os.path.dirname(dir_ServerConf)  # Путь к папке с файлом

        if not os.path.exists(folder_path):  # Если пути не существует создаем его
            os.makedirs(folder_path)


        with open(dir_ServerConf, 'a') as file:  # Открываем фаил и пишем

            for conf in command:
                file.writelines(conf + "\n")
                commandas = commandas + " " + conf
                devises = devises + " " + dev

        res.append("Устройству: {0} отправлена конфигурация {1}".format(devises, commandas))

    return res


def read_points(path):

    all_geo = []

    for geo in os.listdir(path):
        lon = []
        len = []

        file = open(f"{path}/{geo}", 'r')
        data = file.readlines()

        for i in data:
            if "<coordinates>" in i:
                coordinates = (i.replace('<coordinates>', '').replace('</coordinates>', '').strip()).split(' ')

                if coordinates:
                    for el in coordinates:
                        point = el.split(',')
                        lon.append(float(point[1]))
                        len.append(float(point[0]))
        all_geo.append((lon, len))
    return all_geo


def check_geofence(device, geofence):
    res = 0
    dev_cord = read_last_position(device, path_last_position)
    dev_cord = {'Device': '3009740', 'Lon': 59.689056, 'Len': 89.938881}
    list_geo = read_points(geofence)

    for i, j in list_geo:
        maximal = max(i), max(j)
        minimal = min(i), min(j)
        if maximal[0] > dev_cord['Lon'] > minimal[0] and maximal[1] > dev_cord['Len'] > minimal[1]:
            res = res + 1

    return res


now = datetime.now()
log_file = f'{os.getcwd()}/log'

if not os.path.exists(log_file):
    os.mkdir(log_file)

logging.basicConfig(filename=f"{log_file}/{now.year}.{now.month}.{now.day}.log", level=logging.DEBUG)
devices, geofence, path_dirconf, conf_in_geo, conf_out_geo, path_last_position = readConfig()

f = open(f"{log_file}/{now.year}.{now.month}.{now.day}.log", 'r')

regular_conf = r"Conf"
list_log = [line.strip() for line in reversed(f.readlines())]

keys = {}

for i in devices:
    keys[i] = 0

logging.info(f'{now.time()} служба запущена...')

while 1:
    # try:
    now = datetime.now()
    print(f"{now.hour}:{now.minute}:{now.second} запущен опрос устройств...")
    for dev_cord in devices:
        # dev_cord =
        res = check_geofence(dev_cord, geofence)

        if res == 0:
            if keys[f'{dev_cord}'] == 0:
                logging.debug(f'{now.hour}:{now.minute}:{now.second} Device: {dev_cord} out geofence. No setting change required')
            else:
                logging.info(f'{now.hour}:{now.minute}:{now.second} Device:  {dev_cord}  out geofence. Config accept: {conf_out_geo}')
                get_data(dev_cord, conf_out_geo, path_dirconf)

            keys[f'{dev_cord}'] = res

        elif res == 1:

            if keys[f'{dev_cord}'] == 1:
                logging.debug(f'{now.hour}:{now.minute}:{now.second} Device: {dev_cord} in geofence. No setting change required')
            else:
                logging.info(f'{now.hour}:{now.minute}:{now.second} Device:  {dev_cord}  in geofence. Config accept: {conf_in_geo}')
                get_data(dev_cord, conf_in_geo, path_dirconf)

            keys[f'{dev_cord}'] = res

    print(f"Опрос устройств закончен.\n")
    time.sleep(5)
    # except:
    #     now = datetime.now()
    #     logging.error(f'{now.time()}Служба была остановлена из за непредвиденной ошибки!!!')
    #     exit()
