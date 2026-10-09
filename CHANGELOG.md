# Changelog

## 0.1.2-alpha — 2026-10-09

- Export des images présentes uniquement sous forme bitmap dans le presse-papiers Wayland (PNG, JPEG, BMP, WebP, TIFF) vers l’iPhone via le raccourci existant.
- Capture en PNG privé, sans modifier le presse-papiers ni les transferts classiques (texte, URL, fichiers).
- Ajout des dépendances `wl-clipboard` et `imagemagick` dans l’installateur.
- Nettoyage des images temporaires après expiration et tests de non-régression.


## 0.1.1-alpha — 2026-10-04

Première version alpha installable.

### Fonctionnalités

- Presse-papiers texte et URL iPhone → KDE.
- Presse-papiers texte et URL KDE → iPhone.
- Fichiers iPhone → KDE avec conservation du nom.
- Fichiers KDE → iPhone en streaming direct, sans ZIP temporaire.
- Gestion des lots de fichiers.
- Ouverture automatique des images et PDF via les applications système par défaut, avec possibilité de choisir une application spécifique.
- Applet Plasma avec état, dernière activité, sens du transfert et liste des fichiers.
- Appairage iPhone par QR code.
- Raccourci iOS maître partagé via iCloud.
- Découverte locale via mDNS (`hostname.local`).
- Installation sans certificat HTTPS.
- Services systemd utilisateur.
- Règle UFW limitée au réseau local.
