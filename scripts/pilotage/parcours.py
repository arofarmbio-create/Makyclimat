"""Rendu du chemin de livraison à partir des tâches et horaires de coordination."""

import html
import re
from datetime import datetime, timedelta


def taches_coordination(texte):
    taches = {}
    section = ""
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            section = ligne[3:]
        if section != "Tâches" or not ligne.startswith("| "):
            continue
        champs = [champ.strip() for champ in re.split(r"(?<!\\)\|", ligne)[1:-1]]
        if len(champs) == 7 and champs[0] != "Tâche":
            taches[champs[0]] = champs[1:]
    return taches


def heure(valeur):
    try:
        return datetime.strptime(valeur, "%d/%m/%Y %H:%M")
    except ValueError:
        return None


def rendu_parcours(config, coordination):
    esc = html.escape
    taches = taches_coordination(coordination)
    cartes = []
    for parcours in config["parcours"]:
        etapes = parcours["etapes"]
        suivis = [taches.get(etape["suivi"], ["—", "Suivi manquant", "", "", "—", "—"]) for etape in etapes]
        terminees = sum(etat == "Fait" for _, etat, *_ in suivis)
        prochain = next((i for i, suivi in enumerate(suivis) if suivi[1] != "Fait"), None)
        creneaux = [(heure(suivi[4]), heure(suivi[5])) for suivi in suivis]
        connus = [(debut, fin) for debut, fin in creneaux if debut and fin and fin >= debut]
        origine = min((debut for debut, _ in connus), default=None)
        duree = max((fin for _, fin in connus), default=None) - origine if origine else timedelta(0)
        secondes = max(duree.total_seconds(), 60)
        axe = ""
        if origine:
            repere = "%d/%m %H:%M"
            axe = (f'<div class="gantt-axe"><span>{origine:{repere}}</span>'
                   f'<span>{origine + timedelta(seconds=secondes / 2):{repere}}</span>'
                   f'<span>{origine + timedelta(seconds=secondes):{repere}}</span></div>')
        lignes = []
        for index, (etape, suivi, creneau) in enumerate(zip(etapes, suivis, creneaux)):
            responsable, etat, _, suite, debut, fin = suivi
            ton = "ok" if etat == "Fait" else "info" if index == prochain else "neutre"
            d, f = creneau
            if origine and d and f and f >= d:
                gauche = 100 * (d - origine).total_seconds() / secondes
                largeur = 100 * (f - d).total_seconds() / secondes
                barre = (f'<div class="gantt-piste" aria-hidden="true"><span class="{ton}" '
                         f'style="left:{min(gauche, 99.5):.2f}%;width:{largeur:.2f}%"></span></div>')
            else:
                barre = '<span class="muted">Créneau non consigné</span>'
            choix = ' class="gantt-prochaine"' if index == prochain else ""
            dates = f"{debut} → {fin}" if d or f else "—"
            lignes.append(
                f'<tr{choix}><th scope="row"><strong>{esc(etape["nom"])}</strong>'
                f'<div class="muted">{esc(etape["sortie"])}</div></th>'
                f'<td>{esc(responsable)}</td><td>{esc(etape["relecteur"])}</td>'
                f'<td><span class="st {ton}"><i></i>{esc(etat)}</span></td>'
                f'<td>{barre}<div class="muted small">{esc(dates)}</div></td></tr>'
            )
        if prochain is None:
            suite_html = "<p><strong>Chantier terminé.</strong> Tous les jalons sont clos.</p>"
        else:
            responsable, etat, _, suite, *_ = suivis[prochain]
            suite = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", suite).replace("**", "").replace("`", "")
            suite_html = (f'<p class="gantt-suite"><strong>Prochaine étape · {esc(etapes[prochain]["nom"])}'
                          f'</strong> · {esc(responsable)} · {esc(etat)}<br>{esc(suite)}</p>')
        pct = round(100 * terminees / len(etapes))
        cartes.append(
            f'<article class="card pad"><h3>{esc(parcours["titre"])}</h3>'
            f'<p class="muted">{esc(parcours["cadre"])} · <a href="../{esc(parcours["protocole"], quote=True)}">Protocole de vérification</a></p>'
            f'<p><strong>Pilote</strong> · {esc(parcours["pilote"])} · '
            f'<strong>Arbitrage scientifique</strong> · {esc(parcours["decideur"])}</p>'
            f'<div class="gantt-avance"><progress aria-label="Jalons terminés" value="{terminees}" max="{len(etapes)}"></progress>'
            f'<strong>{pct} %</strong><span class="muted">{terminees}/{len(etapes)} jalons terminés</span></div>'
            + suite_html
            + '<div class="gantt-scroll"><table class="t gantt"><thead><tr><th>Jalon et condition de fin</th>'
            '<th>Exécute</th><th>Relit</th><th>État</th><th>Créneau réel · Nairobi'
            + axe + "</th></tr></thead><tbody>" + "".join(lignes) + "</tbody></table></div>"
            '<p class="muted small">La progression compte les jalons terminés à poids égal. '
            'Les barres montrent les créneaux consignés, sans prévision de durée pour les étapes suivantes.</p></article>'
        )
    return "".join(cartes)
