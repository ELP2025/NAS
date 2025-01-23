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
                             
print (routeur_liste)

def generate_cisco_config(routeur, valeurs, protocole):
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
    config.append(f"hostname {routeur.keys()}")
    
    # Configuration des interfaces
    for interface, ip in valeurs.items():
        config.append(f"interface {interface}")
        config.append(f" ipv6 address {ip}")
        config.append(" ipv6 enable")
    protocole_rip = "Voir dico gaby"   ###################################""
    if protocole == 'RIP':
        config.append(f"ipv6 rip {protocole_rip} enable")
        
    elif protocole == 'OSPF':
        print ("OSPF")
    
    config.append("end")
    return "\n".join(config)

dico_routeur = {'R1': {'Ge 1/0': '1000:100:100::1', 'Ge 2/0': '1000:100:100:5::2'},
  'R12': {'Ge 2/0': '1000:100:100:3::1', 'Ge 4/0': '1000:100:100:8::2'},
  'R13': {'Ge 1/0': '1000:100:100:4::1',
          'Ge 2/0': '1000:100:100:3::2',
          'Ge 3/0': '1000:100:100:7::2',
          'Ge 4/0': '1000:100:100:9::2'},
  'R14': {'Ge 1/0': '1000:100:100:4::2',
          'Ge 2/0': '1000:100:100:5::1',
          'Ge 3/0': '1000:100:100:6::2'},
  'R2': {'Ge 1/0': '1000:100:100::2',
         'Ge 2/0': '1000:100:100:1::1',
         'Ge 3/0': '1000:100:100:6::1'},
  'R3': {'Ge 1/0': '1000:100:100:2::1',
         'Ge 2/0': '1000:100:100:1::2',
         'Ge 3/0': '1000:100:100:7::1',
         'Ge 4/0': '1000:100:100:8::1'},
  'R4': {'Ge 1/0': '1000:100:100:2::2', 'Ge 4/0': '1000:100:100:9::1'}}

        
for routeur, val in dico_routeur.items():
    file_name = f"config_test_{r}.cfg"
    with open(file_name, 'w') as file:
        print(routeur)
        print (val)
        file.write(generate_cisco_config(routeur, val)) ####### Attention, protocole
print ("Terminé")