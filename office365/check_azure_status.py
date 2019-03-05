#!/usr/bin/python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# Azure Status check
# 22.02.2019 by Roland Mueller

import sys
import argparse
import urllib.request
from lxml import etree
from html2text import html2text


class Service:
    def __init__(self, name, region, status):
        self.region = region
        self.name = name
        self.status = status


def get_data(zone="", regions_to_check=[], services_to_check=[], url=""):
    regions = {}
    services = {}
    
    service_states = []

    status_page = urllib.request.urlopen(url)

    data = etree.HTML(status_page.read().decode("utf8"))
    tables = data.xpath("//table[@data-zone-name='" + zone + "']")

    if tables == []:
        print("UNKNOWN - No data found for specified zone")
        sys.exit(3)

    # parse regions out of the table
    for i, head in enumerate(tables[0].xpath("//table[@data-zone-name='" + zone + "']/thead/tr/th")):
        region = html2text(etree.tostring(head, method="text").decode("utf-8")).strip()
        if region in regions_to_check:
            regions[i] = region

    # get states of each services
    for i, row in enumerate(tables[1].xpath("//table[@data-zone-name='" + zone + "']/tbody/tr")):
        for j, service in enumerate(row):
            if j == 0:
                # check if services should be checked
                service = html2text(etree.tostring(row[0], method="text").decode("utf-8")).strip()
                if service in services_to_check:
                    services[i] = service
            else:
                # check if region is should be checked and if get status
                status = html2text(etree.tostring(service, method="text").decode("utf-8")).strip()
                if i in services and j in regions and status != "Blank":
                    service_states.append(Service(name = services[i], region = regions[j], status = status))
    
    return service_states

def evaluate_data(service_states=[]):
    good = 0
    information = 0
    warning = 0
    error = 0
    unknown = 0

    message = ""

    # count state of services
    for status in service_states:
        if status.status == "Good":
            good += 1
        elif status.status == "Information":
            information += 1
        elif status.status == "Warning":
            warning += 1
            message += " " + status.name + "(!)"
        elif status.status == "Error":
            error += 1
            message += " " + status.name + "(!!)"
        else:
            unknown += 1
            message += " " + status.name

        #print(status.name, status.region, status.status)

    # add performance data and return exit state
    message += " " + str(good+information) + " Services OK | ok=" + str(good) + "; information=" + str(information) + "; warning=" + str(warning) + "; error=" + str(error) + "; unknown=" + str(unknown) + ";"
    if error > 0:
        return(2, "CRITICAL -" + message)
    elif warning > 0:
        return(1, "WARNING -" + message)
    elif unknown > 0:
        return(3, "UNKNOWN -" + message)
    else:
        return(0, "OK -" + message)


def main(argv=None):
    description = """Check to parse the Microsoft Azure Status page
    Use this script with --regions and --services in a comma separated list,
    see the Microsoft Status Page for names https://azure.microsoft.com/en-us/status/
    eg. ./check_azure_status.py --regions 'Non-Regional*, North Europe, West Europe' --services 'Azure DNS, Storage' """
    
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-z', '--zone', dest='zone',
                         help='zone which regions located',
                         action='store',
                         required=True)

    parser.add_argument('-r', '--regions', dest='regions',
                         help='regions which should be checked for the provided serivces, provide a comma separated list',
                         action='store',
                         required=True)

    parser.add_argument('-s', '--services', dest='services',
                         help='serivces which should be checked, provide a comma separated list',
                         action='store',
                         required=True)

    parser.add_argument('-u', '--url', dest='url',
                            help='microsoft url for status page, might be used for localization',
                            action='store',
                            default='https://azure.microsoft.com/en-us/status/')

    try:
        args = parser.parse_args()
    except:
        # Something didn't work. We will return an unknown.
        print(' invalid argument(s) {usage}'.format(usage=parser.format_usage()))
        sys.exit(3)


    # parse microsoft page and create specific services
    regions = [r.strip() for r in args.regions.split(',')]
    services = [s.strip() for s in args.services.split(',')]
    service_states = get_data(zone=args.zone.lower(), regions_to_check=regions, services_to_check=services, url=args.url)

    # get the result of the data
    code, message = evaluate_data(service_states)

    print(message)
    sys.exit(code)


if __name__ == '__main__':
    main(sys.argv)