from pprint import pprint
import ipaddress
import argparse
import json
import yaml

def load_intent_file(filename) :
    """Loading the file as a Python dict object. Compatible with yaml and  json"""
    with open(filename, 'r') as intent_file:
        if (filename.split('.')[-1] == 'json') :
            data = json.load(intent_file)
        elif (filename.split('.')[-1] == 'yaml' or 'yml'):
              data = yaml.safe_load(intent_file)
    return data

def get_as_data(data, as_number):
    """Function to extract AS data from data"""
    return data.get(f'AS{as_number}', {})

def get_all_as_subnets(as_data):
    """Function that returns all the available subnets for an AS"""
    network = ipaddress.ip_network(f"{as_data[0].get('IPv6_prefix')}/{as_data[0].get('IPv6_mask')}")
    networks = iter([network.subnets(new_prefix=64)])
    print(next(networks))
    

def get_as_routers_data(as_data):
    return as_data.get('routers', {})


if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description='''Projet GNS3 2024-2025 -- Génération automatisé de configurations CISCO''')
    parser.add_argument('filename', help="Intent file describing the network that needs to be configured. YAML and JSON are supported")
    parser.add_argument('-g', '--generate_config',action='store_true', help="Generate config files and store them to the current directory")
    parser.add_argument('-c', '--copy_config', action='store_true', help="Generate config files and copy them to the right GNS3 directory")
    parser.add_argument('-t', '--telnet', action='store_true', help="Automatically configures the routers using Telnet")
    args=parser.parse_args()
    data = load_intent_file(args.filename)
    data = get_as_data(data, 1)
    get_all_as_subnets(data)
