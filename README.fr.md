# MX Link

**Partagez photos, fichiers, textes et liens entre iPhone et KDE Plasma, sur votre réseau local.**

**Un seul raccourci iOS. Dans les deux sens. Aucune app en arrière-plan. Aucun cloud.**

[![MX Link en images](mx-link-overview.png)](mx-link-overview.png)

## Ce que fait MX Link

**iPhone → KDE**
- Partagez photos, PDF et fichiers depuis la feuille de partage iOS. Ils sont enregistrés sur KDE, avec ouverture automatique possible des photos et PDF.
- Partagez une URL : elle s'ouvre directement dans le navigateur du PC.
- Partagez du texte : il est copié dans le presse-papiers KDE.

**KDE → iPhone**
- Copiez un texte, une image ou des fichiers sur KDE.
- Lancez le raccourci **MX Link** sur l'iPhone et choisissez **Récupérer depuis MX**.

**Presse-papiers iPhone → KDE**
- Lancez le même raccourci et choisissez **Envoyer vers MX** pour transmettre le texte du presse-papiers.

**Tous les échanges sont déclenchés depuis l'iPhone.** Rien ne tourne en arrière-plan sur iOS et le presse-papiers n'est pas synchronisé automatiquement.

## Installation

Il faut KDE Plasma sur MX Linux ou une distribution basée sur Debian, un iPhone avec l'app Raccourcis et les deux appareils sur le même réseau local.

Sur KDE :

```bash
git clone https://github.com/Syl6931/mx-link.git
cd mx-link
bash install.sh
```

Ouvrez le widget **MX Link** dans le panneau Plasma, puis **Appairer un iPhone**. Scannez le QR code, installez le raccourci iOS et sélectionnez **Appairer cet iPhone** sur la page affichée.

C'est tout. Depuis l'iPhone, utilisez **Partager → MX Link** pour envoyer immédiatement un élément, ou lancez le raccourci **MX Link** seul pour choisir le sens du presse-papiers.

Les fichiers reçus arrivent par défaut dans **Téléchargements/MX Link**. Le widget Plasma affiche les échanges récents et les réglages de réception.

## Désinstallation

```bash
bash uninstall.sh
```

Pour supprimer aussi les paramètres d'appairage : `bash uninstall.sh --purge`. Les fichiers déjà reçus sont conservés.

[Read in English](README.md).
