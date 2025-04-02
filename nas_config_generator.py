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

def get_external_ips(routers_dict, data, as_subnets):
     for connection in data.get("AS_connections", []):
        subnet = next(as_subnets[int(connection["AS_1"]) if int(connection["AS_1"]) < int(connection["AS_2"]) else int(connection["AS_2"])])

        subnet_ips = subnet.hosts()
        first_ip = str(next(subnet_ips)) +' 255.255.255.252'
        second_ip = str(next(subnet_ips)) + ' 255.255.255.252'

        routers_dict[connection["AS_1_router_hostname"]]['interfaces'][connection["AS_1_router_interface"]] = first_ip
        routers_dict[connection["AS_2_router_hostname"]]['interfaces'][connection["AS_2_router_interface"]] = second_ip
    
def get_ibgp_neighbors(routers_dict, data):
    for connection in data.get("internal_connections", []):
        first_peer_loopback_ip = routers_dict[connection['first_peer_hostname']]['interfaces']['loopback0'].split(' ')[0]
        second_peer_loopback_ip = routers_dict[connection['second_peer_hostname']]['interfaces']['loopback0'].split(' ')[0]
        
        routers_dict[connection['first_peer_hostname']]['bgp_neighbors'].append((second_peer_loopback_ip, False))
        routers_dict[connection['second_peer_hostname']]['bgp_neighbors'].append((first_peer_loopback_ip, False))

def get_ebgp_neighbors(routers_dict, data):
    for connection in data.get("AS_connections", []):
        if connection["connexion"][0]["type"] == 'BGP':
            first_peer_ip = routers_dict[connection["AS_1_router_hostname"]]["interfaces"][connection["AS_1_router_interface"]].split(' ')[0]
            second_peer_ip = routers_dict[connection["AS_2_router_hostname"]]["interfaces"][connection["AS_2_router_interface"]].split(' ')[0]

            routers_dict[connection["AS_1_router_hostname"]]['bgp_neighbors'].append((first_peer_ip, True))
            routers_dict[connection["AS_2_router_hostname"]]['bgp_neighbors'].append((second_peer_ip, True))

def get_routers_dict(data):
    """Convert the intent file into a super useful dict for our project, very fancy :tm:"""
    routers = dict()
    as_subnets = dict()
    for as_name_string in [key for key, _ in data.items() if "AS_" not in key]: # Find all the AS
        as_data = data.get(as_name_string, {})[0]
        as_number = int(as_data.get("number"))

        for router in as_data.get("routers",[]):

            hostname = router.get("hostname")
            telnet_port = int(router.get("telnet_port"))
            num_creation = int(router.get("num_creation"))
            routers[hostname] = {"as_number" : as_number, "num_creation" : num_creation ,"telnet_port" : telnet_port, "interfaces" : {}, 'bgp_neighbors' : []}
        
        as_subnets[as_number] = get_internal_ips(routers, as_data)
        get_loopback_ips(routers, as_data)
        get_ibgp_neighbors(routers, as_data)
    get_external_ips(routers, data, as_subnets)
    get_ebgp_neighbors(routers, data)
    return routers

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
    config.append(f"hostname {hostname}")
    config.append("!")
    config.append("!")
    return "\n".join(config)

def config_interfaces(valeurs, num_as):
    """
    Génère une configuration pour les interfaces d'un routeur.

    :param valeurs: Dictionnaire des interfaces avec leurs adresses IP
    :return: Chaîne de texte représentant la configuration des interfaces
    """
    config = []
    
# Configuration des interfaces
    for interface, ip in valeurs.items():
        config.append(f"interface {interface}")
        config.append(f" ip address {ip}")
        config.append (f" ip ospf {num_as} area 0")
        config.append("!")

    return "\n".join(config)

def bgp_add(bgp_config, num, num_as, network, border_routers, router):
    """
    Génère la configuration BGP pour un routeur Cisco.

    :param bgp_config: Dictionnaire contenant les informations BGP (AS et voisins)
    :param num: Numéro du routeur (extrait du nom du routeur)
    :return: Chaîne de texte représentant la configuration BGP
    """
    config = []
    # Configuration du BGP
    config.append(f"router bgp {num_as}")
    config.append(f" bgp router-id {num}.{num}.{num}.{num}")
    config.append(" bgp log-neighbor-changes")
    for neighbor in bgp_config[f"{router}"]:
        print (neighbor)
        config.append(f" neighbor {neighbor[0]} remote-as {neighbor[1]}")
        if neighbor[2]:
            config.append(f" neighbor {neighbor[0]} update-source Loopback0")
        else :
            config.append(f" neighbor {neighbor[0]} route-map {neighbor[3].upper()} in")
    config.append(" !\n address-family ipv4")
    for border_router in border_routers:
        if f"{router}" in border_router[0]:
            for key, ip_value in network.items():
                if key[0] == num_as:
                    config.append(f"  network {ip_value}")
    for neighbor in bgp_config[f"R{num}"]:
        config.append(f"  neighbor {neighbor[0]} next-hop-self")
        config.append(f"  neighbor {neighbor[0]} activate")
        config.append(f"  neighbor {neighbor[0]} send-community both")
    config.append(" exit-address-family")
    config.append("!")
    return "\n".join(config)

def add_protocol(num, num_as, border_routers):
    config = []
    
    config.append(f"ip router ospf {num_as}")
    config.append(f" router-id {num}.{num}.{num}.{num}")
    for router in border_routers:
        if f"R{num}" == router[0]:
            config.append(f" passive-interface {router[1]}")
                 
    return "\n".join(config)


def generate_config_file(router, info):
    num_as = info["as_number"]
    num_creat = info["num_creation"]
    file_name = f"i{num_creat}_startup-config.cfg"
    with open(file_name, 'w') as file:
        file.write(generate_base_cisco_config(router))
        file.write("\n" + config_interfaces(info["interfaces"], num_as))
        #file.write("\n" + bgp_add(info["routers_bgp"], num_creat, num_as, info["router_network"], info["border_routers"], router))
        #file.write("\n" + add_protocol(num_creat, num_as , info["border_routers"]))
    print(f"Configuration pour le router {router} terminée")
# END OF CONFIG



if __name__ == "__main__":
        args = argument_parser()
        data = load_intent_file(args.filename)
        routers_info = get_routers_dict(data)
        pprint(routers_info)
        for router, info in routers_info.items():
            generate_config_file(router, info)
        #if args.copy_config :
         #   configurator = FileDispatcher(args.copy_config)
          #  configurator.copy_configs()

