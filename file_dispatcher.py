#!/usr/bin/env python3

import os
#import paramiko
#from scp import SCPClient

def get_router_config_files(directory):
    """Récupère un dictionnaire associant les routeurs aux fichiers de configuration.

    Le nom du fichier doit inclure l'adresse IP ou l'identifiant du routeur.
    Exemple : 192.168.1.1.cfg

    Args:
        directory (str): Répertoire contenant les fichiers de configuration.

    Returns:
        dict: Dictionnaire {adresse_ip: chemin_vers_fichier}.
    """
    config_files = {}
    for file in os.listdir(directory):
        if file.endswith('.cfg'):
            router_ip = file.replace('.cfg', '')  # Supposons que le nom du fichier est l'IP
            config_files[router_ip] = os.path.join(directory, file)
    return config_files

def distribute_configs(config_files_directory, router_mapping):
    """
    Distribue les fichiers .cfg aux routeurs appropriés.

    Args:
        config_files_directory (str): Chemin du répertoire contenant les fichiers .cfg.
        router_mapping (dict): Dictionnaire où les clés sont les adresses IP des routeurs,
                               et les valeurs sont les chemins distants où placer les fichiers.
    """
    config_files = get_router_config_files(config_files_directory)

    if not config_files:
        print("Aucun fichier .cfg trouvé dans le répertoire spécifié.")
        return

    for router_ip, remote_directory in router_mapping.items():
        if router_ip not in config_files:
            print(f"Aucun fichier de configuration trouvé pour le routeur {router_ip}.")
            continue

        local_config_file = config_files[router_ip]

        print(f"Connexion au routeur {router_ip}...")
        
        try:
            # Établir la connexion SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(router_ip, username='votre_utilisateur', password='votre_mot_de_passe')

            # Utiliser SCP pour transférer le fichier
            with SCPClient(ssh.get_transport()) as scp:
                destination_path = os.path.join(remote_directory, os.path.basename(local_config_file))
                print(f"Transfert de {local_config_file} vers {destination_path} sur {router_ip}...")
                scp.put(local_config_file, destination_path)

            print(f"Fichier transféré avec succès vers {router_ip}.")

        except Exception as e:
            print(f"Erreur lors de la connexion ou du transfert sur {router_ip}: {e}")

        finally:
            ssh.close()
"""
# Exemple d'utilisation
if __name__ == "__main__":
    # Répertoire local contenant les fichiers .cfg
    local_config_directory = "/chemin/vers/vos/configs"

    # Mapping des routeurs : adresse IP -> répertoire distant
    routers = {
        "192.168.1.1": "/etc/router/configs/",
        "192.168.1.2": "/etc/router/configs/",
        "192.168.1.3": "/etc/router/configs/"
    }

    distribute_configs(local_config_directory, routers)
"""


def scan_files(directory, target_extension=None):
    """
    Explore tous les fichiers dans un répertoire et ses sous-répertoires.

    Args:
        directory (str): Le chemin du répertoire de base à explorer.
        target_extension (str, optional): Extension des fichiers à rechercher (ex: ".cfg").

    Returns:
        list: Une liste de chemins vers les fichiers correspondant au critère.
    """
    matching_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if target_extension is None or file.endswith(target_extension):
                matching_files.append(os.path.join(root, file))

    return matching_files

if __name__ == "__main__":
    # Chemin de la zone à scanner
    # base_directory = input("Rentrer le chemin de votre projet pour mettre en place les configs")
    base_directory = "C:/Users/bapti/GNS3/projects/Test_config/project-files/dynamips"
    # Extension cible (par exemple ".cfg"), ou None pour tout lister
    extension_cible = ".cfg"

    print("Scan en cours...")
    files = scan_files(base_directory, target_extension=extension_cible)
    print (files)

    if files:
        print(f"Fichiers trouvés ({len(files)}):")
        for file in files:
            print(file)
    else:
        print("Aucun fichier correspondant trouvé.")
