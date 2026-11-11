# Point des attentes Codex — 11 novembre 2026

Périmètre : consigne `exec:codex:20261111-144357-8270`. Rapprochement du tableau et des avis déjà rendus, sans relancer les sessions automatiques ni les calculs.

| Chantier | Dernier avis lu | Action restante |
|---|---|---|
| R-21, méthode et puissance | `codex-relecture-051d5469ed71.md`, 14:37 | Claude doit justifier le transfert de la CCI des témoins aux épisodes, ou maintenir une analyse de sensibilité ; reformuler les seuils comme repères conservateurs et documenter leur dérivation et leur incertitude Monte-Carlo. Scores toujours verrouillés. |
| Droits et état GitHub des relectures | `codex-relecture-23a8531d3f17.md`, 14:43 | Claude doit soumettre la reprise au démarrage au délai et au plafond de tentatives. Suppression inconditionnelle des échecs encore présente lors du contrôle. |
| Charge et nouvelle conversation | `codex-relecture-0104331b7612.md`, 14:46 | Accepter le dernier nombre de jetons sans fenêtre renseignée (repli 200 000) ; confirmer le démarrage du nouveau Claude avant de fermer l'ancien. Le premier défaut est encore présent à la lecture. |

Les avis cités se trouvent dans `pilotage/etat/coordination/` (suivi local). Ce point transmet leurs conclusions ; il ne remplace pas une relecture après correction. Les autres lignes « À relire » ne sont pas déclarées validées par ce rapprochement.

Vérification locale : `.venv/Scripts/python.exe -B -X utf8 -m pytest tests/test_pilotage.py tests/test_conversations.py tests/test_conversations_codex.py -q -p no:cacheprovider` : **30 tests réussis**. Ces tests ne lèvent pas les blocages des avis statiques.

Les modifications de code déjà présentes au début de cette intervention sont laissées à leur chantier. Aucun téléchargement, calcul scientifique, lancement GitHub ou publication effectué.
