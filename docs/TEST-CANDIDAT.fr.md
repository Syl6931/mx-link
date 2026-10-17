# Test depuis zéro — 0.1.4-alpha

Le paquet n’est pas installé automatiquement sur le MXBook Pro. Les commandes ci-dessous
s'exécutent dans le dossier extrait de l'archive, avec le compte utilisateur habituel.

## 1. Retirer l'installation actuelle

```bash
bash uninstall.sh --purge
```

Cela retire services, plasmoïde, CLI, autostart, règle UFW connue, configuration, jeton,
état, historique, journaux et cache. Les anciens paquets source ne sont pas une installation.
Les téléchargements reçus sont conservés. Pour un test sans anciennes sauvegardes, supprimer
manuellement les seuls dossiers suivants, **après avoir décidé de ne pas conserver de retour arrière** :

- `~/.local/share/mxlink-backups`
- `~/.local/share/mxlink-feature-snapshots`
- `~/.local/share/mxlink-migrations`
- `~/.local/share/mxlink-test`

Sur iPhone : supprimer le raccourci **MX Link** et ses éventuels doublons/anciens raccourcis,
retirer les raccourcis du Centre de contrôle/écran d'accueil, puis supprimer
`iCloud Drive/Shortcuts/MXLink-config.json` (dossier éventuellement affiché « Raccourcis »).
Ne pas supprimer tout le dossier Shortcuts. Fermer l'ancienne page Safari d'appairage.

## 2. Installer et appairer

```bash
bash install.sh --check
bash install.sh
~/.local/bin/mxlink status
```

Ouvrir **Appairer un iPhone** dans le plasmoïde. Scanner le QR sur l'iPhone,
installer le raccourci, revenir sur la même page, puis **Appairer cet iPhone**.
Accepter les autorisations Raccourcis/Fichiers/réseau local. Si le délai de cinq minutes
est dépassé, fermer puis rouvrir l'appairage dans le plasmoïde.

## 3. Recette KDE et iPhone

- Envoyer du texte et une URL depuis la feuille de partage ; vérifier le presse-papiers et le navigateur par défaut.
- Envoyer une photo, plusieurs photos, un PDF et un fichier avec accents/espaces dans le nom.
- Copier du texte, un fichier Dolphin, plusieurs fichiers, puis une image bitmap : récupérer depuis l'iPhone.
- Tester **Envoyer vers MX** depuis le menu du raccourci.
- Vérifier paramètres de réception, dossier, historique et annulation de l'effacement.
- Redémarrer Linux puis répéter un envoi et une récupération sans réappairer.
- Ouvrir `/setup` sans code : refus attendu. Réutiliser le lien après appairage : refus attendu.
- Tester désinstallation, puis installation vierge à nouveau si nécessaire.

## 4. Recette sans Plasma

Sur un compte/une machine de test distinct, utiliser `bash install.sh --headless`.
Exécuter `mxlink pair` (ou son chemin complet), puis `set-text`, `get-text` et `send-files`
selon le README. Les fichiers reçus doivent être enregistrés sans ouvrir d'application.
Tester également un vrai bureau X11 et un autre compositeur Wayland avant d'annoncer une
compatibilité générale : les adaptateurs ont des tests simulés, pas une certification de tous les bureaux.

## Validation effectuée avant livraison

La suite automatisée couvre : historique, bitmaps PNG/BMP, choix des adaptateurs X11/Wayland,
installation/purge avec commandes système simulées, services HTTP réels dans un HOME vierge,
appairage unique/expiré, liste des routes autorisées, requêtes malformées, upload interrompu,
MIME, noms, permissions, échanges texte et fichiers sans bureau.

L'interface complète KDE et le parcours réel sur iPhone restent à valider par cette recette.
La CI est fournie dans l'archive ; aucune exécution GitHub n'est revendiquée pour ce candidat.
