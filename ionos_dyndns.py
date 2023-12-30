#!/usr/bin/env python3

# Author: Lázaro Blanc
# GitHub: https://github.com/lazaroblanc
# Usage example: ./ionos_dyndns.py --A --AAAA --api-prefix <api_prefix> --api-secret <api_secret>

import subprocess  # Getting IPv6 address from systools instead of via web API
import re  # Just regex stuff
import requests  # Talk to the API
import json  # Work with the API responses
from argparse import ArgumentParser, RawDescriptionHelpFormatter  # Commandline argument parsing

import sys
import logging
logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(message)s", datefmt="%B %d %H:%M:%S", level=logging.INFO)

def parse_cmdline_args():
    argparser = ArgumentParser(
        description="Create and update DNS records for this host using IONOS' API to use as a sort of DynDNS (for example via a cronjob).",
        epilog="Author: Lázaro Blanc\nGitHub: https://github.com/lazaroblanc",
        formatter_class=RawDescriptionHelpFormatter
    )
    argparser.add_argument(
        "-4", "--A",
        default=False,
        action="store_const",
        const=True,
        help="Create/Update A record"
    )
    argparser.add_argument(
        "-6", "--AAAA",
        default=False,
        action="store_const",
        const=True,
        help="Create/Update AAAA record"
    )
    argparser.add_argument(
        "-i", "--interface",
        default="eth0",
        action="store",
        metavar="",
        help="Interface name for determining the public IPv6 address (Default: eth0)"
    )
    argparser.add_argument(
        "-H", "--fqdn",
        default=subprocess.getoutput(f"hostname -f"),
        action="store",
        metavar="",
        help="Host's FQDN (Default: hostname -f)"
    )
    argparser.add_argument(
        "--api-prefix",
        required=True,
        action="store",
        metavar="",
        help="API key publicprefix"
    )
    argparser.add_argument(
        "--api-secret",
        required=True,
        action="store",
        metavar="",
        help="API key secret"
    )

    args = argparser.parse_args()

    if not args.A and not args.AAAA:
        argparser.print_help()
        exit()

    return args


# Map args to global variables
args = parse_cmdline_args()
fqdn = args.fqdn.lower()
api_url = "https://api.hosting.ionos.com/dns/v1/zones"
api_key_publicprefix = args.api_prefix
api_key_secret = args.api_secret
api_headers = {
    "accept": "application/json",
    "X-API-Key": f"{api_key_publicprefix}.{api_key_secret}"
}
interface = args.interface


def main():

    domain = get_domain_from_fqdn(fqdn)
    zone = get_zone(domain)
    all_records = get_all_records_for_fqdn(zone["id"], fqdn)
    records_to_create = []
    records_to_update = []

    # Code duplication. Could use some refactoring but I don't have time for this atm
    if args.A:
        ipv4_address = get_ipv4_address()
        logging.info("Public IPv4: " + ipv4_address)
        if filter_records_by_type(all_records, "A"):
            if filter_records_by_type(all_records, "A")[0]["content"] == ipv4_address:
                logging.info("A record is up-to-date")
            else:
                logging.info("A record is outdated")
                records_to_update.append(
                    new_record(fqdn, "A", ipv4_address, 60))
        else:
            logging.info("No A record found")
            records_to_create.append(new_record(fqdn, "A", ipv4_address, 60))

    # Good god this is ugly. I hate myself for writing this. This really needs refactoring...
    if args.AAAA:
        ipv6_address = get_ipv6_address(interface)
        if ipv6_address != "":
            logging.info("Public IPv6: " + ipv6_address)
            if filter_records_by_type(all_records, "AAAA"):
                if filter_records_by_type(all_records, "AAAA")[0]["content"] == ipv6_address:
                    logging.info("AAAA record is up-to-date")
                else:
                    logging.info("AAAA record is outdated")
                    records_to_update.append(new_record(
                        fqdn, "AAAA", ipv6_address, 60))
            else:
                logging.info("No AAAA record found")
                records_to_create.append(new_record(
                    fqdn, "AAAA", ipv6_address, 60))
        else:
            logging.info("Could not find a public IPv6 address on this system")

    if (len(records_to_create) > 0):
        post_new_records(zone["id"], records_to_create)

    if (len(records_to_update) > 0):
        patch_records(zone["id"], records_to_update)


def get_domain_from_fqdn(fqdn):
    # Place the hyphen at the start of the character class to avoid misinterpretation
    regex = r"(?:(?:[\w-]+)\.)?([\w-]+\.\w+)$"
    match = re.search(regex, fqdn, re.IGNORECASE)
    return match.group(1) if match else None


def get_ipv4_address():
    return requests.request("GET", "https://api4.ipify.org").text


def get_ipv6_address(interface_name):
    ip_output = subprocess.getoutput(f"ip -6 -o address show dev {interface_name} scope global | grep --invert temporary | grep --invert mngtmpaddr")
    if ip_output != "":
        ip_output_regex = r"(?:inet6)(?:\s+)(.+)(?:\/\d{1,3})"
        return re.search(ip_output_regex, ip_output, re.IGNORECASE).group(1)
    else:
        return ""


def get_zone(domain):
    response = json.loads(requests.request(
        "GET", api_url, headers=api_headers).text)
    return list(filter(lambda zone: zone['name'] == domain, response))[0]


def get_all_records_for_fqdn(zone_id, host):
    url = f"{api_url}/{zone_id}"
    records = json.loads(requests.request("GET", url, headers=api_headers).text)['records']
    return list(filter(lambda record: record['name'] == host, records))


def filter_records_by_type(records, type):
    return list(filter(lambda record: record['type'] == type, records))


def new_record(name, record_type, ip_address, ttl):
    return {
        "name": name,
        "type": record_type,
        "content": ip_address,
        "ttl": ttl
    }


def post_new_records(zone_id, records):
    url = f"{api_url}/{zone_id}/records"
    return requests.request("POST", url, headers=api_headers, json=records)


def patch_records(zone_id, records):
    url = f"{api_url}/{zone_id}"
    return requests.request("PATCH", url, headers=api_headers, json=records)


main()
