from pprint import pprint 
from file_dispatcher import  FileDispatcher
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
    is_mpls_as = as_data.get("mpls", False)
    for internal in as_data.get("internal_connections", {}):
        # Getting all the data
        first_peer = routers_dict.get(internal.get('first_peer_hostname', None))
        first_interface = internal.get('first_peer_interface', None)
        second_peer = routers_dict.get(internal.get('second_peer_hostname', None))
        second_interface = internal.get('second_peer_interface', None)

        first_peer["mpls"] = True
        second_peer["mpls"] = True

        # Error checking
        if first_peer["interfaces"].get(first_interface, None) : raise Exception(f'Intent file error : interface {first_interface} for router {internal.get('first_peer_hostname', None)} is already in use')
        if second_peer["interfaces"].get(second_interface, None) : raise Exception(f'Intent file error : interface {second_interface} for router {internal.get('second_peer_hostname', None)} is already in use')
       
        subnet_ips = current_subnet.hosts()
        first_ip = str(next(subnet_ips)) + ' 255.255.255.252'
        second_ip = str(next(subnet_ips)) + ' 255.255.255.252'
    
        first_peer["interfaces"][first_interface] = (first_ip, is_mpls_as, None)
        second_peer["interfaces"][second_interface] = (second_ip, is_mpls_as, None)
           
        current_subnet = next(as_subnets)

    return as_subnets 

def get_loopback_ips(routers_dict, as_data):
    loopback_subnets = get_loopback_subnet(as_data.get("IPv4_prefix"), as_data.get("IPv4_mask"))
    current_subnet = next(loopback_subnets)

    for hostname, router_data in routers_dict.items():
        if int(router_data["as_number"]) != int(as_data["number"]) : continue
        ip = str(current_subnet.hosts()[0]) + ' 255.255.255.255'
        routers_dict[hostname]["interfaces"]["Loopback0"] = (ip, False, None)

        current_subnet = next(loopback_subnets)

def get_external_ips(routers_dict, data, as_subnets):
     for connection in data.get("AS_connections", []):
        subnet = next(as_subnets[int(connection["AS_1"]) if int(connection["AS_1"]) > int(connection["AS_2"]) else int(connection["AS_2"])])

        subnet_ips = subnet.hosts()
        first_ip = str(next(subnet_ips)) +' 255.255.255.252'
        second_ip = str(next(subnet_ips)) + ' 255.255.255.252'

        routers_dict[connection["AS_1_router_hostname"]]['interfaces'][connection["AS_1_router_interface"]] = (first_ip, False, None)
        routers_dict[connection["AS_2_router_hostname"]]['interfaces'][connection["AS_2_router_interface"]] = (second_ip, False, None)
    
def get_ibgp_neighbors(routers_dict, data):
    for router in data["routers"]:
        for second_peer in data["routers"]:
            if router == second_peer : continue
            loopback_ip = routers_dict[second_peer["hostname"]]['interfaces']['Loopback0'][0].split(' ')[0]
            
            routers_dict[router["hostname"]]['bgp_neighbors'].append((loopback_ip, int(data["number"]),False))

def get_ebgp_neighbors(routers_dict, data):
    for connection in data.get("AS_connections", []):
        first_peer_ip = routers_dict[connection["AS_1_router_hostname"]]["interfaces"][connection["AS_1_router_interface"]][0].split(' ')[0]
        second_peer_ip = routers_dict[connection["AS_2_router_hostname"]]["interfaces"][connection["AS_2_router_interface"]][0].split(' ')[0]

        first_peer_as = int(routers_dict[connection["AS_1_router_hostname"]]["as_number"])
        second_peer_as = int(routers_dict[connection["AS_2_router_hostname"]]["as_number"])
        
        if connection["connexion"][0]["type"] == 'BGP':
            routers_dict[connection["AS_1_router_hostname"]]['bgp_neighbors'].append((second_peer_ip, second_peer_as,True))
            routers_dict[connection["AS_2_router_hostname"]]['bgp_neighbors'].append((first_peer_ip, first_peer_as,True))
        
        if connection["connexion"][0]["type"] == "VPN":
           vrf_name = connection["connexion"][0]["vrf_name"]
           rd_number = (len(routers_dict[connection["AS_1_router_hostname"]]["vpns"]) + 1) * 100
           rt_number = (len(routers_dict[connection["AS_1_router_hostname"]]["vpns"]) + 1) * 1000
           remote_as = second_peer_as
           remote_ip = second_peer_ip

           shlag_ip, shlag_mpls, _ = routers_dict[connection["AS_1_router_hostname"]]["interfaces"][connection["AS_1_router_interface"]]
           routers_dict[connection["AS_1_router_hostname"]]["interfaces"][connection["AS_1_router_interface"]] = (shlag_ip, shlag_mpls, vrf_name)

           routers_dict[connection["AS_1_router_hostname"]]['vpns'].append((vrf_name, rd_number, rt_number, remote_ip, remote_as))
           
           routers_dict[connection["AS_2_router_hostname"]]['bgp_neighbors'].append((first_peer_ip, first_peer_as, True))
            
            
            


