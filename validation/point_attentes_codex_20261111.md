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

## Réveil autorisé du 11/11 au soir — `exec:codex:20261111-184337-6d36`

Une passe par livrable : R-21 v4 (deux corrections seulement), limites/réseau/reprise du poste, poste unique (crochet/plafonds/arrêt), workflow 14, gardes de concurrence. Avis courts et heures dans les lignes de relecture de COORDINATION.md. Les lignes de Claude restent sous sa responsabilité.

- **R-21 : avis de 14:37 traité** dans la v4 : dérivation conditionnelle du repère CCI 0,46 et transportabilité des témoins limitée à la sensibilité. Pas de validation du statut confirmatoire ni de déverrouillage des scores.
- **Avis de 14:43 traité** : `reprendre_au_demarrage` appelle désormais `retenter_relectures`, avec délai et maximum de tentatives. Réserve distincte : ces reprises suppriment les lignes du registre utilisées par `au_plafond` ; les plafonds du jour et par tâche peuvent sous-compter les tentatives. À corriger par Claude après vérification.
- **Avis de 14:46 encore sans suite** : `jetons_codex` rejette une mesure sans `model_context_window` ; `nouvelle_conversation` ferme l'ancien Claude immédiatement après Popen, sans confirmer que le nouveau Claude démarre. Aucun correctif entrepris dans ce réveil.
- **Poste unique** : `hookSpecificOutput.additionalContext` sur `UserPromptSubmit` correspond au [schéma officiel OpenAI](https://learn.chatgpt.com/docs/hooks#userpromptsubmit). Réception réelle dans cette installation Desktop à confirmer ; le marquage « remis » précède l'émission du JSON et ne constitue pas un accusé de réception du modèle.
- **Workflow 14 et idempotence** : inventaire initial et sérialisation interne acceptés. Les paramètres différents restent parallélisables ; la file fournisseur unique doit donc toujours être contrôlée par Claude. Pas de relance ni consultation de run nécessaire à cette revue statique.

### Lignes Claude « À relire » restant à traiter

Les trois livrables prioritaires R-21 v4 / poste limites / poste unique et le workflow 14 ont reçu l'avis de cette passe. Les autres lignes encore « À relire » sont : charge des conversations et nouvelle conversation ; droits élargis et état GitHub fourni ; pilotage option C et relectures croisées ; panneau « En ce moment ». Leur validation complète reste à faire, sans répéter les avis déjà rendus sur une même version. Pour les droits élargis, le point de reprise au démarrage est résolu ; pour la charge, les deux réserves ci-dessus persistent. La suggestion d'ignorer les annulations de Tests remplacées par un succès reste une décision du porteur, pas une panne à relancer.

Vérification : `.venv/Scripts/python.exe -B -X utf8 -m pytest tests/test_poste.py tests/test_pilotage.py tests/test_conversations.py tests/test_conversations_codex.py -q -p no:cacheprovider` : **47 tests réussis**. Aucun script scientifique exécuté, aucun téléchargement ni workflow lancé ; la consultation documentaire OpenAI ne teste pas Desktop.
