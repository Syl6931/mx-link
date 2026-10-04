# MX Link

**[English](README.md) | Français**

MX Link est un pont local entre **KDE Plasma** et **iPhone** pour échanger rapidement le presse-papiers et des fichiers dans les deux sens.

> **Statut :** `0.1.0-alpha` — première version publique destinée aux tests.

## Fonctionnalités

- Texte et URL iPhone → PC
- Texte et URL PC → iPhone
- Un ou plusieurs fichiers iPhone → PC
- Un ou plusieurs fichiers PC → iPhone
- Lots de fichiers envoyés en streaming direct, sans ZIP intermédiaire
- Ouverture automatique des images reçues dans Gwenview
- Ouverture automatique des PDF reçus avec l’application par défaut
- Applet Plasma indiquant la disponibilité et la dernière activité
- Affichage du sens du transfert, du nombre de fichiers, du volume et des noms
- Appairage de l’iPhone par QR code
- Découverte locale via mDNS (`hostname.local`)
- Aucun certificat HTTPS à installer sur iOS

## Plateforme ciblée

Cette première alpha cible :

- MX Linux / systèmes basés sur Debian
- KDE Plasma 6
- iPhone / iOS avec l’app Raccourcis d’Apple
- Les deux appareils connectés au même réseau local de confiance

D’autres distributions Linux pourront être prises en charge plus tard, mais l’installateur ne les cible pas encore.

## Installation

Décompressez l’archive de la release puis lancez :

```bash
bash install.sh --check
bash install.sh --install
```

L’installateur :

1. vérifie et installe les dépendances nécessaires ;
2. installe le daemon local MX Link ;
3. installe le gateway HTTP accessible sur le réseau local ;
4. génère un jeton d’appairage aléatoire ;
5. installe l’applet Plasma ;
6. ajoute MX Link au panneau Plasma supérieur lorsqu’il existe ;
7. installe et active les services systemd utilisateur ;
8. active la découverte mDNS locale via Avahi ;
9. limite le port TCP `8767` au réseau local via UFW ;
10. génère le QR code d’appairage propre à la machine.

## Appairer un iPhone

Ouvrez l’applet Plasma **MX Link** et choisissez **Appairer un iPhone**.

Puis, sur l’iPhone :

1. scannez le QR code ;
2. touchez **Installer MX Link** ;
3. ajoutez le raccourci ;
4. revenez à la page d’installation ;
5. touchez **Appairer cet iPhone**.

Le raccourci iOS partagé ne contient ni adresse IP personnelle ni jeton d’appairage. L’appairage enregistre localement sur l’iPhone la configuration de la machine.

Pour un accès quotidien plus rapide, vous pouvez ajouter **MX Link** comme grand contrôle Raccourcis dans le Centre de contrôle iOS.

## Utilisation

### PC → iPhone

**Presse-papiers**

1. Copiez un texte ou une URL sous KDE.
2. Lancez **MX Link** sur l’iPhone.
3. Collez normalement dans iOS.

**Fichiers**

1. Sélectionnez un ou plusieurs fichiers dans Dolphin.
2. Copiez-les avec `Ctrl+C`.
3. Lancez **MX Link** sur l’iPhone.
4. Choisissez **Enregistrer dans Fichiers** ou **Partager…**.

MX Link ne lit le presse-papiers KDE que lorsque l’iPhone le demande. Copier ou trier des fichiers sur le PC ne déclenche donc aucun transfert en arrière-plan.

### iPhone → PC

Utilisez la feuille de partage iOS et choisissez **MX Link**.

Par défaut, les fichiers reçus sont enregistrés dans :

```text
~/Téléchargements/MX Link
```

Le dossier de réception et les ouvertures automatiques peuvent être réglés dans l’applet Plasma.

## Architecture

MX Link utilise deux services locaux :

- `127.0.0.1:8765` — daemon principal, accessible uniquement en local
- `0.0.0.0:8767` — gateway réseau local, protégé par le jeton d’appairage

L’iPhone rejoint la machine grâce à son nom mDNS, par exemple :

```text
http://monpc.local:8767
```

MX Link ne dépend donc pas d’une adresse IP attribuée par DHCP.

## Sécurité

MX Link est conçu pour un **réseau local de confiance**.

Le gateway LAN exige un jeton aléatoire généré lors de l’installation, mais le trafic entre l’iPhone et le PC utilise HTTP et n’est donc **pas chiffré**.

N’utilisez pas MX Link sur un réseau local non fiable.

Voir [SECURITY.md](SECURITY.md) pour plus de détails.

## Désinstallation

```bash
bash uninstall.sh
```

Pour supprimer également la configuration et le jeton :

```bash
bash uninstall.sh --purge
```

Les fichiers déjà reçus dans `Téléchargements/MX Link` sont conservés.

## Limites connues de cette alpha

- L’installateur cible actuellement Debian / MX Linux.
- La partie iPhone dépend de l’app Raccourcis d’Apple.
- Le transport HTTP suppose un réseau local de confiance.
- La gestion de plusieurs iPhone ou plusieurs PC reste basique.
- La logique de mise à jour évoluera avant une version stable.

## Licence

MIT — voir [LICENSE](LICENSE).
