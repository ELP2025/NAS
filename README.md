# GNS3
Projet GNS3:
Groupe 31 : OHRON Gabriel, FILIPOZZI Eloi, SANCHEZ Baptiste
Ce projet a pour but de manipuler les routeurs Cisco ainsi que leurs fichiers de configuration, 
afin d'automatiser les configurations anciennement faites à la main.

Le fichier de code principal est le fichier generate_config.
Ce fichier permet, à l'aide de l'intent file de générer des configurations de routeurs cisco. Si l'on rajoute au lancement le lien vers le fichier du projet GNS, on peut remplacer automatiquement les configurations des routeurs initiales par celles générées. 

Pour lancer le projet depuis un ordinateur extérieur: 
Prérequis : avoir le projet GNS câblé et ouvert (pas encore lancé)
Installer la librairie Exscript avec `pip install Exscript`
Télécharger le projet depuis le github https://github.com/ELP2025/GNS3.git
Lancer le programme avec la commande : 
"version de python" generate_config.py intent.yml -c "chemin vers le directory du projet (avant les project-files)"

Dès lors le programme se lancera, génèrera les configurations liées à l'intent file.

## Fonctionnalités
- Assignation automatique des adresses IP
- Copie automatique des fichiers de configuration
- Mise en place de RIP/OSPF
- iBGP + eBGP
- BGP Policies

Nous avons également essayé de configurer les routers en telnet mais cela ne marche pas.