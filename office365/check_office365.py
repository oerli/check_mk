#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# Office 365 Status check
# 01.12.2018 by Roland Mueller
#
'''
check_office365 - A simple Nagios plugin to check an Office 365 status.
Created to monitor status of cloud services.

Requires json and argparse python libraries.
Possible Checks [Outlook.com, OneDrive, Yammer.com, Microsoft To-Do] Eg.:
/usr/local/bin/check_office365.py -H https://portal.office.com/api/servicestatus/index -S Outlook.com

'''

import sys
import argparse
import json
import time
from urllib2 import Request, urlopen

def fetch_json(feed_url, service):
    '''Fetch a feed from a given string'''

    try:
        start = time.time()
        request = Request(feed_url)
        request.add_header("Accept", "application/json")
        response = urlopen(request)
        end = time.time()
        myfeed = json.loads(response.read())
    except:
        output = 'Could not parse URL (%s)' % feed_url
        exitcritical(output, 0, 0)

    for item in myfeed["Services"]:
        if item["Name"] == service:
            return item, response.headers["content-length"], end - start

    output = 'Service (%s) not found' % service
    exitcritical(output, response.headers["content-length"], end - start)

def main(argv=None):
    """Gather user input and start the check """
    description = "A simple Nagios plugin to check an Office 365 service status."
    epilog = """notes: If you do not specify any warning or
 critical conditions, it will always return OK.
 This will only check the newest feed entry."""

    version = '0.1'

    # Set up our arguments
    parser = argparse.ArgumentParser(description=description,
                                  epilog=epilog)

    parser.add_argument('--version', action='version', version=version)

    parser.add_argument('-H', dest='url',
                         help='URL to monitor',
                         action='store',
                         required=True)

    parser.add_argument('-S', dest='service',
                         help='Service name to monitor',
                         action='store',
                         required=True)

    parser.add_argument('-v', '--verbosity', dest='verbosity',
                         help='Verbosity level. 0 = Only the title and time is returned. '
                         '1 = Title, time and link are returned. '
                         '2 = Title, time, link and description are returned (Default)',
                         action='store',
                         default='2')

    try:
        args = parser.parse_args()
    except:
        # Something didn't work. We will return an unknown.
        output = ': Invalid argument(s) {usage}'.format(usage=parser.format_usage())
        exitunknown(output, 0, 0)

    # Parse our feed, getting title, description and link of newest entry.
    url = args.url
    if (url.find('http://') != 0 and url.find('https://') != 0):
        url = 'http://{url}'.format(url=url)

    service = args.service
    # we have everything we need, let's start 
    service_status, size, time = fetch_json(url, service)
    
    output = service_status["Name"]
    if service_status["Messages"] != None:
        output = output + " - " + str(service_status["Messages"])

    if service_status["IsUp"] == True:
        exitok(output, size, time)
    else:
        exitcritical(output, size, time)

def exitok(output, size, time):
    print 'OK - %s' % output + ' | time=' + str(time) + ';;;0.000000 size=' + str(size) + 'B;;;0'
    sys.exit(0)

def exitcritical(output, size, time):
    print 'CRITICAL - %s' % output + ' | time=' + str(time) + ';;;0.000000 size=' + str(size) + 'B;;;0'
    sys.exit(2)

def exitunknown(output):
    sys.exit(3)

if __name__ == '__main__':
    result = main(sys.argv)
    sys.exit(result)

