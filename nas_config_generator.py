from pprint import pprint 
import ipaddress
import argparse
import json
import yaml

# FILE INTERACTION AND USER INTERACTION
def argument_parser():
    parser = argparse.ArgumentParser(description='''Projet NAS 2024-2025 -- Génération automatisé de configurations CISCO avec support BGP/MPLS VPN''')
    parser.add_argument('filename', help="Intent file describing the network that needs to be configured. YAML and JSON are supported")
    parser.add_argument('-c', '--copy_config', help="Generate config files and copy them to the specified GNS3 directory")
    parser.add_argument('-t', '--telnet', action='store_true', help="Automatically configures the routers using Telnet")
    return parser.parse_args()

def load_intent_file(filename):
    """Loading the file as a Python dict object. Compatible with yaml and  json"""
    with open(filename, 'r') as intent_file:
        if (filename.split('.')[-1] == 'json') :
            data = json.load(intent_file)
        elif (filename.split('.')[-1] == 'yaml' or 'yml'):
              data = yaml.safe_load(intent_file)
    return data

# UTILS FUNCTIONS
def get_all_as_subnets(prefix, mask):
    """Function that returns all the available subnets for an AS"""
    network = ipaddress.ip_network(f"{prefix}/{mask}")
    networks = iter(network.subnets(new_prefix=30))
    return networks

def get_loopback_subnet(prefix, mask):
    """Function to retrieve the loopback subnet for an AS"""
    network = ipaddress.ip_network(f"{prefix}/{mask}")
    # WARNING : Dark magic below, see here : https://stackoverflow.com/questions/2138873/cleanest-way-to-get-last-item-from-python-iterator
    *_, last = iter(network.subnets(new_prefix=24))
    return iter(last.subnets(new_prefix=32))

def get_internal_ips(routers_dict, as_data):
    """Generate the ip for internal connections in an AS"""
    as_subnets = get_all_as_subnets(as_data.get("IPv4_prefix"), as_data.get("IPv4_mask"))
    current_subnet = next(as_subnets)
    for internal in as_data.get("internal_connections", {}):
        # Getting all the data
        first_peer = routers_dict.get(internal.get('first_peer_hostname', None))
        first_interface = internal.get('first_peer_interface', None)
        second_peer = routers_dict.get(internal.get('second_peer_hostname', None))
        second_interface = internal.get('second_peer_interface', None)

        # Error checking
        if first_peer["interfaces"].get(first_interface, None) : raise Exception(f'Intent file error : interface {first_interface} for router {internal.get('first_peer_hostname', None)} is already in use')
        if second_peer["interfaces"].get(second_interface, None) : raise Exception(f'Intent file error : interface {second_interface} for router {internal.get('second_peer_hostname', None)} is already in use')
       
        subnet_ips = current_subnet.hosts()
        first_ip = str(next(subnet_ips)) + ' 255.255.255.252'
        second_ip = str(next(subnet_ips)) + ' 255.255.255.252'
    
        first_peer["interfaces"][first_interface] = first_ip
        second_peer["interfaces"][second_interface] = second_ip
           
        current_subnet = next(as_subnets)

    return as_subnets 

def get_loopback_ips(routers_dict, as_data):
    loopback_subnets = get_loopback_subnet(as_data.get("IPv4_prefix"), as_data.get("IPv4_mask"))
    current_subnet = next(loopback_subnets)

    for hostname, router_data in routers_dict.items():
        if int(router_data["as_number"]) != int(as_data["number"]) : continue
        ip = str(current_subnet.hosts()[0]) + ' 255.255.255.255'
        routers_dict[hostname]["interfaces"]["loopback0"] = ip

        current_subnet = next(loopback_subnets)
        

def get_routers_dict(data):
    """Convert the intent file into a super useful dict for our project, very fancy :tm:"""
    routers = dict()
    for as_name_string in [key for key, _ in data.items() if "AS" in key]: # Find all the AS
        as_data = data.get(as_name_string, {})[0]
        as_number = int(as_data.get("number"))

        for router in as_data.get("routers",[]):

            hostname = router.get("hostname")
            telnet_port = int(router.get("telnet_port"))
            routers[hostname] = {"as_number" : as_number, "telnet_port" : telnet_port, "interfaces" : {}}
        
        get_internal_ips(routers, as_data)
        get_loopback_ips(routers, as_data)
    return routers


if __name__ == "__main__":
        args = argument_parser()
        data = load_intent_file(args.filename)
        print(get_routers_dict(data)) 
