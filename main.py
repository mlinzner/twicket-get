import requests
import argparse
import logging
import json
from time import sleep
import pyprowl
import sys

api_key="83d6ec0c-54bb-4da3-b2a1-f3cb47b984f1"
s = requests.Session()
p = pyprowl.Prowl('8da97a64ad222fcfb6129a93d74c018927ba83fe')

parser = argparse.ArgumentParser(prog='twicket-get', description='Snag yer tickets.')
parser.add_argument('-u', '--user', help='The username used for Twickets', required=True)
parser.add_argument('-p', '--password', help='The password used for Twickets', required=True)
parser.add_argument('-e', '--event-id', help='Unique identifier for Twickets event', required=True)
parser.add_argument('-t', '--time-delay', help='Time delay for availability polling (in seconds), default: 2s', type=float ,required=False)
args = parser.parse_args()


def get_ticket_avail(inventory_id, seats):
    url = 'https://www.twickets.live/services/inventory/' + str(inventory_id) + '?api_key=' + api_key + '&qty=' + str(seats)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0'}
    cookies = {'clientId': 'cf6de4c4-cca6-4425-b252-4c1360309a1c', 'territory': 'GB', 'locale': 'en_GB'}
    response = s.get(url=url, headers=headers)
    results = response.json()
    return results


def check_event_avail(event_id):
    url = 'https://www.twickets.live/services/g2/inventory/listings/' + str(event_id) + '?api_key=' + api_key
    headers = {}
    payload = {}
    cookies = {'clientId': 'cf6de4c4-cca6-4425-b252-4c1360309a1c', 'territory': 'GB', 'locale': 'en_GB'}
    response = s.get(url=url, headers=headers, data=payload, cookies=cookies)
    results = response.json()
    itineraries = list()

    if results['responseData']:
        count = 0
        for result in results['responseData']:
            #print(str(count), str(result['id']).split('@')[1], result['type'], result['section'], result['row'], str(result['pricing']['prices'][0]['netSellingPrice'] / 100))
            itineraries.append({'id': str(result['id']).split('@')[1], 'seats': str(result['splits'][0]),
                                'type': result['type'], 'area': result['area'], 'section': result['section'],
                                'row': result['row'], 'price': result['pricing']['prices'][0]['netSellingPrice'] / 100})
            count += 1
        return itineraries
    else:
        return None


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


def get_section(listing):
    return listing.get('section')

def perform_login(username, password):
    url = 'https://www.twickets.live/services/auth/login?api_key=' + api_key
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0',
               'content-type': 'application/json'}
    cookies = {'clientId': 'cf6de4c4-cca6-4425-b252-4c1360309a1c', 'territory': 'GB', 'locale': 'en_GB'}
    data = {"login": username, "password": password, "accountType": "U"}
    response = s.post(url=url, headers=headers, data=json.dumps(data), cookies=cookies)
    result = response.json()
    if result['responseData']:
        return result['responseData']
    else:
        return None


def request_hold(blockId, quantity, auth_token):
    url = 'https://www.twickets.live/services/bookings/hold?api_key=' + api_key
    data = {'blockId': blockId, 'qty': quantity}
    cookies = {'clientId': 'cf6de4c4-cca6-4425-b252-4c1360309a1c', 'territory': 'GB', 'locale': 'en_GB'}
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0',
               'content-type': 'application/json', 'Authorization': 'TOKEN ' + auth_token}
    response = s.post(url=url, data=json.dumps(data), cookies=cookies, headers=headers)
    result = response.json()
    if result['holdReference']:
        print(str(result['holdReference']))
        return {'holdReference': result['holdReference'], 'expires': result['expires']}
    else:
        print('holdReference empty. responseCode: ' + str(result['responseCode']))
        return None


