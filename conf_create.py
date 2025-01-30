#!/usr/bin/env python3

import yaml
from pprint import pprint

def read_yaml_file(file_path):
    """
    Lit un fichier YAML et retourne son contenu sous forme de dictionnaire.

    :param file_path: Chemin du fichier YAML à lire
    :return: Contenu du fichier sous forme de dictionnaire ou None en cas d'erreur
    """
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)  # Charger le fichier YAML
            return data
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{file_path}' n'existe pas.")
    except yaml.YAMLError as e:
        print(f"Erreur dans le fichier YAML : {e}")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    return None

def generate_cisco_config(routeur):
    """
    Génère une configuration de base pour un routeur Cisco.

    :param routeur: Nom d'hôte du routeur (hostname)
    :return: Chaîne de texte représentant la configuration de base
    """
    config = []
    
    # Configuration de base
    config.append("service timestamps debug datetime msec")
    config.append("service timestamps log datetime msec")
    config.append("!")
    config.append(f"hostname {routeur}")
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
    
    # Configuration des interfaces
    for interface, ip in valeurs.items():
        config.append(f"interface {interface}")
        config.append(" no ip address")
        config.append(" ipv6 enable")
        config.append(f" ipv6 address {ip}")
        #config.append(" shutdown")
        #config.append(" no shutdown")
        if dico_protocoles[routeur]["protocol"] == 'RIP' and interface != "loopback0":
            num_as = dico_protocoles[routeur]['AS_number']
            config.append (f" ipv6 rip RIP_AS_{num_as} enable")
        elif dico_protocoles[routeur]["protocol"] == 'OSPF' and interface != "loopback0":
            num_as = dico_protocoles[routeur]['AS_number']
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

def map_routers_to_as_and_protocol(file_path):
    """
    Associe chaque routeur à son numéro d'AS et son protocole.

    :param file_path: Chemin du fichier YAML contenant la description des AS et routeurs
    :return: Dictionnaire avec les routeurs comme clés, et les numéros d'AS et protocoles comme valeurs
    """
    data = read_yaml_file(file_path)
    if not data:
        return {}
    
    router_mapping = {}
    for as_key, as_values in data.items():
        for as_entry in as_values:
            as_number = as_entry.get('number')
            protocol = as_entry.get('IGP')
            for router in as_entry.get('routers', []):
                router_name = router['hostname']
                router_mapping[router_name] = {"AS_number": as_number, "protocol": protocol}
    return router_mapping

def add_protocole (num, dico_protocoles, routeur):
    config = []
    
    #configuration du protocole routeur*
    pprint (dico_protocoles)
    if dico_protocoles["protocol"] == 'RIP':
        num_as = dico_protocoles['AS_number']
        config.append (f"ipv6 router rip RIP_AS_{num_as}")
        config.append (" redistribute connected")
    elif dico_protocoles["protocol"] == 'OSPF':
        num_as = dico_protocoles['AS_number']
        config.append (f"ipv6 router ospf {num_as}")
        config.append (f"router-id {num}.{num}.{num}.{num}")
    return "\n".join(config)
    

