#from file_dispatcher import FileDispatcher
from pprint import pprint
import ipaddress
import argparse
import json
import yaml
import re 

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

def config_interfaces(valeurs, num_as, router):
    """
    Génère une configuration pour les interfaces d'un routeur.

    :param valeurs: Dictionnaire des interfaces avec leurs adresses IP
    :return: Chaîne de texte représentant la configuration des interfaces
    """
    config = []
    
# Configuration des interfaces
    for interface, ip in valeurs[router].items():
        config.append(f"interface {interface}")
        config.append(f" ip address {ip}")
        config.append (f" ip ospf {num_as} area 0")
        config.append("!")

    return "\n".join(config)

def bgp_add(bgp_config, num, num_as, network, border_routers):
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
    for neighbor in bgp_config[f"R{num}"]:
        print (neighbor)
        config.append(f" neighbor {neighbor[0]} remote-as {neighbor[1]}")
        if neighbor[2]:
            config.append(f" neighbor {neighbor[0]} update-source Loopback0")
        else :
            config.append(f" neighbor {neighbor[0]} route-map {neighbor[3].upper()} in")
    config.append(" !\n address-family ipv4")
    for router in border_routers:
        if f"R{num}" in router[0]:
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
    num_as = info["num_as"]
    num_creat = info["num_creat"]
    file_name = f"i{num_creat}_startup-config.cfg"
    with open(file_name, 'w') as file:
        file.write(generate_base_cisco_config(router))
        file.write("\n" + config_interfaces(info["interface"], num_as, router))
        file.write("\n" + bgp_add(info["routers_bgp"], router, num_as, info["router_network"], info["border_routers"]))
        file.write("\n" + add_protocol(num_creat, num_as , info["border_routers"]))
    print(f"Configuration pour le router {router} terminée")
# END OF CONFIG
