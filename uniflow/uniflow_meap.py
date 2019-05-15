#!/usr/local/bin/python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# Uniflow MEAP Connection Status check
# 15.05.2019 by Roland Mueller

import sys
import argparse
import requests
import time
from requests_ntlm import HttpNtlmAuth
from lxml import etree

class Printer:
    def __init__(self):
        self.serialNumber = ""
        self.deviceType = ""
        self.ipAddress = ""
        self.deviceId = ""
        self.timeStatus = "Unknown"
        self.connectionStatus = "Unknown"
        self.time = 0


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
            elif element.attrib['name'] == 'IPAddress':
                printer.ipAddress = element.text
            elif element.attrib['name'] == "Behaviour":
                if element.text == "MOMLM=connected=LMCARDTYPELOGIN=Card Type Login@MOMCLIENT=connected=SECUREPRINT=Secure Print Behavior":
                    printer.connectionStatus = "Ok"
                else:
                    printer.connectionStatus = "Error"
            elif element.attrib['name'] == "LastDataReceivedTimeStamp":
                printer.time = int(time.time() - float(element.text))
                if  printer.time > 7200:
                    printer.timeStatus = "Error"
                elif printer.time > 1800:
                    printer.timeStatus = "Warning"
                else:
                    printer.timeStatus = "Ok"

        printers.append(printer)

    return printers

def evaluate_data(printers=[]):
    for printer in printers:
        if printer.connectionStatus == "Ok" and printer.timeStatus == "Ok":
            message = "0 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";1800;7200;; Printer " + printer.serialNumber + " is connected"
        elif printer.connectionStatus == "Error":
            message = "2 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";1800;7200;; Printer " + printer.serialNumber + " has MEAP Application Error (!!)"
        elif printer.timeStatus == "Error":
            message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";1800;7200;; Printer " + printer.serialNumber + " did not connect(!!) in the last " + str(printer.time/60) + " minutes"
        elif printer.timeStatus == "Warning":
            message = "1 MEAP_" + printer.serialNumber + " run_age=" + str(printer.time) + ";1800;7200;; Printer " + printer.serialNumber + " did not connect(!) in the last " + str(printer.time/60) + " minutes"
        else:
            message = "0 MEAP_" + printer.serialNumber + " - Unknown Printer " + printer.serialNumber + " Status"
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

    try:
        args = parser.parse_args()
    except:
        # Something didn't work. We will return an unknown.
        print(' invalid argument(s) {usage}'.format(usage=parser.format_usage()))
        sys.exit(3)

    print("<<<local>>>")
    evaluate_data(printers=get_data(connect=args.connect, user=args.user, password=args.password, limit=args.limit))


if __name__ == '__main__':
    main(sys.argv)