def prebook(blockId, holdref, quantity, auth_token):
    url = 'https://www.twickets.live/services/bookings/prebook?api_key=' + api_key
    data = {'blockId': blockId, 'holdReference': holdref, 'qty': quantity, 'attendees': [], 'deliveryMethodId': 4,
            'buyerAddress': {"city": None, "line1": None, "line2": None, "recipientName": None, "postcode": None, "statecode": None},
            'paymentMethod': 0, 'buyerLocale': 'en_GB'}
    cookies = {'clientId': 'cf6de4c4-cca6-4425-b252-4c1360309a1c', 'territory': 'GB', 'locale': 'en_GB'}
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0',
               'content-type': 'application/json', 'Authorization': 'TOKEN ' + auth_token}
    response = s.post(url=url, data=json.dumps(data), cookies=cookies, headers=headers)
    result = response.json()
    if result['token']:
        print(str(result['token']), result['redirectUrl'])
        return {'token': result['token'], 'redirectUrl': result['redirectUrl'], 'invoiceNumber': result['invoiceNumber']}
    else:
        print('token empty. responseCode: ' + str(result['responseCode']))


if __name__ == '__main__':
    format = "%(levelname)s %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S", stream=sys.stdout)
    print("Starting")
    logging.info("Main       : Initialized")

    try:
        #check_event_avail(444082439103088)
        logging.info("Main       : Logging in...")
        authorization_token = perform_login(args.user, args.password)
        p.verify_key()
        p.notify(event='Twickets', description='Twicket loop started',
                 priority=0, url='https://www.twickets.live/event/1535073546361905152',
                 appName='twicket-get')
        logging.info("Main       : Entering main loop")
        while 1:
            #options = check_event_avail(1231881975082520576)
            options = check_event_avail(args.event_id)
            if options:
                logging.info("Main loop   : " + str(len(options)) + " options found")
                options.sort(key=get_section)
                while len(options) > 0:
                    current = options.pop(0)
                    # check if current is available to checkout
                    ticket = get_ticket_avail(current['id'], current['seats'])
                    if ticket['available'] and int(current['seats']) < 4:
                        # If deliveryMethod is defined and the setting is "Meet Up", pass
                        if int(ticket['deliveryPlan'][0]['deliveryMethod']):
                            if int(ticket['deliveryPlan'][0]['deliveryMethod']) == 1:
                                logging.warning("Main loop   : [Skipped] Delivery method was " + ticket['deliveryPlan'][0]['title'])
                                continue
                        hold_details = request_hold(ticket['block']['blockId'], current['seats'], authorization_token)
                        if hold_details:
                            print("Hold details: " + hold_details['holdReference'] + ": expires " + hold_details['expires'])
                            prebook_result = prebook(ticket['block']['blockId'], hold_details['holdReference'], current['seats'], authorization_token)
                            if prebook_result:
                                p.notify(event='Twickets', description='Prebooked: ' + str(current['section']) + ', ' + str(current['row']) + ', ' + str(current['price']),
                                         priority=0, url=prebook_result['redirectUrl'],
                                         appName='twicket-get')
                                logging.info("Main loop   : Prebooking success: https://www.twickets.live/block/" + str(ticket['block']['blockId']) + "," + str(current['seats']) + "\n" +
                                             prebook_result['redirectUrl'])
                            else:
                                logging.error("Main loop   : Prebooking failed: https://www.twickets.live/block/" + str(ticket['block']['blockId']) + "," + str(current['seats']))
                                p.notify(event='Twickets',
                                         description='Prebook failed: ' + str(current['section']) + ', ' + str(current['row']) + ', ' +
                                                     str(current['price']),
                                         priority=0, url="https://www.twickets.live/block/" + str(ticket['block']['blockId']) + "," + str(current['seats']),
                                         appName='twicket-get')
                        else:
                            print("Unable to hold ", str(current['id']), str(current['section']), str(current['row']))
                            #print('Ticket dump:')
                            #print(current, ticket)
                            continue
                    else:
                        print("Ticket unavailable")
            else:
                logging.info("Main loop  : No tickets found")
            if args.time_delay is not None:
                sleep(args.time_delay)
            else:
                sleep(2)


    except KeyboardInterrupt:
        print("\nExiting by user request.\n", file=sys.stderr)
        sys.exit(0)