def get_routers_dict(data):
    """Convert the intent file into a super useful dict for our project, very fancy :tm:"""
    routers = dict()
    as_subnets = dict()
    for as_name_string in [key for key, _ in data.items() if "AS_" not in key]: # Find all the AS
        as_data = data.get(as_name_string, {})[0]
        as_number = int(as_data.get("number"))
        is_igp_as = as_data.get("igp", False)
        is_vpn_client=as_data.get("VPN_Client", False)

        for router in as_data.get("routers",[]):

            hostname = router.get("hostname")
            telnet_port = int(router.get("telnet_port"))
            num_creation = int(router.get("num_creation"))
            is_border = router.get("is_border")
            routers[hostname] = {
                "as_number" : as_number,
                "is_border" : is_border,
                "mpls": False, 
                "igp": is_igp_as,
                "VPN_Client": is_vpn_client,
                "num_creation" : num_creation ,
                "telnet_port" : telnet_port, 
                "interfaces" : {}, 
                'bgp_neighbors' : [], 
                'vpns': []
            }
        
        as_subnets[as_number] = get_internal_ips(routers, as_data)
        get_loopback_ips(routers, as_data)
        get_ibgp_neighbors(routers, as_data)
    get_external_ips(routers, data, as_subnets)
    get_ebgp_neighbors(routers, data)
    return routers

#START OF CONFIG
def generate_base_cisco_config(hostname, mpls, vrfs):
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
    for vrf in vrfs:
        config.append(f"ip vrf {vrf[0]}")
        config.append(f" rd {vrf[1]}:{vrf[1]}")
        config.append(f" route-target export {vrf[2]}:{vrf[2]}")
        config.append(f" route-target import {vrf[2]}:{vrf[2]}")
        config.append("!")
    config.append("!")
    if mpls == True:
        config.append("mpls label protocol ldp\nmultilink bundle-name authenticated\n!")
    return "\n".join(config)

def config_interfaces(valeurs, num_as, igp):
    """
    Génère une configuration pour les interfaces d'un routeur.

    :param valeurs: Dictionnaire des interfaces avec leurs adresses IP
    :return: Chaîne de texte représentant la configuration des interfaces
    """
    config = []
    
    # Configuration des interfaces
    for interface, values_interface in valeurs.items():
        config.append(f"interface {interface}")
        if values_interface[2]:
            config.append(f" ip vrf forwarding {values_interface[2]}")
        elif igp:
            config.append (f" ip ospf {num_as} area 0")
        config.append(f" ip address {values_interface[0]}")
        config.append (" negotiation auto")
        if values_interface[1]:
            config.append (" mpls ip")
        config.append("!")


    return "\n".join(config)

def bgp_add(bgp_config, num, num_as, VPN_Client):
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
    for neighbor in bgp_config:
        if VPN_Client and neighbor[1] != num_as:
            config.append(f" neighbor {neighbor[0]} remote-as {neighbor[1]}")
        elif not VPN_Client:
            config.append(f" neighbor {neighbor[0]} remote-as {neighbor[1]}")
            if neighbor[1] == num_as:
                config.append(f" neighbor {neighbor[0]} update-source Loopback0")
    config.append(" !\n address-family ipv4")
    if VPN_Client:
        config.append("  redistribute connected")
    for neighbor in bgp_config:
        if VPN_Client and neighbor[1] != num_as:
            config.append(f"  neighbor {neighbor[0]} activate")
            config.append(f"  neighbor {neighbor[0]} allowas-in")
        elif not VPN_Client:
            config.append(f"  neighbor {neighbor[0]} activate")
    config.append(" exit-address-family")
    config.append("!")
    return "\n".join(config)

def add_protocol(num, num_as, igp):
    config = []
    if igp:
        config.append(f"router ospf {num_as}")
        config.append(f" router-id {num}.{num}.{num}.{num}")
        config.append(" redistribute connected")
        config.append("!")
        return "\n".join(config)
    else:
        return "!"

def add_vpnv4(hostname, as_num, router_infos):
    config = []
    border_routers_ips = []
    for host, router in router_infos.items():
        if router["as_number"] == as_num and router["is_border"] == True and host != hostname:
            border_routers_ips.append(router["interfaces"]["Loopback0"][0].split(' ')[0])
    
    config.append(" address-family vpnv4")
    for router in border_routers_ips:
        config.append(f"  neighbor {router} activate")
        config.append(f"  neighbor {router} send-community both")
    config.append(" exit-address-family")
    config.append("!")
    return "\n".join(config)


def add_vrf(vpn):
    config = []
    
    for vrf in vpn:
        config.append(f" address-family ipv4 vrf {vrf[0]}")
        config.append("  redistribute connected")
        config.append(f"  neighbor {vrf[3]} remote-as {vrf[4]}")
        config.append(f"  neighbor {vrf[3]} activate")
        config.append(" exit-address-family")
        config.append("!")
    return "\n".join(config)

def generate_config_file(router, info, router_infos):
    num_as = info["as_number"]
    num_creat = info["num_creation"]
    file_name = f"i{num_creat}_startup-config.cfg"
    with open(file_name, 'w') as file:
        file.write(generate_base_cisco_config(router, info["mpls"], info["vpns"]))
        file.write("\n" + config_interfaces(info["interfaces"], num_as, info["igp"]))
        file.write("\n" + add_protocol(num_creat, num_as, info["igp"]))
        file.write("\n" + bgp_add(info["bgp_neighbors"], num_creat, num_as, info["VPN_Client"]))
        if info["vpns"]:
            file.write("\n" + add_vpnv4(router, num_as, router_infos))
            file.write("\n" + add_vrf(info["vpns"]))

    print(f"Configuration pour le router {router} terminée")
# END OF CONFIG



if __name__ == "__main__":
        args = argument_parser()
        data = load_intent_file(args.filename)
        routers_info = get_routers_dict(data)
        pprint(routers_info)
        for router, info in routers_info.items():
            generate_config_file(router, info, routers_info)
        if args.copy_config :
            configurator = FileDispatcher(args.copy_config)
            configurator.copy_configs()
            #pour faire marcher le filedispatcher : après le lancement du code rajotuer -c "directory de tous les routers"

