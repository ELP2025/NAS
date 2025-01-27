#!/usr/bin/env python3

import yaml
from  pprint import pprint

def read_yaml_file(file_path):
    """
    Lit un fichier YAML et retourne son contenu sous forme de dictionnaire.
    
    :param file_path: Chemin du fichier YAML à lire
    :return: Contenu du fichier sous forme de dictionnaire
    """
    try:
        with open(file_path, 'r') as file:
            # Charger le fichier YAML
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{file_path}' n'existe pas.")
    except yaml.YAMLError as e:
        print(f"Erreur dans le fichier YAML : {e}")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    return None
"""
# Exemple d'utilisation
if __name__ == "__main__":
    # Spécifiez le chemin du fichier YAML ici
    file_path = input("Entrez le chemin du fichier YAML à lire : ").strip()
    yaml_data = read_yaml_file(file_path)
    
    if yaml_data is not None:
        print("\nContenu du fichier YAML chargé sous forme de dictionnaire :\n")
        print(yaml_data)

"""

def create_and_write_file(file_name):
    """
    Crée un fichier et permet d'écrire du contenu dans ce fichier.
    
    :param file_name: Nom du fichier à créer
    """
    try:
        with open(file_name, 'w') as file:
            print(f"Le fichier '{file_name}' a été créé.")
            print("Entrez le contenu du fichier (tapez 'FIN' sur une nouvelle ligne pour terminer) :")
            
            while True:
                line = input()
                if line.strip().upper() == 'FIN':  # Arrêter la saisie si l'utilisateur tape 'FIN'
                    break
                file.write(line + '\n')  # Écrire la ligne dans le fichier
                
        print(f"Le contenu a été écrit dans le fichier '{file_name}'.")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

"""
# Exemple d'utilisation
if __name__ == "__main__":
    file_name = "config_test.cfg"
    create_and_write_file(file_name)
"""

file_path = "/home/baptiste/GNS/GNS3/intent.yml"
dico_intent = read_yaml_file (file_path)
#print (dico_intent)

routeur_liste = []
for groups in dico_intent:
    for r in dico_intent[groups][0].get('routers', []):
        routeur_liste.append(r.get('hostname', ''))
                             
#print (routeur_liste)

def generate_cisco_config(routeur):
    """
    Génère une configuration de base pour un routeur Cisco.
    
    :param hostname: Nom d'hôte du routeur
    :param interfaces: Liste de dictionnaires contenant les informations sur les interfaces
    :param username: Nom d'utilisateur pour le login
    :param password: Mot de passe pour le login
    :param enable_secret: Secret pour activer le mode privilégié
    :return: Chaîne de texte représentant le fichier de configuration
    """
    config = []
    
    # Configuration de base
    config.append("service timestamps debug datetime msec")
    config.append("service timestamps log datetime msec")
    config.append ("!")
    config.append(f"hostname {routeur}")
    config.append ("!")
    config.append("ipv6 unicast-routing")
    config.append ("!")
    return "\n".join(config)

def config_interfaces (valeurs):
    
    config = []
    
    # Configuration des interfaces
    for interface, ip in valeurs.items():
        config.append(f"interface {interface}")
        config.append(" ipv6 enable")
        config.append(f" ipv6 address {ip}")
        config.append(" shutdown")
        config.append(" no shutdown")
        config.append ("!")

        """
        if protocole == 'RIP':
            config.append(f"ipv6 rip {protocole} enable")
        elif protocole == 'OSPF':
            config.append(f" ipv6 ospf {protocole} area 0")
    """
    #config.append("end")
    return "\n".join(config)

""""
def protocole_routeur(name):
    print("")
"""

def bgp_add (bgp_config, num):
    config = []
    
    #Configuration du BGP
    config.append(f"routeur bgp {bgp_config["AS"]}")
    config.append(f" bgp routeur-id {num}.{num}.{num}.{num}")
    config.append(f" bgp log-neighbor-changes\n no bgp default ipv4-unicast")
    for neighbor in bgp_config["neighbors"].values():
        print (neighbor)
        config.append(f" neighbor {neighbor[0]} remote-as {neighbor[1]}") #neighbor[0] = adresse IP du voisin et neighbor[1]= n°d'AS du voisin
    config.append(" !\n address-family ipv4\n exit-address-family\n !\n address-family ipv6")
    for neighbor in bgp_config["neighbors"].values():
        config.append(f"  neighbor {neighbor[0]} activate") #neighbor[0] = adresse IP du voisin et neighbor[1]= n°d'AS du voisin
    config.append(" exit-address-family")
    config.append("!")
    return "\n".join(config)

    

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
    
        
for routeur, val in dico_routeur.items():
    num = routeur[1:]
    file_name = f"i{num}_startup-config.cfg"
    with open(file_name, 'w') as file:
        #print(routeur)
        #print (val)
        #protocole = dico_prot
        bgp_config = {"AS" : 2000, "neighbors" : {"neighbor" : ["2000:200:200:56::1","2000"], "neighbor_2" : ["2000:200:200:67::1","2000"]}}
        print (bgp_config)
        file.write(generate_cisco_config(routeur))
        file.write("\n" + config_interfaces(val)) 
        file.write("\n" + bgp_add(bgp_config, num))
        #file.write(protocole_routeur("tkt"))
print ("Terminé")