# Sécurité

MX Link est conçu pour un réseau local de confiance.

Le service exposé sur le LAN écoute sur le port TCP 8767 et exige un jeton
aléatoire généré localement lors de l'installation. Le daemon principal reste
lié à `127.0.0.1:8765`.

Le trafic entre l'iPhone et le PC utilise HTTP sur le réseau local et n'est
donc pas chiffré. N'utilisez pas MX Link sur un réseau local non fiable.

Le jeton est stocké dans `~/.config/mxlink/token` avec des permissions
restreintes et n'est jamais inclus dans la distribution.
