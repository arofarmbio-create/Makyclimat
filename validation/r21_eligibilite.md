# R-21 — Population éligible (épisodes, districts, témoins)

Calcul du 11/11/2026 par [`scripts/r21_eligibilite.py`](../scripts/r21_eligibilite.py) ; 59 mois GloFAS en local. Détail par unité : [`r21_eligibilite.csv`](r21_eligibilite.csv). Aucun score calculé.

## Unités épisode × district

- Unités avec fiche : 468, dans 25 épisodes.
- **Éligibles : 425 unités, 22 épisodes, 12 saisons.**
- Non éligibles, aucune initialisation 1-3 j avant : 28 unités (2 épisodes).
- Non éligibles, données ECMWF indisponibles (bande endommagée) : 15 unités (1 épisodes).

| Épisode | Début | Saison | Districts éligibles |
|---:|---|---:|---:|
| 0 | 2004-01-26 | 2003 | 41 |
| 1 | 2004-03-07 | 2003 | 79 |
| 2 | 2005-03-08 | 2004 | 2 |
| 3 | 2005-03-31 | 2004 | 2 |
| 4 | 2007-03-09 | 2006 | 21 |
| 5 | 2007-03-26 | 2006 | 3 |
| 6 | 2008-02-17 | 2007 | 50 |
| 7 | 2008-02-27 | 2007 | 12 |
| 8 | 2008-03-05 | 2007 | 1 |
| 9 | 2010-02-03 | 2009 | 11 |
| 10 | 2010-03-09 | 2009 | 13 |
| 11 | 2011-02-09 | 2010 | 20 |
| 12 | 2011-02-22 | 2010 | 1 |
| 13 | 2012-02-09 | 2011 | 41 |
| 15 | 2012-12-23 | 2012 | 1 |
| 16 | 2013-01-19 | 2012 | 5 |
| 17 | 2013-01-28 | 2012 | 12 |
| 19 | 2014-03-30 | 2013 | 6 |
| 20 | 2015-02-07 | 2014 | 44 |
| 21 | 2015-02-22 | 2014 | 5 |
| 23 | 2016-02-02 | 2015 | 4 |
| 24 | 2017-03-16 | 2016 | 51 |

## Saison × mois

Témoins : districts sans fiche de cyclone ou d'inondation dans le mois (sur 120 districts) ; jours-districts = témoins × jours du mois. La restriction aux districts ayant une maille de rivière éligible se fait dans le code des scores.

| Saison | Mois | GloFAS | Districts avec unité éligible | Districts témoins | Jours-districts témoins |
|---:|---|---|---:|---:|---:|
| 2003 | déc. 2003 | publié | 0 | 120 | 3720 |
| 2003 | jan. 2004 | publié | 41 | 76 | 2356 |
| 2003 | fév. 2004 | publié | 0 | 120 | 3480 |
| 2003 | mars 2004 | publié | 79 | 40 | 1240 |
| 2004 | déc. 2004 | publié | 0 | 120 | 3720 |
| 2004 | jan. 2005 | publié | 0 | 120 | 3720 |
| 2004 | fév. 2005 | publié | 0 | 120 | 3360 |
| 2004 | mars 2005 | publié | 4 | 116 | 3596 |
| 2005 | déc. 2005 | publié | 0 | 120 | 3720 |
| 2005 | jan. 2006 | publié | 0 | 120 | 3720 |
| 2005 | fév. 2006 | publié | 0 | 120 | 3360 |
| 2005 | mars 2006 | publié | 0 | 120 | 3720 |
| 2006 | jan. 2007 | publié | 0 | 120 | 3720 |
| 2006 | fév. 2007 | publié | 0 | 120 | 3360 |
| 2006 | mars 2007 | publié | 23 | 92 | 2852 |
| 2007 | jan. 2008 | publié | 0 | 120 | 3720 |
| 2007 | fév. 2008 | publié | 52 | 57 | 1653 |
| 2007 | mars 2008 | publié | 1 | 119 | 3689 |
| 2008 | jan. 2009 | publié | 0 | 120 | 3720 |
| 2008 | fév. 2009 | publié | 0 | 119 | 3332 |
| 2009 | jan. 2010 | publié | 0 | 120 | 3720 |
| 2009 | fév. 2010 | publié | 11 | 102 | 2856 |
| 2009 | mars 2010 | publié | 13 | 103 | 3193 |
| 2010 | déc. 2010 | publié | 0 | 120 | 3720 |
| 2010 | jan. 2011 | publié | 0 | 120 | 3720 |
| 2010 | fév. 2011 | publié | 21 | 92 | 2576 |
| 2011 | jan. 2012 | publié | 0 | 120 | 3720 |
| 2011 | fév. 2012 | publié | 41 | 55 | 1595 |
| 2011 | mars 2012 | publié | 0 | 120 | 3720 |
| 2012 | déc. 2012 | publié | 1 | 119 | 3689 |
| 2012 | jan. 2013 | publié | 16 | 100 | 3100 |
| 2012 | fév. 2013 | publié | 0 | 110 | 3080 |
| 2012 | mars 2013 | publié | 0 | 120 | 3720 |
| 2013 | déc. 2013 | publié | 0 | 120 | 3720 |
| 2013 | mars 2014 | publié | 6 | 112 | 3472 |
| 2014 | fév. 2015 | publié | 49 | 56 | 1568 |
| 2015 | fév. 2016 | publié | 4 | 115 | 3335 |
| 2016 | jan. 2017 | publié | 0 | 120 | 3720 |
| 2016 | fév. 2017 | publié | 0 | 120 | 3360 |
| 2016 | mars 2017 | publié | 51 | 60 | 1860 |
| 2017 | déc. 2017 | publié (exclu) | 0 | 0 | 0 |
| 2017 | jan. 2018 | publié (exclu) | 0 | 0 | 0 |
| 2018 | jan. 2019 | publié (exclu) | 0 | 0 | 0 |
| 2018 | fév. 2019 | publié (exclu) | 0 | 0 | 0 |
| 2018 | mars 2019 | publié (exclu) | 0 | 0 | 0 |
