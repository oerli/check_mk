#!/usr/local/bin/python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# Uniflow MEAP Connection Status check
# 15.05.2019 by Roland Mueller

import sys
import argparse
import requests
import time
import json
from requests_ntlm import HttpNtlmAuth
from lxml import etree

class Printer:
    def __init__(self):
        self.serialNumber = ""
        self.deviceType = ""
        self.ipAddress = ""
        self.deviceId = ""
        self.deviceStatus = "Ok"
        self.timeStatus = "Unknown"
        self.connectionStatus = "Unknown"
        self.connectionDescription = ""
        self.time = 0
        self.critTime = 28800
        self.warnTime = 1800

def get_data(connect="", user="", password="", limit=""):
    import requests

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache',
    }

    data = {
        'action': 'load',
        'category': 'meap',
        'subCategory': 'MeapStatusList',
        'subCatStringId': 'List View',
        'displayName': 'MEAP & miniMIND',
        'EAIManufacturer': 'undefined',
        'resultsPerPage': limit,
        'pageNumber': 'undefined',
        'orderCriteria': 'SerialNumber Asc',
        'searchCriteria': 'undefined'
    }

    response = requests.post(connect + '/pwserver/ajaxGetDeviceListDataSet.asp', headers=headers, data=data, auth=HttpNtlmAuth(user, password))
    
    data = etree.fromstring(response.content)

    printers = []
    for elements in data.findall("record"):
        printer = Printer()
        for element in elements:
            if element.attrib['name'] == 'SerialNumber':
                printer.serialNumber = element.text
            elif element.attrib['name'] == 'DeviceType':
                printer.deviceType = element.text.replace(" ", "_")
            elif element.attrib['name'] == 'DeviceID':
                printer.deviceId = element.text
                if element.text == "MiCard - EEPROM error FW Update necessary!":
                    printer.deviceStatus = "Warning"
            elif element.attrib['name'] == 'IPAddress':
                printer.ipAddress = element.text
            elif element.attrib['name'] == "Behaviour":
                printer.connectionDescription = element.text
                if element.text == "MOMLM=connected=LMCARDTYPELOGIN=Card Type Login@MOMCLIENT=connected=SECUREPRINT=Secure Print Behavior":
                    printer.connectionStatus = "Ok"
                elif element.text == "MOMLM=connected==@MOMCLIENT=notconnected==" or element.text == "MOMLM=connected=LMCARDTYPELOGIN=Card Type Login@MOMCLIENT=notconnected==" or element.text == "MOMLM=connected=LMCARDTYPELOGIN=Card Type Login@MOMCLIENT=connected==":
                    printer.connectionStatus = "Warning"
                else:
                    printer.connectionStatus = "Warning"
            elif element.attrib['name'] == "LastDataReceivedTimeStamp":
                printer.time = int(time.time() - float(element.text))
                if printer.time > printer.critTime:
                    printer.timeStatus = "Error"
                elif printer.time > printer.warnTime:
                    printer.timeStatus = "Warning"
                else:
                    printer.timeStatus = "Ok"

        printers.append(printer)

    return printers

def evaluate_data(printers=[], descriptions={}):
    for printer in printers:
        # try to resolve description
        if printer.serialNumber in descriptions:
            description = descriptions[printer.serialNumber]
        else:
            description = printer.serialNumber
            
        if printer.connectionStatus == "Ok" and printer.timeStatus == "Ok" and printer.deviceStatus == "Ok":
            message = "0 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " is connected"  
        elif printer.deviceStatus == "Warning":
            message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") Card Reader Error (!!)"
        elif printer.connectionStatus == "Warning":
            if printer.connectionDescription == "MOMLM=connected==" or printer.connectionDescription == "MOMLM=connected=LMCARDTYPELOGIN=Card Type Login":
                message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") Secure Scan Print Application(!) not loaded"
            elif printer.connectionDescription == "MOMLM=connected==@MOMCLIENT=notconnected==" or printer.connectionDescription == "MOMLM=connected=LMCARDTYPELOGIN=Card Type Login@MOMCLIENT=notconnected==":
                message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") Secure Scan Print Application(!) not connected"
            elif printer.connectionDescription == "MOMLM=connected=LMCARDTYPELOGIN=Card Type Login@MOMCLIENT=connected==":
                message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") Secure Scan Print Application(!) configuration not loaded"
            elif printer.connectionDescription == "MOMLM=notconnected==@MOMCLIENT=notconnected==":
                message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") Universal Login Manager(!) not connected"
            else:
                message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") Universal Login Manager(!) not loaded"
        elif printer.time > printer.critTime:
            message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") did not connect since " + (str(int(printer.time/3600/24)) + " days(!)" if printer.time/3600 >= 24 else str(int(printer.time/3600)) + " hours(!)")
        elif printer.time > printer.warnTime:
            message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";" + str(printer.warnTime) + ";" + str(printer.critTime) + ";; " + description + " (" + printer.ipAddress + ") did not connect since " + str(int(printer.time/3600)) + " hours " + str(int((printer.time%3600/60))) + " minutes"
        else:
            message = "3 MEAP_" + printer.serialNumber + " - " + description + " (" + printer.ipAddress + ") unknown status"
        print(message)

def main(argv=None):
    description = """Check to parse the NTWare Uniflow Connection MEAP page
    Use this script with --connect --user --password
    eg. ./uniflow_meap.py --connect http://localhost --user user --password pw """
    
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-u', '--user', dest='user',
                         help='user which has *admin* rights on uniflow server',
                         action='store',
                         required=True)

    parser.add_argument('-p', '--password', dest='password',
                         help='ntlm password for user',
                         action='store',
                         required=True)

    parser.add_argument('-c', '--connect', dest='connect',
                            help='uniflow connection string (protocol and host only)',
                            action='store',
                            default='http://localhost')

    parser.add_argument('-l', '--limit', dest='limit',
                            help='limit maximum devices',
                            action='store',
                            default='15')

    parser.add_argument('-d', '--descriptions', dest='descriptions',
                        help='printer description/names json filename to translate from serial numbers',
                        action='store')

    try:
        args = parser.parse_args()
    except:
        # Something didn't work. We will return an unknown.
        print(' invalid argument(s) {usage}'.format(usage=parser.format_usage()))
        sys.exit(3)
    
    descriptions = {}

    if args.descriptions:
        with open(args.descriptions, 'r') as file:
            descriptions = json.load(file)

    print("<<<local>>>")
    evaluate_data(printers=get_data(connect=args.connect, user=args.user, password=args.password, limit=args.limit), descriptions=descriptions)


if __name__ == '__main__':
    main(sys.argv)