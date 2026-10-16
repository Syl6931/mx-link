# Sécurité

MX Link est conçu pour un réseau local de confiance.

Le service exposé sur le LAN écoute sur le port TCP 8767 et exige un jeton
aléatoire généré localement lors de l'installation. Le daemon principal reste
lié à `127.0.0.1:8765`.

Le trafic entre l'iPhone et le PC utilise HTTP sur le réseau local et n'est
donc pas chiffré. N'utilisez pas MX Link sur un réseau local non fiable.

Le jeton est stocké dans `~/.config/mxlink/token` avec des permissions
restreintes et n'est jamais inclus dans la distribution.

**Limite importante de l'appairage actuel :** la page `/setup` du port 8767
est accessible sans authentification et transmet le jeton d'appairage. Toute
personne ayant accès à cette page sur le réseau local peut récupérer le jeton.
Le QR code facilite l'appairage mais ne constitue pas, à lui seul, un contrôle
d'accès. Les transferts utilisent HTTP non chiffré : limiter l'exposition
réseau est donc indispensable.

L'installateur ajoute une règle UFW autorisant TCP 8767 depuis le sous-réseau
IPv4 de la route par défaut, mais n'active pas UFW. Cette restriction ne
s'applique que si UFW est effectivement actif ; d'autres pare-feu doivent
être configurés séparément. La passerelle écoute sur `0.0.0.0:8767` (toutes
les interfaces). Ne redirigez jamais ce port depuis Internet.

L'historique de transfert est limité aux 30 dernières opérations et son fichier
`~/.local/state/mxlink/history.json` est privé (`0600`). Les contenus du
presse-papiers texte ne sont pas archivés. Les routes HTTP `/history`,
`/history/open` et `/history/clear` du daemon local ne sont pas accessibles
via le proxy réseau (port 8767). Les ouvertures de fichiers utilisent
uniquement des références de transferts déjà enregistrés.
