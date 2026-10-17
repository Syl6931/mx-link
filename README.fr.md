# MX Link — 0.1.4-alpha

Échangez textes, liens, images et fichiers entre un iPhone et Linux sur votre réseau local.
Le plasmoïde KDE est conservé ; le moteur fonctionne aussi sans Plasma, sous Wayland/X11
ou sans bureau avec une interface en ligne de commande.

**Version alpha.** Installation automatique ciblée :
MX Linux et Debian avec Python ≥ 3.11 et une session utilisateur systemd. L'applet cible Plasma 6.
Sur les autres distributions, installer les dépendances manuellement puis utiliser `--skip-deps`.
Le fonctionnement sur tous les compositeurs Wayland n'est pas garanti : l'accès au presse-papiers
dépend des protocoles proposés par le compositeur.

## Installer

Extraire l'archive puis, depuis son dossier :

```bash
bash install.sh --check
bash install.sh
```

Exécuter en tant qu'utilisateur habituel, **pas avec sudo**. Le script demande sudo pour
les paquets, Avahi et la règle UFW. Il détecte Plasma ; son absence n'empêche pas l'installation.
L'installateur vérifie les sommes SHA-256, conserve une sauvegarde du moteur existant,
installe les deux services utilisateur et la commande `~/.local/bin/mxlink`.

Pour une machine sans bureau :

```bash
bash install.sh --headless
~/.local/bin/mxlink pair
```

`--headless` force le mode sans bureau, même si des variables graphiques sont présentes.
Il n'installe pas les dépendances graphiques ni le plasmoïde. Une session systemd utilisateur
est nécessaire. Pour démarrer avant toute connexion utilisateur, un administrateur peut activer
`sudo loginctl enable-linger "$USER"` ; l'installateur ne le fait pas implicitement.
Un système MX lancé sans gestionnaire systemd utilisateur n'est pas pris en charge par cet installateur.

## Appairer un iPhone

1. Dans le plasmoïde : **Appairer un iPhone**, ou au terminal : `~/.local/bin/mxlink pair`.
2. Scanner le QR ou ouvrir le lien privé sur l'iPhone connecté au même réseau.
3. Installer le raccourci **MX Link** depuis la page, puis revenir à cette page.
4. Choisir **Appairer cet iPhone** directement sur la même page. Autoriser l'exécution du raccourci.

La fenêtre dure **5 minutes**. Le clic d’appairage consomme le lien une seule fois. Une nouvelle
fenêtre invalide la précédente. Si le lien expire pendant l'installation du raccourci,
générer un nouveau QR. `/setup` seul ne fournit aucun jeton.

Le raccourci existant est compatible : il reçoit `MXLINKPAIR:` suivi d'un JSON version 1.
Il conserve `MXLink-config.json` dans le dossier Raccourcis/Shortcuts d'iCloud Drive.
**iCloud distribue le raccourci et peut synchroniser cette configuration contenant le jeton ;
les fichiers échangés passent directement sur le réseau local.** Il n'y a pas de relais Internet.
Tous les iPhone appairés partagent actuellement le même jeton du poste.

## Utiliser

- iPhone → Linux : **Partager → MX Link**, pour texte, URL, image, PDF ou fichier.
- Linux → iPhone : copier texte, fichiers ou image, puis **MX Link → Récupérer depuis MX**.
- Presse-papiers iPhone → Linux : **MX Link → Envoyer vers MX**.

Les fichiers arrivent par défaut dans `Téléchargements/MX Link`. Les images/PDF peuvent
s'ouvrir automatiquement dans les applications définies par l'utilisateur. Les URL suivent
le navigateur par défaut. Pas de synchronisation automatique en arrière-plan sur iOS.
Les préférences et l'historique restent accessibles localement, via le plasmoïde.

Sans bureau, les fichiers sont enregistrés et les textes/URL restent dans un espace d'échange
privé à l'utilisateur. Il n'y a ni ouverture d'application ni notification graphique :

```bash
printf 'Bonjour depuis Linux' | ~/.local/bin/mxlink set-text
~/.local/bin/mxlink get-text
~/.local/bin/mxlink send-files /chemin/photo.jpg /chemin/document.pdf
~/.local/bin/mxlink status
~/.local/bin/mxlink config
printf '{"open_images":false,"open_pdfs":false}' | ~/.local/bin/mxlink set-config
```

`send-files` est réservé au mode sans bureau ; dans une session graphique, copier les fichiers
avec le gestionnaire de fichiers. Le texte courant reste disponible jusqu'à son remplacement
ou la purge ; il ne fait pas partie des journaux ni de l'historique.

## Réseau et sécurité

- TCP **8767** entrant, toutes les interfaces IPv4 : passerelle HTTP destinée à l'iPhone.
- TCP **8765**, uniquement `127.0.0.1` : API locale du moteur, du plasmoïde et de la CLI.
- L'installateur ajoute une règle UFW pour le sous-réseau IPv4 détecté, **sans activer UFW**.
  Sans réseau détecté ou avec un autre pare-feu, configurer la règle manuellement.
- Avahi fournit le nom `nom-du-poste.local` ; le réseau doit autoriser mDNS et les échanges entre clients.
- **Aucune ouverture/redirection NAT/PAT ni DMZ sur la box ou le routeur.**
- **HTTP non chiffré : réseau local de confiance uniquement.** L'appairage temporaire ne
  protège pas contre une interception réseau. Ne pas utiliser sur un Wi-Fi public.

La passerelle exige le jeton pour les transferts et n'expose jamais `/config`, l'historique,
les réglages, les commandes d'ouverture locale ou la création d'une fenêtre d'appairage.
Voir [SECURITY.md](SECURITY.md) pour les limites du modèle de sécurité.

## Diagnostic et désinstallation

```bash
systemctl --user status mxlink.service mxlink-http.service
~/.local/bin/mxlink status
journalctl --user -u mxlink.service -u mxlink-http.service -n 50
bash uninstall.sh
# Supprimer aussi configuration, jeton, état courant, journaux et cache :
bash uninstall.sh --purge
```

Les fichiers reçus et sauvegardes historiques restent conservés. Pour le test entièrement
vierge Linux + iPhone, suivre [docs/TEST-CANDIDAT.fr.md](docs/TEST-CANDIDAT.fr.md).

Voir aussi [la traçabilité de l'audit](docs/AUDIT-0.1.4.md) et [la documentation anglaise](README.md).
