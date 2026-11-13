# Proposition de système de travail — à discuter

*13/11/2026. Claude, à partir de l'[audit de Codex](audit_organisation_2026-11-13.md) et des échanges avec le porteur
du 13/11. **Rien n'est codé** : chaque point est à valider (✔), à modifier ou à refuser par le porteur.*

## 0. Le problème à résoudre

On avance, mais on se perd : états périmés, index trop long (33 Ko), lots confiés avant que les décisions ou données
soient prêtes, aucun résultat de thèse « confirmé ». Le porteur part sur le terrain lundi 16/11 et doit pouvoir
suivre et autoriser depuis son téléphone. Les deux assistants ne doivent jamais être à court en même temps.

## 1. Rôles (décidé le 13/11)

| Qui | Fait |
|---|---|
| Porteur | Collecte les données externes (forages, ministère, ONG, mesures) ; choisit les priorités ; autorise ce qui engage |
| Coordinateur (Claude **ou** Codex) | Choisit la prochaine tâche, prépare des lots prêts, relit, commite, tient l'état à jour, notifie le porteur |
| L'autre assistant | Exécute ou relit les lots confiés |

- **Mêmes droits** pour les deux quand ils coordonnent, commit et push compris (décidé).
- **Le porteur choisit le coordinateur** depuis le tableau de bord ou Telegram (décidé).

## 2. Avancer vers des résultats confirmés (audit, points 4 et 7)

- Le porteur choisit **3 résultats prioritaires** pour la reprise du 16/11, chacun avec sa condition de fin.
- Pour chacun, une chaîne courte : donnée nécessaire → protocole et puissance → calcul → relecture → résultat.
- Une chaîne bloquée par une donnée passe en attente, et on travaille sur une autre chaîne.
- *Question : l'organigramme se limite-t-il à ces 3 chaînes au départ ?*

## 3. Moins de tours, moins de jetons (audit, points 1, 2, 3, 5, 6, 9)

1. **État court et juste** : à chaque livraison, le coordinateur ferme la ligne, le message et la reprise ensemble.
2. **COORDINATION.md sous 15 Ko** : archiver le terminé.
3. **Lot prêt avant de confier** : données présentes et décisions prises, sinon on ne lance pas.
4. **Décisions groupées** : une seule question au porteur avec toutes les options, pas une par tour.
5. **Relecture limitée** aux blocages et aux changements ; le relecteur attitré garde son contexte.
6. **Passation courte** de Codex : livrable, vérifications, réserve, fichiers modifiés.
7. **Un seul point de reprise** commun, tenu par le coordinateur.

## 4. Ne jamais être à court tous les deux

- **Jauges** dans le poste : limite de 5 h et limite hebdomadaire, pour Claude et pour Codex.
- **Réserve** : au-delà de 70 %, plus de gros travaux pour cet assistant ; il garde de quoi coordonner.
- **Bascule** du coordinateur vers l'autre avant la limite, choisie par le porteur ou proposée par notification.
- **Modèles plus légers** pour la routine (relectures courtes, sessions filles), le plus fort pour les protocoles.
- **Gros travaux juste après une remise à zéro** des limites.
- **Conversations courtes** : repartir à neuf à un point propre (cette conversation est trop longue).
- Si les deux sont à court : pause propre, seuls les workflows GitHub déjà lancés continuent ; notification.

## 5. Le porteur sur le terrain

| Besoin | Proposition |
|---|---|
| Notifications et autorisations | **Bot Telegram privé** (votre compte seul) : alertes, boutons Autoriser / Refuser / Voir, commandes « situation », « décisions », « coordinateur claude/codex », « stop » |
| Voir le tableau de bord | **Page mobile légère** (à décider, alertes, chantiers, journal du jour), par Tailscale (réseau privé) ; ou seulement Telegram au début |
| Connexion coupée | **SMS par la tablette** (SIM dédiée, passerelle locale) : alertes urgentes ; réponse « OUI » + code à usage unique, depuis votre seul numéro |
| WhatsApp | Pas d'automatisation : brouillons envoyés sur Telegram, copiés par vous |
| Panne de courant | BIOS « redémarrage au retour du courant », ouverture de session automatique, tâche au démarrage (serveur, surveillant, bot) ; onduleur conseillé |

## 6. E-mails (niveau à décider)

| Niveau | Action | Accord |
|---|---|---|
| 0 | Lire, trier, résumer | non demandé |
| 1 | Brouillon de réponse | validé par Telegram avant envoi |
| 2 | Envoi seul, messages sans enjeu, contacts sur liste blanche | réglage décidé une fois |
| Interdit | Argent, contrats, données sous licence, mots de passe, nouveaux destinataires, pièces jointes de données | toujours le porteur |

- Proposition : **niveaux 0 et 1 seulement au départ**.
- Un e-mail reçu est une donnée, jamais un ordre.
- Fonctionnement en continu par une tâche programmée dans le cloud ; un tri simple avant d'appeler un assistant.

## 7. Sécurité

- Un seul canal d'autorisation, authentifié ; journal de toutes les actions faites au nom du porteur ; commande STOP.
- Aucun secret ni donnée personnelle dans le dépôt Makyclimat (public) : jetons et code des e-mails hors du dépôt.

## 8. Réutilisable pour PYC HUB

- Un noyau commun (coordinateur, maçons, journal, Telegram, SMS, autorisations) et une configuration par projet.
- *Question : qu'est-ce que PYC HUB (dépôt, site, organisation) ?*

## 9. Ordre de réalisation proposé (après validation)

1. Avant lundi : nettoyage de l'état (§ 3, points 1, 2, 7), choix des 3 résultats (§ 2), bot Telegram minimal
   (alertes et autorisations), redémarrage automatique (§ 5).
2. Semaine 1 : coordinateur alterné et jauges (§ 4), secours SMS, e-mails niveaux 0-1.
3. Ensuite : page mobile, PYC HUB.

## 10. Décisions attendues du porteur

1. Valider ou modifier chaque section (§ 2 à § 9).
2. Les 3 résultats prioritaires pour le 16/11.
3. Le niveau de départ des e-mails.
4. Page mobile tout de suite, ou Telegram seul au début.
5. Ce qu'est PYC HUB.
