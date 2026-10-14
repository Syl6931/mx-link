# Changelog

## Non publié — 2026-10-14

- Correction de la confirmation de nettoyage de l’historique : boutons « Annuler » et « Effacer » distincts, sans toucher aux fichiers transférés.
- Icône Plasma remplacée par le pictogramme épuré « monitor-smartphone » demandé : écran et téléphone, trait uniforme, sans flèches ni fond opaque ; taille légèrement agrandie.

## 0.1.3-alpha — 2026-10-13

- Nouvelle icône symbolique représentant un ordinateur et un smartphone avec transfert bidirectionnel. Icône agrandie dans la zone de notification KDE et tracé SVG optimisé pour mieux occuper l’espace.
- Historique privé local des 30 dernières opérations : sens, heure, type et éléments transférés ; fichiers et liens accessibles par clic.
- Regroupement des envois multiples, liste dépliable des fichiers et bouton d'effacement avec confirmation.
- Aucun contenu texte du presse-papiers conservé ; les éléments effacés ou temporaires sont indiqués comme indisponibles.
- Historique et actions d'ouverture réservés à l'interface locale : ces routes ne sont pas transmises par la passerelle iPhone.
- Tests automatisés de rétention, regroupement, suppression, permissions et confidentialité.

## 0.1.2-alpha + correctif — 2026-10-11

- Correction du message « Réponse invalide » après enregistrement des réglages : les sélecteurs d’applications sont désormais synchronisés par liaison déclarative QML, sans référence hors portée.

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
