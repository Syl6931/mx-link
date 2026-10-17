# Validation historique du candidat 1 — 2026-10-17

Cette note documente les vérifications initiales **avant** la correction du parcours iOS.
Pour la livraison 0.1.4-alpha, voir le CHANGELOG et les tests d’intégration.

- Base GitHub : `1ebdf7ea72a7c43c89c15298d3f744144237bb1d`.
- Comparaison avec le moteur et le plasmoïde installés : aucun développement local inédit ;
  correctif de permissions bitmap déjà plus complet dans GitHub.
- Environnement isolé Linux/Python 3.12 : **20 tests réussis**, aucun ignoré.
  Tests HTTP réels dans un HOME vierge sans affichage, plus adaptateurs simulés et
  installation/désinstallation avec commandes système simulées (pas d'installation root).
- MXBook Pro/Python 3.13 : **14 tests réussis** ; classe d'intégration volontairement ignorée
  car les ports de la version active sont occupés. Aucune interruption de ces services.
- `bash install.sh --check` exécuté sur le MXBook Pro : syntaxe, manifest, métadonnées,
  lien du raccourci et outils présents vérifiés.
- Contrôle QML via qmllint : retour 0, avec avertissements de résolution des imports Plasma
  dans le contexte du linter ; ceci ne vaut pas validation du rendu de l'applet.
- Test Qt réel, hors écran, sur le MXBook Pro : requête XMLHttpRequest POST JSON reçue
  sans Origin, compatible avec la protection locale ; test Qt réussi.
- Raccourci iCloud inspecté en lecture seule : protocole `MXLINKPAIR:`, configuration
  `MXLink-config.json` et routes de transfert conservés.

## Recette humaine demandée lors de la préparation

Recette humaine depuis zéro décrite dans TEST-CANDIDAT.fr.md : installation réelle KDE,
QR et appairage Safari/Raccourcis, autorisations iOS, transferts dans les deux sens,
historique/réglages, redémarrage. Valider sur un vrai bureau non-Plasma pour élargir la
compatibilité annoncée. La CI est incluse mais n'a pas été exécutée sur GitHub.

Le candidat a été préparé dans `~/MX-Link-candidates/0.1.4-alpha-candidate1`.
Lors de cette validation initiale, il n’avait pas remplacé les services ni le plasmoïde installés. Aucun tag ni release n’était alors publié.
