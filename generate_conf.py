from file_dispatcher import FileDispatcher
from telnet import TelnetConfigurator 
from pprint import pprint
import ipaddress
import argparse
import json
import yaml
import re 

# START OF GETTER FUNCTIONS
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
    parser.add_argument('-c', '--copy_config', help="Generate config files and copy them to the specified GNS3 directory")
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

def map_routers_to_as_and_protocol(data):
    """
    Associe chaque routeur à son numéro d'AS et son protocole.

    :param data : contenu du fichier d'intention sous forme de dictionnaire 
    :return: Dictionnaire avec les routeurs comme clés, et les numéros d'AS et protocoles comme valeurs
    """
    router_mapping = {}
    for as_key, as_values in data.items():
        for as_entry in as_values:
            as_number = as_entry.get('number')
            protocol = as_entry.get('IGP')
            for router in as_entry.get('routers', []):
                router_name = router['hostname']
                router_mapping[router_name] = {"AS_number": as_number, "protocol": protocol}
    return router_mapping
# END OF GETTER FUNCTIONS

# START OF NETWORK ADDRESSING
def generate_routers_loopback_ips(routers, as_prefix):
    """Returns the loopback adress for each router"""
    if not as_prefix : raise Exception(f'Intent file error : at least one AS does not have an IPv6 Prefix')
    for router in routers:
        routers[router].update({'loopback0' : f'{as_prefix[:-1]}9999:{str(router)[1:]}::{str(router)[1:]}/128'})
    return routers

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

        routers[c.get('first_peer_hostname', '')].update({c.get('first_peer_interface', '') : str(next(subnets_ip))+'/64'})
        routers[c.get('second_peer_hostname', '')].update({c.get('second_peer_interface', '') : str(next(subnets_ip))+'/64'})
        

        subnet = next(subnets)
    routers = generate_routers_loopback_ips(routers, as_data.get('IPv6_prefix'))
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

        routers.get(first_peer, {}).update({first_interface : str(next(subnet_ip))+'/64'})
        routers.get(second_peer, {}).update({second_interface : str(next(subnet_ip))+'/64'})
    return routers   
# END OF NETWORK ADDRESSING

#START OF CONFIG
def generate_base_cisco_config(hostname):
    """
    Génère une configuration de base pour un routeur Cisco.

    :param hostname: Nom d'hôte du routeur (hostname)
    :return: Chaîne de texte représentant la configuration de base
    """
    config = []
    
    # Configuration de base
    config.append("service timestamps debug datetime msec")
    config.append("service timestamps log datetime msec")
    config.append("!")
    config.append(f"hostname R{hostname}")
    config.append("!")
    config.append("ipv6 unicast-routing")
    config.append("!")
    return "\n".join(config)

def config_interfaces(valeurs, dico_protocoles, routeur):
    """
    Génère une configuration pour les interfaces d'un routeur.

    :param valeurs: Dictionnaire des interfaces avec leurs adresses IP
    :return: Chaîne de texte représentant la configuration des interfaces
    """
    config = []
    full_name = f"R{routeur}"
    
# Configuration des interfaces
    for interface, ip in valeurs[full_name].items():
        config.append(f"interface {interface}")
        config.append(" no ip address")
        config.append(" ipv6 enable")
        config.append(f" ipv6 address {ip}")
        if dico_protocoles[full_name]["protocol"] == 'RIP':
            num_as = dico_protocoles[full_name]['AS_number']
            config.append (f" ipv6 rip RIP_AS_{num_as} enable")
        elif dico_protocoles[full_name]["protocol"] == 'OSPF':
            num_as = dico_protocoles[full_name]['AS_number']
            config.append (f" ipv6 ospf {num_as} area 0")
        config.append("!")

    return "\n".join(config)

def bgp_add(bgp_config, num):
    """
    Génère la configuration BGP pour un routeur Cisco.

    :param bgp_config: Dictionnaire contenant les informations BGP (AS et voisins)
    :param num: Numéro du routeur (extrait du nom du routeur)
    :return: Chaîne de texte représentant la configuration BGP
    """
    config = []
    
    # Configuration du BGP
    config.append(f"router bgp {bgp_config['AS']}")
    config.append(f" bgp router-id {num}.{num}.{num}.{num}")
    config.append(" bgp log-neighbor-changes\n no bgp default ipv4-unicast")
    for neighbor in bgp_config["neighbors"].values():
        config.append(f" neighbor {neighbor[0]} remote-as {neighbor[1]}")
    config.append(" !\n address-family ipv4\n exit-address-family\n !\n address-family ipv6")
    for neighbor in bgp_config["neighbors"].values():
        config.append(f"  neighbor {neighbor[0]} activate")
    config.append(" exit-address-family")
    config.append("!")
    return "\n".join(config)

def add_protocol(num, dico_protocoles):
    config = []
    
    #configuration du protocole routeur*
    if dico_protocoles["protocol"] == 'RIP':
        num_as = dico_protocoles['AS_number']
        config.append (f"ipv6 router rip RIP_AS_{num_as}")
        config.append (" redistribute connected")
    elif dico_protocoles["protocol"] == 'OSPF':
        num_as = dico_protocoles['AS_number']
        config.append (f"ipv6 router ospf {num_as}")
        config.append (f"router-id {num}.{num}.{num}.{num}")
    return "\n".join(config)

def generate_config_file(hostname, interface_data, router_mapping, bgp_data):
    file_name = f"i{hostname}_startup_config.cfg"
    with open(file_name, 'w') as file:
        file.write(generate_base_cisco_config(hostname))
        file.write("\n" + config_interfaces(interface_data, router_mapping, hostname))
        file.write("\n" + bgp_add(bgp_data, hostname))
        file.write("\n" + add_protocol(hostname, router_mapping[f"R{hostname}"]))
    print(f"Configuration pour le router {hostname} terminée")
# END OF CONFIG

if __name__ == "__main__" :
    try:
        args = argument_parser()
        data = load_intent_file(args.filename) # Loading data

        if args.copy_config and args.telnet : raise Exception("You should not copy and telnet the same config file, this is nonsense.")
        
        # Getting all the IPS for all the routers (interal IP(igp) and external IP(bgp))
        as_data = dict()
        routers_data = dict()
        subnets_iters = dict()
        for as_name_string in [key for key, _ in data.items() if "AS" in key]:
            as_name = int(re.findall(r'\d+', as_name_string)[0])
            as_data[as_name] = get_as_data(data, as_name)
            routers_data_as, subnets_iter_as = get_routers_internal_interface_ip(as_data[as_name])
            routers_data.update(routers_data_as)
            subnets_iters[as_data[as_name].get('number')] = subnets_iter_as
        routers_data = get_routers_external_interfaces_ip(data.get("BGP_connections", {}), routers_data, subnets_iters)
 
        # Mapping each router to it's AS and IGP
        router_mapping = map_routers_to_as_and_protocol(data)
        bgp_config = {
                "AS": 2000,
                "neighbors": {
                    "neighbor": ["2000:200:200:56::1", "2000"],
                    "neighbor_2": ["2000:200:200:67::1", "2000"]
                }
            }

        for router in routers_data:
            generate_config_file(router[1:], routers_data, router_mapping, bgp_config)

        if args.copy_config :
            configurator = FileDispatcher(args.copy_config)
            configurator.copy_configs()

        if args.telnet : 
            pass 
            #TODO : GET every router telnet port and copy the config file there

    except Exception as e:
        print(e)
