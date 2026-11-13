# Délégation pendant les absences du porteur

*Proposée par Claude le 13/11/2026, en application de la [décision du 13/11 après-midi](proposition_systeme.md#11-décisions-du-13112026-après-midi).
**À valider par le porteur** (Telegram : `/valider S-PIL.4`). Elle remplace la délégation du 12/11 (17:20), plus étroite.
Le porteur est absent plusieurs jours de suite, durablement : le système travaille seul et ne l'interroge que sur ce
qui lui revient.*

## 1. Ce que Claude, Codex et la boucle font seuls

- Dérouler le [fil des tâches](../pilotage/fil.yml) (fichier local) : prendre la première étape prête, par priorité, et
  passer à une autre branche quand une donnée, une décision ou un fournisseur bloque.
- Écrire protocoles, analyses de puissance, code, calculs **déjà autorisés**, rapports ; relire (3 tours au plus).
- Corriger une erreur trouvée en relecture, la consigner, recalculer, garder le résultat qui sort.
- Commiter et pousser sur `main` (jamais de push forcé, de réécriture d'historique ni de suppression de données).
- Lancer les workflows de données et les téléchargements dans les règles de rythme (un fournisseur à la fois).
- Tenir à jour COORDINATION.md, le fil, la situation et le point de reprise.
- Préparer les courriers et les e-mails (brouillons seulement).
- Relancer le surveillant s'il s'est arrêté seul (pas après un STOP du porteur).

## 2. Ce qui passe par Telegram (décision du porteur, groupée dans le compte rendu)

- **Valider un nouveau protocole** avant le calcul qu'il fixe (le protocole relu ne suffit pas).
- Retenir une **conclusion de thèse** ou changer le **niveau de fiabilité** d'un résultat vers « soutenue » ou
  « confirmée ».
- **Clore** une piste, ou en ouvrir une qui n'est pas dans le fil.
- Changer une **règle** de COORDINATION.md ou de cette délégation.
- Relever un **plafond** de lancements ou de dépense.
- Un désaccord qui reste après 3 tours de relecture.

Sans réponse, la chaîne concernée attend et le travail continue ailleurs ; la question reste dans le compte rendu
quotidien jusqu'à la réponse.

## 3. Interdit sans le porteur

- Tout envoi externe : e-mail, courrier, message à un partenaire, publication hors du dépôt et du site.
- Argent, contrats, comptes, mots de passe et secrets.
- Données sous licence restrictive, données personnelles, données brutes d'un partenaire dans le dépôt public.
- Suppression de données ou d'historique.
- Contacter MGMERL (règle permanente).

## 4. Garde-fous

- **STOP** (Telegram `/stop`) : plus aucun lancement ; la tâche en cours se termine. `/stop_net` : arrêt immédiat.
  Seul `/reprise` relance. La boucle ne redémarre jamais le surveillant après un STOP.
- **Plafond** : 8 lancements de la boucle par jour (modifiable par le porteur).
- **Journal** : chaque action faite au nom du porteur est consignée (`pilotage/etat/telegram.jsonl`, local).
- **Canal unique** : le bot n'obéit qu'au compte Telegram appairé du porteur.