def main():
    """
    Point d'entrée du programme.
    Lit un fichier YAML, associe les routeurs à leurs AS et protocoles, et génère les fichiers de configuration.
    """
    file_path = '/home/baptiste/GNS/GNS3/intent.yml'  # Chemin du fichier YAML
    router_mapping = map_routers_to_as_and_protocol(file_path)

    dico_routeur = {'R1': {'GigabitEthernet1/0': '1000:100:100::1/64',
            'GigabitEthernet2/0': '1000:100:100:5::2/64',
            'loopback0': '1000:100:100:1::1/128'},
    'R10': {'GigabitEthernet1/0': '2000:200:200:4::2/64',
            'GigabitEthernet2/0': '2000:200:200:5::1/64',
            'GigabitEthernet3/0': '2000:200:200:6::2/64',
            'GigabitEthernet4/0': '2000:200:200:8::2/64',
            'loopback0': '2000:200:200:10::10/128'},
    'R11': {'GigabitEthernet1/0': '1000:100:100:c::2/64',
            'GigabitEthernet2/0': '2000:200:200:5::2/64',
            'GigabitEthernet4/0': '2000:200:200:9::2/64',
            'loopback0': '2000:200:200:11::11/128'},
    'R12': {'GigabitEthernet2/0': '1000:100:100:3::1/64',
            'GigabitEthernet4/0': '1000:100:100:8::2/64',
            'loopback0': '1000:100:100:12::12/128'},
    'R13': {'GigabitEthernet1/0': '1000:100:100:4::1/64',
            'GigabitEthernet2/0': '1000:100:100:3::2/64',
            'GigabitEthernet3/0': '1000:100:100:7::2/64',
            'GigabitEthernet4/0': '1000:100:100:9::2/64',
            'loopback0': '1000:100:100:13::13/128'},
    'R14': {'GigabitEthernet1/0': '1000:100:100:4::2/64',
            'GigabitEthernet2/0': '1000:100:100:5::1/64',
            'GigabitEthernet3/0': '1000:100:100:6::2/64',
            'loopback0': '1000:100:100:14::14/128'},
    'R2': {'GigabitEthernet1/0': '1000:100:100::2/64',
            'GigabitEthernet2/0': '1000:100:100:1::1/64',
            'GigabitEthernet3/0': '1000:100:100:6::1/64',
            'loopback0': '1000:100:100:2::2/128'},
    'R3': {'GigabitEthernet1/0': '1000:100:100:2::1/64',
            'GigabitEthernet2/0': '1000:100:100:1::2/64',
            'GigabitEthernet3/0': '1000:100:100:7::1/64',
            'GigabitEthernet4/0': '1000:100:100:8::1/64',
            'loopback0': '1000:100:100:3::3/128'},
    'R4': {'GigabitEthernet1/0': '1000:100:100:2::2/64',
            'GigabitEthernet2/0': '1000:100:100:b::1/64',
            'GigabitEthernet4/0': '1000:100:100:9::1/64',
            'loopback0': '1000:100:100:4::4/128'},
    'R5': {'GigabitEthernet1/0': '2000:200:200::1/64',
            'GigabitEthernet2/0': '1000:100:100:b::2/64',
            'GigabitEthernet4/0': '2000:200:200:8::1/64',
            'loopback0': '2000:200:200:5::5/128'},
    'R6': {'GigabitEthernet1/0': '2000:200:200::2/64',
            'GigabitEthernet2/0': '2000:200:200:1::1/64',
            'GigabitEthernet3/0': '2000:200:200:6::1/64',
            'GigabitEthernet4/0': '2000:200:200:9::1/64',
            'loopback0': '2000:200:200:6::6/128'},
    'R7': {'GigabitEthernet1/0': '2000:200:200:2::1/64',
            'GigabitEthernet2/0': '2000:200:200:1::2/64',
            'GigabitEthernet3/0': '2000:200:200:7::1/64',
            'loopback0': '2000:200:200:7::7/128'},
    'R8': {'GigabitEthernet1/0': '2000:200:200:2::2/64',
            'GigabitEthernet2/0': '2000:200:200:3::1/64',
            'loopback0': '2000:200:200:8::8/128'},
    'R9': {'GigabitEthernet1/0': '2000:200:200:4::1/64',
            'GigabitEthernet2/0': '2000:200:200:3::2/64',
            'GigabitEthernet3/0': '2000:200:200:7::2/64',
            'loopback0': '2000:200:200:9::9/128'}}

    # Génération des fichiers de configuration pour chaque routeur
    for routeur, val in dico_routeur.items():
        num = routeur[1:]  # Extraire le numéro du routeur
        file_name = f"i{num}_startup-config.cfg"
        with open(file_name, 'w') as file:
            bgp_config = {
                "AS": 2000,
                "neighbors": {
                    "neighbor": ["2000:200:200:56::1", "2000"],
                    "neighbor_2": ["2000:200:200:67::1", "2000"]
                }
            }
            file.write(generate_cisco_config(routeur))
            file.write("\n" + config_interfaces(val, router_mapping, routeur))
            file.write("\n" + bgp_add(bgp_config, num))
            file.write("\n"+ add_protocole(num, router_mapping[routeur], routeur))

    print("Génération des configurations terminée.")

if __name__ == "__main__":
    main()
