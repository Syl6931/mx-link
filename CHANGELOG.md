# 0.1.4-alpha — 2026-10-17

- Appairage iOS sur une seule page web : installation du raccourci et bouton d’appairage direct, sans page « Préparer l’appairage » en double.
- L’appairage conserve un lien privé valable cinq minutes et utilisable une seule fois ; la redirection vers Raccourcis intervient après validation du bouton.
- Services découplés de Plasma, CLI autonome, mode headless, adaptateurs Wayland/X11.
- Transferts et traitement HTTP renforcés, installation/purge, documentation et tests d’intégration.

## Historique de préparation — candidat 1 (2026-10-17)

- Temporary one-use pairing; LAN transfer endpoint allowlist.
- Standalone CLI, optional Plasma widget, Wayland/X11 and forced headless exchange.
- Streamed bounded uploads, collision-safe private files, corrected MIME signatures.
- Fresh-install logging fix, log rotation, removal of clipboard text/URL logging.
- Obsolete TLS/status/Chrome-specific paths removed; shared HTTP and clipboard modules.
- Installer/purge fixes, regression/integration tests, CI and bilingual documentation.
- Candidate 1 testé sur MX Linux et iPhone avant correction du parcours d’appairage.

# Changelog

## Non publié — 2026-10-15

- Raccourci iOS maître mis à jour : au lancement direct, choix entre récupération depuis KDE et envoi du presse-papiers iPhone ; depuis la feuille de partage, transfert immédiat conservé. Mise à jour du lien iCloud dans la page d’appairage et dans les vérifications d’installation.
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
