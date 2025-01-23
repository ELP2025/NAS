from pprint import pprint
import ipaddress
import argparse
import json
import yaml
import re 

def load_intent_file(filename):
    """Loading the file as a Python dict object. Compatible with yaml and  json"""
    with open(filename, 'r') as intent_file:
        if (filename.split('.')[-1] == 'json') :
            data = json.load(intent_file)
        elif (filename.split('.')[-1] == 'yaml' or 'yml'):
              data = yaml.safe_load(intent_file)
    return data

def argument_parser():
    parser = argparse.ArgumentParser(description='''Projet GNS3 2024-2025 -- Génération automatisé de configurations CISCO''')
    parser.add_argument('filename', help="Intent file describing the network that needs to be configured. YAML and JSON are supported")
    parser.add_argument('-g', '--generate_config',action='store_true', help="Generate config files and store them to the current directory")
    parser.add_argument('-c', '--copy_config', action='store_true', help="Generate config files and copy them to the right GNS3 directory")
    parser.add_argument('-t', '--telnet', action='store_true', help="Automatically configures the routers using Telnet")
    return parser.parse_args()

def get_as_data(data, as_number):
    """Function to extract AS data from data"""
    return data.get(f'AS{as_number}', {})[0]

def get_all_as_subnets(as_data):
    """Function that returns all the available subnets for an AS"""
    network = ipaddress.ip_network(f"{as_data.get('IPv6_prefix')}/{as_data.get('IPv6_mask')}")
    networks = iter(network.subnets(new_prefix=64))
    return networks

def get_routers_internal_interface_ip(as_data):
    """Returns routers ips for each interface"""
    routers = {r.get('hostname', ''):{} for r in as_data.get('routers', {})} #Getting all the routers in the AS
    connections = as_data.get('internal_connections', {})     # Getting all the connections
    subnets = get_all_as_subnets(as_data)
    subnet = next(subnets)
    for c in connections :
        # Gathering all the data we need
        first_peer = routers.get(c.get('first_peer_hostname', None))
        first_interface = c.get('first_peer_interface', None)
        second_peer = routers.get(c.get('second_peer_hostname', None))
        second_interface = c.get('second_peer_interface', None)
       
        # Error checking
        if first_peer.get(first_interface, None) : raise Exception(f'Intent file error : interface {first_interface} for router {c.get('first_peer_hostname', None)} is already in use')
        if second_peer.get(second_interface, None) : raise Exception(f'Intent file error : interface {second_interface} for router {c.get('second_peer_hostname', None)} is already in use')
       
        subnets_ip = subnet.hosts()

        routers[c.get('first_peer_hostname', '')].update({c.get('first_peer_interface', '') : str(next(subnets_ip))})
        routers[c.get('second_peer_hostname', '')].update({c.get('second_peer_interface', '') : str(next(subnets_ip))})
        

        subnet = next(subnets) 
    return routers, subnets

def get_routers_external_interfaces_ip(external_connections_data, routers, iters):
    """Returns routers ips for each interface, including external connections"""
    for connection in external_connections_data:
        subnet = next(iters[connection.get('AS_1')])
        # Getting all the connection details
        first_peer = connection.get('AS_1_router_hostname', {})
        first_interface = connection.get('AS_1_router_interface', {})
        second_peer = connection.get('AS_2_router_hostname', {})
        second_interface = connection.get('AS_2_router_interface', {})

        # Error Checking
        if routers.get(first_peer, {}).get(first_interface, None) : raise Exception(f'Intent file error : interface {first_interface} for router {first_peer} is already in use')
        if routers.get(second_peer, {}).get(second_interface, None) : raise Exception(f'Intent file error : interface {second_interface} for router {second_peer} is already in use')

        subnet_ip = subnet.hosts()

        routers.get(first_peer, {}).update({first_interface : str(next(subnet_ip))})
        routers.get(second_peer, {}).update({second_interface : str(next(subnet_ip))})
    return routers   

if __name__ == "__main__" :
    #try:
        args = argument_parser()
        data = load_intent_file(args.filename)
        as_data = dict()
        routers_data = dict()
        subnets_iters = dict()
        for as_name_string in [key for key, val in data.items() if "AS" in key]:
            as_name = int(re.findall(r'\d+', as_name_string)[0])
            as_data[as_name] = get_as_data(data, as_name)
            routers_data_as, subnets_iter_as = get_routers_internal_interface_ip(as_data[as_name])
            routers_data.update(routers_data_as)
            subnets_iters[as_data[as_name].get('number')] = subnets_iter_as
        routers_data = get_routers_external_interfaces_ip(data.get("BGP_connections", {}), routers_data, subnets_iters)
        pprint(routers_data)    
#except Exception as e:
    #    print(e)
