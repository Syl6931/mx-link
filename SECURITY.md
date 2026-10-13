# Sécurité

MX Link est conçu pour un réseau local de confiance.

Le service exposé sur le LAN écoute sur le port TCP 8767 et exige un jeton
aléatoire généré localement lors de l'installation. Le daemon principal reste
lié à `127.0.0.1:8765`.

Le trafic entre l'iPhone et le PC utilise HTTP sur le réseau local et n'est
donc pas chiffré. N'utilisez pas MX Link sur un réseau local non fiable.

Le jeton est stocké dans `~/.config/mxlink/token` avec des permissions
restreintes et n'est jamais inclus dans la distribution.

L'historique de transfert est limité aux 30 dernières opérations et son fichier
`~/.local/state/mxlink/history.json` est privé (`0600`). Les contenus du
presse-papiers texte ne sont pas archivés. Les routes HTTP `/history`,
`/history/open` et `/history/clear` du daemon local ne sont pas accessibles
via le proxy réseau (port 8767). Les ouvertures de fichiers utilisent
uniquement des références de transferts déjà enregistrés.
