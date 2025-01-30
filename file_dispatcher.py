#!/usr/bin/env python3


import os
import shutil

def find_gns3_config_files(gns3_project_dir):
    """
    Recherche récursivement tous les fichiers de configuration GNS3 au format i{numéro}_startup-config.cfg.

    Args:
        gns3_project_dir (str): Chemin du dossier de configuration du projet GNS3.

    Returns:
        dict: Un dictionnaire {numéro_routeur: chemin_du_fichier}.
    """
    router_configs = {}

    for root, sous_doss, files in os.walk(gns3_project_dir):
        print (files)
        print (sous_doss)
        for file in files:
            if file.startswith("i") and file.endswith("_startup-config.cfg"):
                try:
                    router_num = int(file[1:].split("_")[0])  # Extraction du numéro après "i"
                    router_configs[router_num] = os.path.join(root, file)
                except ValueError:
                    continue  # Ignore les fichiers mal formatés

    return router_configs

def replace_configs(gns3_configs, custom_config_dir):
    """
    Remplace les fichiers de configuration GNS3 par les fichiers de configuration personnalisés.

    Args:
        gns3_configs (dict): Dictionnaire {numéro_routeur: chemin_du_fichier_GNS3}.
        custom_config_dir (str): Dossier contenant les fichiers de configuration personnalisés.
    """
    replaced_files = 0

    for router_num, gns3_config_path in gns3_configs.items():
        custom_config_path = os.path.join(custom_config_dir, f"i{router_num}_startup-config.cfg")

        if os.path.exists(custom_config_path):
            shutil.copy(custom_config_path, gns3_config_path)
            print(f" Remplacement : {gns3_config_path} ← {custom_config_path}")
            replaced_files += 1
        else:
            print(f" Aucune config trouvée pour le routeur {router_num} ({custom_config_path} manquant)")

    print(f"\n {replaced_files}/{len(gns3_configs)} fichiers remplacés.")

if __name__ == "__main__":
    # Chemins à modifier selon ton projet
    gns3_project_directory = "/mnt/c/Users/bapti/GNS3/projects/Test_config"
    custom_config_directory = "/home/baptiste/GNS/GNS3"

    print(" Recherche des fichiers de configuration GNS3...")
    gns3_configs = find_gns3_config_files(gns3_project_directory)

    if not gns3_configs:
        print(" Aucun fichier de configuration GNS3 trouvé !")
    else:
        print(f" {len(gns3_configs)} fichiers de configuration trouvés.")

        print("\n Remplacement des fichiers...")
        replace_configs(gns3_configs, custom_config_directory)


