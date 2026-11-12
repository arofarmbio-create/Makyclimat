# R-21 bis — Diagnostic exploratoire

Protocole : protocole_r21_diagnostic.md, sections 4–7 et 12. Référence conditionnelle au modèle et aux seuils ; aucune attribution causale acquise.

Bootstrap par saison : 2 000 tirages, graine 20261112. Comparaisons sur support commun ; a conservé, n exclu. CHIRPS différé ; EMS réservé.

IBTrACS horodaté : https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.SI.list.v04r01.csv ; filtres partagés de build_cyclones (positions à 6 h, sans interpolation).

Mailles rattachées aux bassins par leur fokontany (même localisation que R-21), puis hydro_units.csv. Les jours ajoutés pour J±3 ne sont pas des témoins supplémentaires.

## districts

référence basse : A, erreur hydrologique ou B

Plis hors tolérance : 0.

### commun

```json
{
  "n": 425,
  "taux": {
    "controle": 0.14823529411764705,
    "ensemble": 0.16,
    "reanalyse": 0.14588235294117646
  },
  "ic": {
    "controle": [
      0.06582007233273056,
      0.2550165195017835
    ],
    "ensemble": [
      0.06981073010980543,
      0.268379028927865
    ],
    "reanalyse": [
      0.04285250463821892,
      0.29830630536374414
    ],
    "ecart": [
      -0.05952770846329798,
      0.07001174496644293
    ]
  },
  "exclusions": {
    "controle": {
      "a": 28,
      "b": 115,
      "c": 136,
      "d": 83,
      "e": 63,
      "n": 0
    },
    "ensemble": {
      "a": 28,
      "b": 108,
      "c": 148,
      "d": 73,
      "e": 68,
      "n": 0
    },
    "reanalyse": {
      "a": 28,
      "b": 119,
      "c": 138,
      "d": 78,
      "e": 62,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

### sans_riviere

```json
{
  "n": 397,
  "taux": {
    "controle": 0.15869017632241814,
    "ensemble": 0.1712846347607053,
    "reanalyse": 0.1561712846347607
  },
  "ic": {
    "controle": [
      0.0705765781922525,
      0.2734898002549936
    ],
    "ensemble": [
      0.07493866399018624,
      0.2902522238553121
    ],
    "reanalyse": [
      0.045338536627319445,
      0.3269015296906749
    ],
    "ecart": [
      -0.0625,
      0.07633859384337974
    ]
  },
  "exclusions": {
    "controle": {
      "a": 28,
      "b": 115,
      "c": 136,
      "d": 83,
      "e": 63,
      "n": 0
    },
    "ensemble": {
      "a": 28,
      "b": 108,
      "c": 148,
      "d": 73,
      "e": 68,
      "n": 0
    },
    "reanalyse": {
      "a": 28,
      "b": 119,
      "c": 138,
      "d": 78,
      "e": 62,
      "n": 0
    }
  },
  "exclus_communs": 28
}
```

### reanalyse_controle

```json
{
  "n": 425,
  "taux": {
    "controle": 0.14823529411764705,
    "reanalyse": 0.14588235294117646
  },
  "ic": {
    "controle": [
      0.06582007233273056,
      0.2550165195017835
    ],
    "reanalyse": [
      0.04285250463821892,
      0.29830630536374414
    ],
    "ecart": [
      -0.05952770846329798,
      0.07001174496644293
    ]
  },
  "exclusions": {
    "controle": {
      "a": 28,
      "b": 115,
      "c": 136,
      "d": 83,
      "e": 63,
      "n": 0
    },
    "reanalyse": {
      "a": 28,
      "b": 119,
      "c": 138,
      "d": 78,
      "e": 62,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

### pm1

```json
{
  "n": 425,
  "taux": {
    "controle": 0.24235294117647058,
    "ensemble": 0.24705882352941178,
    "reanalyse": 0.24235294117647058
  },
  "ic": {
    "controle": [
      0.09560461324729899,
      0.3419883861079697
    ],
    "ensemble": [
      0.09315100931677019,
      0.3487412587412586
    ],
    "reanalyse": [
      0.09901802685323735,
      0.33982652946918657
    ],
    "ecart": [
      -0.051948633803472505,
      0.06824429383035979
    ]
  },
  "exclusions": {
    "controle": {
      "a": 28,
      "b": 294,
      "c": 0,
      "d": 0,
      "e": 103,
      "n": 0
    },
    "ensemble": {
      "a": 28,
      "b": 292,
      "c": 0,
      "d": 0,
      "e": 105,
      "n": 0
    },
    "reanalyse": {
      "a": 28,
      "b": 294,
      "c": 0,
      "d": 0,
      "e": 103,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

### k1

```json
{
  "n": 425,
  "taux": {
    "controle": 0.14823529411764705,
    "ensemble": 0.16,
    "reanalyse": 0.13647058823529412
  },
  "ic": {
    "controle": [
      0.06582007233273056,
      0.2550165195017835
    ],
    "ensemble": [
      0.06981073010980543,
      0.268379028927865
    ],
    "reanalyse": [
      0.03961375086436827,
      0.2808662227406758
    ],
    "ecart": [
      -0.060026209697588116,
      0.0485846372688478
    ]
  },
  "exclusions": {
    "controle": {
      "a": 28,
      "b": 115,
      "c": 136,
      "d": 83,
      "e": 63,
      "n": 0
    },
    "ensemble": {
      "a": 28,
      "b": 108,
      "c": 148,
      "d": 73,
      "e": 68,
      "n": 0
    },
    "reanalyse": {
      "a": 28,
      "b": 339,
      "c": 0,
      "d": 0,
      "e": 58,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

## bassins

référence basse : A, erreur hydrologique ou B

Plis hors tolérance : 0.

### commun

```json
{
  "n": 275,
  "taux": {
    "controle": 0.1890909090909091,
    "ensemble": 0.2,
    "reanalyse": 0.18545454545454546
  },
  "ic": {
    "controle": [
      0.08415622535704899,
      0.2950663466967813
    ],
    "ensemble": [
      0.08745247148288973,
      0.30827141965585897
    ],
    "reanalyse": [
      0.07670019712430427,
      0.3333586626139816
    ],
    "ecart": [
      -0.08605724956512842,
      0.07559300114952686
    ]
  },
  "exclusions": {
    "controle": {
      "a": 0,
      "b": 81,
      "c": 88,
      "d": 54,
      "e": 52,
      "n": 0
    },
    "ensemble": {
      "a": 0,
      "b": 82,
      "c": 83,
      "d": 55,
      "e": 55,
      "n": 0
    },
    "reanalyse": {
      "a": 0,
      "b": 71,
      "c": 91,
      "d": 62,
      "e": 51,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

### sans_riviere

```json
{
  "n": 275,
  "taux": {
    "controle": 0.1890909090909091,
    "ensemble": 0.2,
    "reanalyse": 0.18545454545454546
  },
  "ic": {
    "controle": [
      0.08415622535704899,
      0.2950663466967813
    ],
    "ensemble": [
      0.08745247148288973,
      0.30827141965585897
    ],
    "reanalyse": [
      0.07670019712430427,
      0.3333586626139816
    ],
    "ecart": [
      -0.08605724956512842,
      0.07559300114952686
    ]
  },
  "exclusions": {
    "controle": {
      "a": 0,
      "b": 81,
      "c": 88,
      "d": 54,
      "e": 52,
      "n": 0
    },
    "ensemble": {
      "a": 0,
      "b": 82,
      "c": 83,
      "d": 55,
      "e": 55,
      "n": 0
    },
    "reanalyse": {
      "a": 0,
      "b": 71,
      "c": 91,
      "d": 62,
      "e": 51,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

### reanalyse_controle

```json
{
  "n": 275,
  "taux": {
    "controle": 0.1890909090909091,
    "reanalyse": 0.18545454545454546
  },
  "ic": {
    "controle": [
      0.08415622535704899,
      0.2950663466967813
    ],
    "reanalyse": [
      0.07670019712430427,
      0.3333586626139816
    ],
    "ecart": [
      -0.08605724956512842,
      0.07559300114952686
    ]
  },
  "exclusions": {
    "controle": {
      "a": 0,
      "b": 81,
      "c": 88,
      "d": 54,
      "e": 52,
      "n": 0
    },
    "reanalyse": {
      "a": 0,
      "b": 71,
      "c": 91,
      "d": 62,
      "e": 51,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

### pm1

```json
{
  "n": 275,
  "taux": {
    "controle": 0.28,
    "ensemble": 0.2909090909090909,
    "reanalyse": 0.29454545454545455
  },
  "ic": {
    "controle": [
      0.11814126230661041,
      0.4235494850759294
    ],
    "ensemble": [
      0.12028975314719742,
      0.44508713401142347
    ],
    "reanalyse": [
      0.13353456855169185,
      0.42819396051103364
    ],
    "ecart": [
      -0.0277820910973085,
      0.06593406593406595
    ]
  },
  "exclusions": {
    "controle": {
      "a": 0,
      "b": 198,
      "c": 0,
      "d": 0,
      "e": 77,
      "n": 0
    },
    "ensemble": {
      "a": 0,
      "b": 195,
      "c": 0,
      "d": 0,
      "e": 80,
      "n": 0
    },
    "reanalyse": {
      "a": 0,
      "b": 194,
      "c": 0,
      "d": 0,
      "e": 81,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

### k1

```json
{
  "n": 275,
  "taux": {
    "controle": 0.1890909090909091,
    "ensemble": 0.2,
    "reanalyse": 0.16727272727272727
  },
  "ic": {
    "controle": [
      0.08415622535704899,
      0.2950663466967813
    ],
    "ensemble": [
      0.08745247148288973,
      0.30827141965585897
    ],
    "reanalyse": [
      0.06483815919850269,
      0.30899600370670677
    ],
    "ecart": [
      -0.09786039648424971,
      0.048913043478260865
    ]
  },
  "exclusions": {
    "controle": {
      "a": 0,
      "b": 81,
      "c": 88,
      "d": 54,
      "e": 52,
      "n": 0
    },
    "ensemble": {
      "a": 0,
      "b": 82,
      "c": 83,
      "d": 55,
      "e": 55,
      "n": 0
    },
    "reanalyse": {
      "a": 0,
      "b": 229,
      "c": 0,
      "d": 0,
      "e": 46,
      "n": 0
    }
  },
  "exclus_communs": 0
}
```

## bassins_recoupement

référence basse : A, erreur hydrologique ou B

Plis hors tolérance : 0.

### commun

```json
{
  "n": 565,
  "taux": {
    "controle": 0.18584070796460178,
    "ensemble": 0.17876106194690267,
    "reanalyse": 0.15752212389380532
  },
  "ic": {
    "controle": [
      0.09824792362359791,
      0.27128061193017083
    ],
    "ensemble": [
      0.0884608843537415,
      0.2573158247732006
    ],
    "reanalyse": [
      0.07644485884241338,
      0.26639344262295084
    ],
    "ecart": [
      -0.08681093289085545,
      0.039172768489053954
    ]
  },
  "exclusions": {
    "controle": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 112,
      "e": 105,
      "n": 0
    },
    "ensemble": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 116,
      "e": 101,
      "n": 0
    },
    "reanalyse": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 124,
      "e": 89,
      "n": 4
    }
  },
  "exclus_communs": 4
}
```

### sans_riviere

```json
{
  "n": 563,
  "taux": {
    "controle": 0.18650088809946713,
    "ensemble": 0.17939609236234458,
    "reanalyse": 0.15808170515097691
  },
  "ic": {
    "controle": [
      0.09889567669172931,
      0.27203284309157566
    ],
    "ensemble": [
      0.08883659323842959,
      0.25801880390855897
    ],
    "reanalyse": [
      0.07666990497338602,
      0.2674897119341564
    ],
    "ecart": [
      -0.0871081178847929,
      0.03953552261691797
    ]
  },
  "exclusions": {
    "controle": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 112,
      "e": 105,
      "n": 0
    },
    "ensemble": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 116,
      "e": 101,
      "n": 0
    },
    "reanalyse": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 124,
      "e": 89,
      "n": 4
    }
  },
  "exclus_communs": 6
}
```

### reanalyse_controle

```json
{
  "n": 565,
  "taux": {
    "controle": 0.18584070796460178,
    "reanalyse": 0.15752212389380532
  },
  "ic": {
    "controle": [
      0.09824792362359791,
      0.27128061193017083
    ],
    "reanalyse": [
      0.07644485884241338,
      0.26639344262295084
    ],
    "ecart": [
      -0.08681093289085545,
      0.039172768489053954
    ]
  },
  "exclusions": {
    "controle": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 112,
      "e": 105,
      "n": 0
    },
    "reanalyse": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 124,
      "e": 89,
      "n": 4
    }
  },
  "exclus_communs": 4
}
```

### pm1

```json
{
  "n": 565,
  "taux": {
    "controle": 0.2867256637168142,
    "ensemble": 0.2831858407079646,
    "reanalyse": 0.26902654867256637
  },
  "ic": {
    "controle": [
      0.12583236728153022,
      0.4291471997905632
    ],
    "ensemble": [
      0.11973254103085278,
      0.43406320881359056
    ],
    "reanalyse": [
      0.12559676044330775,
      0.39207006248095083
    ],
    "ecart": [
      -0.059563328383655044,
      0.03140541571319601
    ]
  },
  "exclusions": {
    "controle": {
      "a": 2,
      "b": 405,
      "c": 0,
      "d": 0,
      "e": 162,
      "n": 0
    },
    "ensemble": {
      "a": 2,
      "b": 407,
      "c": 0,
      "d": 0,
      "e": 160,
      "n": 0
    },
    "reanalyse": {
      "a": 2,
      "b": 411,
      "c": 0,
      "d": 0,
      "e": 152,
      "n": 4
    }
  },
  "exclus_communs": 4
}
```

### k1

```json
{
  "n": 565,
  "taux": {
    "controle": 0.18584070796460178,
    "ensemble": 0.17876106194690267,
    "reanalyse": 0.1433628318584071
  },
  "ic": {
    "controle": [
      0.09824792362359791,
      0.27128061193017083
    ],
    "ensemble": [
      0.0884608843537415,
      0.2573158247732006
    ],
    "reanalyse": [
      0.06428268765133172,
      0.24698071498589633
    ],
    "ecart": [
      -0.0961591627172196,
      0.01735452230500801
    ]
  },
  "exclusions": {
    "controle": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 112,
      "e": 105,
      "n": 0
    },
    "ensemble": {
      "a": 2,
      "b": 165,
      "c": 185,
      "d": 116,
      "e": 101,
      "n": 0
    },
    "reanalyse": {
      "a": 2,
      "b": 482,
      "c": 0,
      "d": 0,
      "e": 81,
      "n": 4
    }
  },
  "exclus_communs": 4
}
```

## D3 — Comparaison par épisode

```json
{
  "0": {
    "districts": {
      "n": 41,
      "taux": {
        "controle": 0.024390243902439025,
        "ensemble": 0.024390243902439025,
        "reanalyse": 0.024390243902439025
      },
      "ic": {
        "controle": [
          0.024390243902439025,
          0.024390243902439025
        ],
        "ensemble": [
          0.024390243902439025,
          0.024390243902439025
        ],
        "reanalyse": [
          0.024390243902439025,
          0.024390243902439025
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 3,
          "b": 26,
          "c": 11,
          "d": 0,
          "e": 1,
          "n": 0
        },
        "ensemble": {
          "a": 3,
          "b": 24,
          "c": 13,
          "d": 0,
          "e": 1,
          "n": 0
        },
        "reanalyse": {
          "a": 3,
          "b": 32,
          "c": 5,
          "d": 0,
          "e": 1,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 15,
      "taux": {
        "controle": 0.13333333333333333,
        "ensemble": 0.13333333333333333,
        "reanalyse": 0.13333333333333333
      },
      "ic": {
        "controle": [
          0.13333333333333333,
          0.13333333333333333
        ],
        "ensemble": [
          0.13333333333333333,
          0.13333333333333333
        ],
        "reanalyse": [
          0.13333333333333333,
          0.13333333333333333
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 8,
          "c": 5,
          "d": 0,
          "e": 2,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 8,
          "c": 5,
          "d": 0,
          "e": 2,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 10,
          "c": 3,
          "d": 0,
          "e": 2,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "1": {
    "districts": {
      "n": 79,
      "taux": {
        "controle": 0.12658227848101267,
        "ensemble": 0.16455696202531644,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.12658227848101267,
          0.12658227848101267
        ],
        "ensemble": [
          0.16455696202531644,
          0.16455696202531644
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          -0.12658227848101267,
          -0.12658227848101267
        ]
      },
      "exclusions": {
        "controle": {
          "a": 3,
          "b": 10,
          "c": 17,
          "d": 39,
          "e": 10,
          "n": 0
        },
        "ensemble": {
          "a": 3,
          "b": 6,
          "c": 21,
          "d": 36,
          "e": 13,
          "n": 0
        },
        "reanalyse": {
          "a": 3,
          "b": 13,
          "c": 22,
          "d": 41,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 42,
      "taux": {
        "controle": 0.2619047619047619,
        "ensemble": 0.30952380952380953,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.2619047619047619,
          0.2619047619047619
        ],
        "ensemble": [
          0.30952380952380953,
          0.30952380952380953
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          -0.2619047619047619,
          -0.2619047619047619
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 5,
          "c": 6,
          "d": 20,
          "e": 11,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 4,
          "c": 5,
          "d": 20,
          "e": 13,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 5,
          "c": 9,
          "d": 28,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "2": {
    "districts": {
      "n": 2,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 0,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 3,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 2,
          "c": 0,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 2,
          "c": 0,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 1,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "3": {
    "districts": {
      "n": 2,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 1,
          "d": 1,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 2,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.5
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.5,
          0.5
        ],
        "ecart": [
          0.5,
          0.5
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 1,
          "d": 0,
          "e": 1,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "4": {
    "districts": {
      "n": 21,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 9,
          "c": 12,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 9,
          "c": 12,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 9,
          "c": 12,
          "d": 0,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 18,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 9,
          "c": 9,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 9,
          "c": 9,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 7,
          "c": 11,
          "d": 0,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "5": {
    "districts": {
      "n": 3,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 1,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 3,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 1,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "6": {
    "districts": {
      "n": 50,
      "taux": {
        "controle": 0.44,
        "ensemble": 0.5,
        "reanalyse": 0.6
      },
      "ic": {
        "controle": [
          0.44,
          0.44
        ],
        "ensemble": [
          0.5,
          0.5
        ],
        "reanalyse": [
          0.6,
          0.6
        ],
        "ecart": [
          0.15999999999999998,
          0.15999999999999998
        ]
      },
      "exclusions": {
        "controle": {
          "a": 4,
          "b": 0,
          "c": 2,
          "d": 22,
          "e": 22,
          "n": 0
        },
        "ensemble": {
          "a": 4,
          "b": 0,
          "c": 3,
          "d": 18,
          "e": 25,
          "n": 0
        },
        "reanalyse": {
          "a": 4,
          "b": 0,
          "c": 1,
          "d": 15,
          "e": 30,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 30,
      "taux": {
        "controle": 0.5666666666666667,
        "ensemble": 0.6,
        "reanalyse": 0.6666666666666666
      },
      "ic": {
        "controle": [
          0.5666666666666667,
          0.5666666666666667
        ],
        "ensemble": [
          0.6,
          0.6
        ],
        "reanalyse": [
          0.6666666666666666,
          0.6666666666666666
        ],
        "ecart": [
          0.09999999999999998,
          0.09999999999999998
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 5,
          "d": 8,
          "e": 17,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 5,
          "d": 7,
          "e": 18,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 8,
          "e": 20,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "7": {
    "districts": {
      "n": 12,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.08333333333333333
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.08333333333333333,
          0.08333333333333333
        ],
        "ecart": [
          0.08333333333333333,
          0.08333333333333333
        ]
      },
      "exclusions": {
        "controle": {
          "a": 3,
          "b": 0,
          "c": 7,
          "d": 2,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 3,
          "b": 0,
          "c": 7,
          "d": 2,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 3,
          "b": 0,
          "c": 6,
          "d": 2,
          "e": 1,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 8,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.125
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.125,
          0.125
        ],
        "ecart": [
          0.125,
          0.125
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 5,
          "d": 3,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 5,
          "d": 3,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 3,
          "d": 4,
          "e": 1,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "9": {
    "districts": {
      "n": 11,
      "taux": {
        "controle": 0.5454545454545454,
        "ensemble": 0.2727272727272727,
        "reanalyse": 0.18181818181818182
      },
      "ic": {
        "controle": [
          0.5454545454545454,
          0.5454545454545454
        ],
        "ensemble": [
          0.2727272727272727,
          0.2727272727272727
        ],
        "reanalyse": [
          0.18181818181818182,
          0.18181818181818182
        ],
        "ecart": [
          -0.3636363636363636,
          -0.3636363636363636
        ]
      },
      "exclusions": {
        "controle": {
          "a": 1,
          "b": 3,
          "c": 1,
          "d": 0,
          "e": 6,
          "n": 0
        },
        "ensemble": {
          "a": 1,
          "b": 1,
          "c": 6,
          "d": 0,
          "e": 3,
          "n": 0
        },
        "reanalyse": {
          "a": 1,
          "b": 5,
          "c": 3,
          "d": 0,
          "e": 2,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 10,
      "taux": {
        "controle": 0.4,
        "ensemble": 0.4,
        "reanalyse": 0.3
      },
      "ic": {
        "controle": [
          0.4,
          0.4
        ],
        "ensemble": [
          0.4,
          0.4
        ],
        "reanalyse": [
          0.3,
          0.3
        ],
        "ecart": [
          -0.10000000000000003,
          -0.10000000000000003
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 4,
          "c": 2,
          "d": 0,
          "e": 4,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 5,
          "c": 0,
          "d": 1,
          "e": 4,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 5,
          "c": 1,
          "d": 1,
          "e": 3,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "10": {
    "districts": {
      "n": 13,
      "taux": {
        "controle": 0.15384615384615385,
        "ensemble": 0.23076923076923078,
        "reanalyse": 0.3076923076923077
      },
      "ic": {
        "controle": [
          0.15384615384615385,
          0.15384615384615385
        ],
        "ensemble": [
          0.23076923076923078,
          0.23076923076923078
        ],
        "reanalyse": [
          0.3076923076923077,
          0.3076923076923077
        ],
        "ecart": [
          0.15384615384615385,
          0.15384615384615385
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 11,
          "e": 2,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 10,
          "e": 3,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 9,
          "e": 4,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 12,
      "taux": {
        "controle": 0.25,
        "ensemble": 0.25,
        "reanalyse": 0.25
      },
      "ic": {
        "controle": [
          0.25,
          0.25
        ],
        "ensemble": [
          0.25,
          0.25
        ],
        "reanalyse": [
          0.25,
          0.25
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 9,
          "e": 3,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 9,
          "e": 3,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 9,
          "e": 3,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "11": {
    "districts": {
      "n": 20,
      "taux": {
        "controle": 0.05,
        "ensemble": 0.05,
        "reanalyse": 0.05
      },
      "ic": {
        "controle": [
          0.05,
          0.05
        ],
        "ensemble": [
          0.05,
          0.05
        ],
        "reanalyse": [
          0.05,
          0.05
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 8,
          "c": 11,
          "d": 0,
          "e": 1,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 8,
          "c": 11,
          "d": 0,
          "e": 1,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 10,
          "c": 9,
          "d": 0,
          "e": 1,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 23,
      "taux": {
        "controle": 0.08695652173913043,
        "ensemble": 0.08695652173913043,
        "reanalyse": 0.17391304347826086
      },
      "ic": {
        "controle": [
          0.08695652173913043,
          0.08695652173913043
        ],
        "ensemble": [
          0.08695652173913043,
          0.08695652173913043
        ],
        "reanalyse": [
          0.17391304347826086,
          0.17391304347826086
        ],
        "ecart": [
          0.08695652173913043,
          0.08695652173913043
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 9,
          "c": 10,
          "d": 2,
          "e": 2,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 9,
          "c": 10,
          "d": 2,
          "e": 2,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 12,
          "c": 6,
          "d": 1,
          "e": 4,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "13": {
    "districts": {
      "n": 41,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.12195121951219512
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.12195121951219512,
          0.12195121951219512
        ],
        "ecart": [
          0.12195121951219512,
          0.12195121951219512
        ]
      },
      "exclusions": {
        "controle": {
          "a": 4,
          "b": 33,
          "c": 4,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 4,
          "b": 35,
          "c": 2,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 4,
          "b": 24,
          "c": 8,
          "d": 0,
          "e": 5,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 22,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.13636363636363635
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.13636363636363635,
          0.13636363636363635
        ],
        "ecart": [
          0.13636363636363635,
          0.13636363636363635
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 20,
          "c": 2,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 21,
          "c": 1,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 14,
          "c": 5,
          "d": 0,
          "e": 3,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "15": {
    "districts": {
      "n": 1,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 1,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 1,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 1,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "16": {
    "districts": {
      "n": 5,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 5,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 5,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 5,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 6,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 6,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 6,
          "c": 0,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 5,
          "c": 1,
          "d": 0,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "17": {
    "districts": {
      "n": 12,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.08333333333333333
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.08333333333333333,
          0.08333333333333333
        ],
        "ecart": [
          0.08333333333333333,
          0.08333333333333333
        ]
      },
      "exclusions": {
        "controle": {
          "a": 3,
          "b": 0,
          "c": 9,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 3,
          "b": 0,
          "c": 9,
          "d": 0,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 3,
          "b": 0,
          "c": 8,
          "d": 0,
          "e": 1,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 4,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.25
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.25,
          0.25
        ],
        "ecart": [
          0.25,
          0.25
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 3,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 3,
          "d": 1,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 1,
          "e": 1,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "19": {
    "districts": {
      "n": 6,
      "taux": {
        "controle": 0.5,
        "ensemble": 0.5,
        "reanalyse": 0.3333333333333333
      },
      "ic": {
        "controle": [
          0.5,
          0.5
        ],
        "ensemble": [
          0.5,
          0.5
        ],
        "reanalyse": [
          0.3333333333333333,
          0.3333333333333333
        ],
        "ecart": [
          -0.16666666666666669,
          -0.16666666666666669
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 2,
          "c": 1,
          "d": 0,
          "e": 3,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 1,
          "c": 2,
          "d": 0,
          "e": 3,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 2,
          "c": 2,
          "d": 0,
          "e": 2,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 5,
      "taux": {
        "controle": 0.4,
        "ensemble": 0.4,
        "reanalyse": 0.4
      },
      "ic": {
        "controle": [
          0.4,
          0.4
        ],
        "ensemble": [
          0.4,
          0.4
        ],
        "reanalyse": [
          0.4,
          0.4
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 2,
          "c": 0,
          "d": 1,
          "e": 2,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 2,
          "c": 0,
          "d": 1,
          "e": 2,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 2,
          "c": 1,
          "d": 0,
          "e": 2,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "20": {
    "districts": {
      "n": 44,
      "taux": {
        "controle": 0.20454545454545456,
        "ensemble": 0.22727272727272727,
        "reanalyse": 0.20454545454545456
      },
      "ic": {
        "controle": [
          0.20454545454545456,
          0.20454545454545456
        ],
        "ensemble": [
          0.22727272727272727,
          0.22727272727272727
        ],
        "reanalyse": [
          0.20454545454545456,
          0.20454545454545456
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 3,
          "b": 7,
          "c": 20,
          "d": 5,
          "e": 9,
          "n": 0
        },
        "ensemble": {
          "a": 3,
          "b": 6,
          "c": 22,
          "d": 3,
          "e": 10,
          "n": 0
        },
        "reanalyse": {
          "a": 3,
          "b": 6,
          "c": 19,
          "d": 7,
          "e": 9,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 24,
      "taux": {
        "controle": 0.20833333333333334,
        "ensemble": 0.20833333333333334,
        "reanalyse": 0.20833333333333334
      },
      "ic": {
        "controle": [
          0.20833333333333334,
          0.20833333333333334
        ],
        "ensemble": [
          0.20833333333333334,
          0.20833333333333334
        ],
        "reanalyse": [
          0.20833333333333334,
          0.20833333333333334
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 4,
          "c": 10,
          "d": 5,
          "e": 5,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 4,
          "c": 9,
          "d": 6,
          "e": 5,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 4,
          "c": 9,
          "d": 6,
          "e": 5,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "21": {
    "districts": {
      "n": 5,
      "taux": {
        "controle": 0.8,
        "ensemble": 0.8,
        "reanalyse": 0.6
      },
      "ic": {
        "controle": [
          0.8,
          0.8
        ],
        "ensemble": [
          0.8,
          0.8
        ],
        "reanalyse": [
          0.6,
          0.6
        ],
        "ecart": [
          -0.20000000000000007,
          -0.20000000000000007
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 0,
          "e": 4,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 0,
          "e": 4,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 2,
          "d": 0,
          "e": 3,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 4,
      "taux": {
        "controle": 0.5,
        "ensemble": 0.5,
        "reanalyse": 0.75
      },
      "ic": {
        "controle": [
          0.5,
          0.5
        ],
        "ensemble": [
          0.5,
          0.5
        ],
        "reanalyse": [
          0.75,
          0.75
        ],
        "ecart": [
          0.25,
          0.25
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 0,
          "e": 2,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 1,
          "c": 1,
          "d": 0,
          "e": 2,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 1,
          "d": 0,
          "e": 3,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "23": {
    "districts": {
      "n": 4,
      "taux": {
        "controle": 1.0,
        "ensemble": 1.0,
        "reanalyse": 0.75
      },
      "ic": {
        "controle": [
          1.0,
          1.0
        ],
        "ensemble": [
          1.0,
          1.0
        ],
        "reanalyse": [
          0.75,
          0.75
        ],
        "ecart": [
          -0.25,
          -0.25
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 0,
          "e": 4,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 0,
          "e": 4,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 1,
          "c": 0,
          "d": 0,
          "e": 3,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 4,
      "taux": {
        "controle": 1.0,
        "ensemble": 1.0,
        "reanalyse": 0.75
      },
      "ic": {
        "controle": [
          1.0,
          1.0
        ],
        "ensemble": [
          1.0,
          1.0
        ],
        "reanalyse": [
          0.75,
          0.75
        ],
        "ecart": [
          -0.25,
          -0.25
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 0,
          "e": 4,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 0,
          "c": 0,
          "d": 0,
          "e": 4,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 0,
          "c": 1,
          "d": 0,
          "e": 3,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  },
  "24": {
    "districts": {
      "n": 51,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 4,
          "b": 8,
          "c": 36,
          "d": 3,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 4,
          "b": 9,
          "c": 35,
          "d": 3,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 4,
          "b": 9,
          "c": 36,
          "d": 2,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    },
    "bassins": {
      "n": 39,
      "taux": {
        "controle": 0.0,
        "ensemble": 0.0,
        "reanalyse": 0.0
      },
      "ic": {
        "controle": [
          0.0,
          0.0
        ],
        "ensemble": [
          0.0,
          0.0
        ],
        "reanalyse": [
          0.0,
          0.0
        ],
        "ecart": [
          0.0,
          0.0
        ]
      },
      "exclusions": {
        "controle": {
          "a": 0,
          "b": 9,
          "c": 28,
          "d": 2,
          "e": 0,
          "n": 0
        },
        "ensemble": {
          "a": 0,
          "b": 10,
          "c": 27,
          "d": 2,
          "e": 0,
          "n": 0
        },
        "reanalyse": {
          "a": 0,
          "b": 6,
          "c": 32,
          "d": 1,
          "e": 0,
          "n": 0
        }
      },
      "exclus_communs": 0
    }
  }
}
```

## D4 — Contexte cyclonique

```json
{
  "100–300 km": {
    "n": 80,
    "taux": {
      "controle": 0.2375,
      "ensemble": 0.25,
      "reanalyse": 0.2375
    },
    "ic": {
      "controle": [
        0.11392405063291139,
        0.4
      ],
      "ensemble": [
        0.13043478260869565,
        0.4642857142857143
      ],
      "reanalyse": [
        0.017573092864344133,
        0.5714285714285714
      ],
      "ecart": [
        -0.10317460317460317,
        0.17857142857142855
      ]
    },
    "exclusions": {
      "controle": {
        "a": 8,
        "b": 9,
        "c": 9,
        "d": 35,
        "e": 19,
        "n": 0
      },
      "ensemble": {
        "a": 8,
        "b": 6,
        "c": 15,
        "d": 31,
        "e": 20,
        "n": 0
      },
      "reanalyse": {
        "a": 8,
        "b": 14,
        "c": 12,
        "d": 27,
        "e": 19,
        "n": 0
      }
    },
    "exclus_communs": 0
  },
  "<100 km": {
    "n": 47,
    "taux": {
      "controle": 0.44680851063829785,
      "ensemble": 0.5106382978723404,
      "reanalyse": 0.3191489361702128
    },
    "ic": {
      "controle": [
        0.31343283582089554,
        0.6428571428571429
      ],
      "ensemble": [
        0.40298507462686567,
        0.6666666666666666
      ],
      "reanalyse": [
        0.043478260869565216,
        0.6153846153846154
      ],
      "ecart": [
        -0.27999999999999997,
        0.045454545454545525
      ]
    },
    "exclusions": {
      "controle": {
        "a": 0,
        "b": 1,
        "c": 2,
        "d": 23,
        "e": 21,
        "n": 0
      },
      "ensemble": {
        "a": 0,
        "b": 0,
        "c": 3,
        "d": 20,
        "e": 24,
        "n": 0
      },
      "reanalyse": {
        "a": 0,
        "b": 1,
        "c": 4,
        "d": 27,
        "e": 15,
        "n": 0
      }
    },
    "exclus_communs": 0
  },
  ">300 km": {
    "n": 279,
    "taux": {
      "controle": 0.053763440860215055,
      "ensemble": 0.05734767025089606,
      "reanalyse": 0.07885304659498207
    },
    "ic": {
      "controle": [
        0.012776519593966109,
        0.11859262589928056
      ],
      "ensemble": [
        0.012776519593966109,
        0.12950574605250859
      ],
      "reanalyse": [
        0.023527113970588234,
        0.15139744054086682
      ],
      "ecart": [
        -0.010929460332655258,
        0.07182556951487172
      ]
    },
    "exclusions": {
      "controle": {
        "a": 20,
        "b": 97,
        "c": 122,
        "d": 25,
        "e": 15,
        "n": 0
      },
      "ensemble": {
        "a": 20,
        "b": 94,
        "c": 127,
        "d": 22,
        "e": 16,
        "n": 0
      },
      "reanalyse": {
        "a": 20,
        "b": 96,
        "c": 118,
        "d": 23,
        "e": 22,
        "n": 0
      }
    },
    "exclus_communs": 0
  },
  "aucun cyclone": {
    "n": 19,
    "taux": {
      "controle": 0.42105263157894735,
      "ensemble": 0.42105263157894735,
      "reanalyse": 0.3157894736842105
    },
    "ic": {
      "controle": [
        0.0,
        0.8888888888888888
      ],
      "ensemble": [
        0.0,
        0.8888888888888888
      ],
      "reanalyse": [
        0.0,
        0.6666666666666666
      ],
      "ecart": [
        -0.2222222222222222,
        0.0
      ]
    },
    "exclusions": {
      "controle": {
        "a": 0,
        "b": 8,
        "c": 3,
        "d": 0,
        "e": 8,
        "n": 0
      },
      "ensemble": {
        "a": 0,
        "b": 8,
        "c": 3,
        "d": 0,
        "e": 8,
        "n": 0
      },
      "reanalyse": {
        "a": 0,
        "b": 8,
        "c": 4,
        "d": 1,
        "e": 6,
        "n": 0
      }
    },
    "exclus_communs": 0
  }
}
```
