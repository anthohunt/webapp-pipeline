// Fabriqué par tests/fabriquer-fixtures.py depuis le vrai programme. Ne pas éditer à la main.
import type { Vue } from '../types'

export const VUE_NEUF: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 1,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "en_cours",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": null,
     "citation": null,
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "ouverte"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  }
 ],
 "liens": {
  "maquette": null,
  "app": null,
  "video": null
 },
 "construction": null,
 "tour": 0,
 "tours": [],
 "close": false,
 "lance_le": null,
 "version_video": null,
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": {
  "quoi": "le pitch de l’app (le tien ou celui du client)",
  "sous_etape": "E1.1"
 },
 "sous_etape_courante": "E1.1",
 "consigne": "Le prochain message de l'utilisateur EST le pitch (le module le valide tout seul, mot pour mot). Ne demande jamais « que voulez-vous faire ? ».",
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 },
 "neuf": true
} as Vue

export const VUE_A_VALIDER: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 1,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "Une app pour partager les frais de trajet",
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "a_valider",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": true
      }
     ],
     "decisions": [
      {
       "a": "2026-10-26T10:19:00Z",
       "sous_etape": "E1.2",
       "resume": "Usage en voiture, à plusieurs",
       "citation": "en voiture, à 3 ou 4",
       "option": "A"
      }
     ]
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "ouverte"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  }
 ],
 "liens": {
  "maquette": null,
  "app": null,
  "video": null
 },
 "construction": null,
 "tour": 0,
 "tours": [],
 "close": false,
 "lance_le": null,
 "version_video": null,
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": {
  "quoi": "valider les questions d'usage",
  "sous_etape": "E1.2"
 },
 "sous_etape_courante": "E1.2",
 "consigne": "Quelques questions sur l'USAGE seulement (qui s'en sert, quand, pour quoi faire, ce qui compte le plus), une à la fois, au plus 5, chacune en A/B/C/D. Écris docs/pipeline/concept.md, résume-le en 3 à 5 points, passe en a_valider et demande A) oui c'est ça / B) je corrige / C) il manque quelque chose / D) autre chose, précise-moi.",
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 }
} as Vue

export const VUE_TEST_MAQUETTE: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 1,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "Une app pour partager les frais de trajet",
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "A",
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": true
      }
     ],
     "decisions": [
      {
       "a": "2026-10-26T10:19:00Z",
       "sous_etape": "E1.2",
       "resume": "Usage en voiture, à plusieurs",
       "citation": "en voiture, à 3 ou 4",
       "option": "A"
      }
     ]
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "en_cours",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "ouverte"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  }
 ],
 "liens": {
  "maquette": "https://maquettes.example.org/design/covoiturage-facile/",
  "app": null,
  "video": null
 },
 "construction": null,
 "tour": 0,
 "tours": [],
 "close": false,
 "lance_le": null,
 "version_video": null,
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": {
  "quoi": "faire tester la maquette au client",
  "sous_etape": "E1.7"
 },
 "sous_etape_courante": "E1.7",
 "consigne": "Le client parcourt la maquette. Chaque remarque se corrige en direct et se republie aussitôt (même lien), une remarque à la fois. Tiens docs/pipeline/design/validation.md (remarques mot pour mot + ce qui a changé). La sous-étape se valide sur le « c'est bon » explicite de l'utilisateur, cité mot pour mot : sur ce « c'est bon », ne redemande rien, passe E1.7 en a_valider puis validee avec cette citation et enchaîne la spécification (E1.8).",
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 }
} as Vue

export const VUE_A_LANCER: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 2,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "Une app pour partager les frais de trajet",
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "A",
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": true
      }
     ],
     "decisions": [
      {
       "a": "2026-10-26T10:19:00Z",
       "sous_etape": "E1.2",
       "resume": "Usage en voiture, à plusieurs",
       "citation": "en voiture, à 3 ou 4",
       "option": "A"
      }
     ]
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "c'est bon pour lui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "gate vert",
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  }
 ],
 "liens": {
  "maquette": "https://maquettes.example.org/design/covoiturage-facile/",
  "app": null,
  "video": null
 },
 "construction": null,
 "tour": 0,
 "tours": [],
 "close": false,
 "lance_le": null,
 "version_video": null,
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": {
  "quoi": "lancer la construction",
  "action": "lancer"
 },
 "sous_etape_courante": null,
 "consigne": null,
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 }
} as Vue

export const VUE_CONSTRUCTION: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 2,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "Une app pour partager les frais de trajet",
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "A",
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": true
      }
     ],
     "decisions": [
      {
       "a": "2026-10-26T10:19:00Z",
       "sous_etape": "E1.2",
       "resume": "Usage en voiture, à plusieurs",
       "citation": "en voiture, à 3 ou 4",
       "option": "A"
      }
     ]
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "c'est bon pour lui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "gate vert",
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "en_cours",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "ouverte"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  }
 ],
 "liens": {
  "maquette": "https://maquettes.example.org/design/covoiturage-facile/",
  "app": null,
  "video": null
 },
 "construction": {
  "en_cours": true,
  "phase": "jalons",
  "tour": 0,
  "bloque": null,
  "jalon_courant": "M2",
  "jalons": [
   {
    "id": "M1",
    "titre": "Prix",
    "statut": "fait"
   },
   {
    "id": "M2",
    "titre": "Trajet",
    "statut": "en-cours"
   }
  ]
 },
 "tour": 0,
 "tours": [],
 "close": false,
 "lance_le": "2026-10-26T10:19:01Z",
 "version_video": null,
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": null,
 "sous_etape_courante": "E2.1",
 "consigne": "Lancée par le bouton du volet ou l'outil `lancer`. Rien à faire en conversation : le volet suit l'avancement.",
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 }
} as Vue

export const VUE_BLOQUEE: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 2,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "Une app pour partager les frais de trajet",
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "A",
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": true
      }
     ],
     "decisions": [
      {
       "a": "2026-10-26T10:19:00Z",
       "sous_etape": "E1.2",
       "resume": "Usage en voiture, à plusieurs",
       "citation": "en voiture, à 3 ou 4",
       "option": "A"
      }
     ]
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "c'est bon pour lui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "gate vert",
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "bloquee",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "ouverte"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "a_faire",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "fermee"
  }
 ],
 "liens": {
  "maquette": "https://maquettes.example.org/design/covoiturage-facile/",
  "app": null,
  "video": null
 },
 "construction": {
  "en_cours": false,
  "phase": "jalons",
  "tour": 0,
  "bloque": "relances épuisées sur M2",
  "jalons": [
   {
    "id": "M1",
    "titre": "Prix",
    "statut": "fait"
   },
   {
    "id": "M2",
    "titre": "Trajet",
    "statut": "en-cours"
   }
  ]
 },
 "tour": 0,
 "tours": [],
 "close": false,
 "lance_le": "2026-10-26T10:19:01Z",
 "version_video": null,
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": {
  "quoi": "construction bloquée : relances épuisées sur M2",
  "action": "lancer"
 },
 "sous_etape_courante": "E2.1",
 "consigne": "Lancée par le bouton du volet ou l'outil `lancer`. Rien à faire en conversation : le volet suit l'avancement.",
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 }
} as Vue

export const VUE_REVUE: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 3,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "Une app pour partager les frais de trajet",
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "A",
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": true
      }
     ],
     "decisions": [
      {
       "a": "2026-10-26T10:19:00Z",
       "sous_etape": "E1.2",
       "resume": "Usage en voiture, à plusieurs",
       "citation": "en voiture, à 3 ou 4",
       "option": "A"
      }
     ]
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "c'est bon pour lui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "gate vert",
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "en_cours",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "ouverte"
  }
 ],
 "liens": {
  "maquette": "https://maquettes.example.org/design/covoiturage-facile/",
  "app": "https://app.example",
  "video": "https://montage.example.org/essai/?code=abc"
 },
 "construction": {
  "en_cours": false,
  "phase": "fini",
  "tour": 0,
  "bloque": null,
  "jalons": [
   {
    "id": "M1",
    "titre": "Prix",
    "statut": "fait"
   }
  ],
  "app_url": "https://app.example",
  "video": {
   "url": "https://montage.example.org/essai/?code=abc",
   "version": "V1"
  }
 },
 "tour": 0,
 "tours": [],
 "close": false,
 "lance_le": "2026-10-26T10:19:01Z",
 "version_video": "V1",
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": {
  "quoi": "montrer la vidéo et l’app au client",
  "sous_etape": "E3.1"
 },
 "sous_etape_courante": "E3.1",
 "consigne": "Donne les deux liens (vidéo, app). L'utilisateur rapporte ce que dit le client. S'il dit que c'est bon : outil `revue` verdict good, citation mot pour mot. Sinon : reprends chaque retour un par un (une question à la fois si un retour est ambigu : quel écran, quel résultat attendu), puis outil `retours` avec la liste (dit = ses mots exacts, attendu = un critère vérifiable), puis outil `revue` verdict retours : la construction repart toute seule sur ces points.",
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 }
} as Vue

export const VUE_CLOSE: Vue = {
 "run": "covoiturage-facile-2026-10-27-090000",
 "projet": "covoiturage-facile",
 "workspace": "/var/lib/webapp-runs/covoiturage-facile-2026-10-27-090000",
 "etape_courante": 3,
 "etapes": [
  {
   "n": 1,
   "titre": "Concevoir",
   "resume": "Du pitch à une maquette cliquable validée par le client, avec le cahier des charges, le parcours utilisateur et les user stories, puis la spécification complète en autonomie.",
   "sous_etapes": [
    {
     "id": "E1.1",
     "titre": "Le pitch",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "Une app pour partager les frais de trajet",
     "sorties": [],
     "decisions": []
    },
    {
     "id": "E1.2",
     "titre": "Les questions d'usage",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "A",
     "sorties": [
      {
       "chemin": "docs/pipeline/concept.md",
       "existe": true
      }
     ],
     "decisions": [
      {
       "a": "2026-10-26T10:19:00Z",
       "sous_etape": "E1.2",
       "resume": "Usage en voiture, à plusieurs",
       "citation": "en voiture, à 3 ou 4",
       "option": "A"
      }
     ]
    },
    {
     "id": "E1.3",
     "titre": "Le cahier des charges",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:00Z",
     "valide_le": "2026-10-26T10:19:00Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/cahier-des-charges.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.4",
     "titre": "Le parcours utilisateur",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/parcours-utilisateur.json",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/parcours-utilisateur.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.5",
     "titre": "Les user stories",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/stories-v1.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.6",
     "titre": "La maquette",
     "qui": "agent",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "oui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/mockup.html",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/mockup-public-url.txt",
       "existe": true
      },
      {
       "chemin": "docs/pipeline/design/screens.json",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.7",
     "titre": "Le test de la maquette",
     "qui": "moi",
     "etat": "validee",
     "depuis": "2026-10-26T10:19:01Z",
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "c'est bon pour lui",
     "sorties": [
      {
       "chemin": "docs/pipeline/design/validation.md",
       "existe": true
      }
     ],
     "decisions": []
    },
    {
     "id": "E1.8",
     "titre": "La spécification",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": "2026-10-26T10:19:01Z",
     "citation": "gate vert",
     "sorties": [
      {
       "chemin": "docs/pipeline/stories.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/roadmap-approved.json",
       "existe": false
      },
      {
       "chemin": "docs/pipeline/stack-decisions.md",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  },
  {
   "n": 2,
   "titre": "Construire",
   "resume": "L'app se construit seule sur le serveur, un groupe d'écrans à la fois (un agent construit, un vérificateur indépendant rejoue les histoires), puis la vidéo de démonstration se tourne et se publie.",
   "sous_etapes": [
    {
     "id": "E2.1",
     "titre": "La construction",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "docs/pipeline/app-url.txt",
       "existe": false
      }
     ],
     "decisions": []
    },
    {
     "id": "E2.2",
     "titre": "La vidéo",
     "qui": "programme",
     "etat": "validee",
     "depuis": null,
     "valide_le": null,
     "citation": null,
     "sorties": [
      {
       "chemin": "video/video-url.txt",
       "existe": false
      },
      {
       "chemin": "video/versions.json",
       "existe": false
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  },
  {
   "n": 3,
   "titre": "Revue",
   "resume": "Le client regarde la vidéo et teste l'app. « Good » clôt la run ; sinon ses retours relancent la construction sur ces seuls points, et la vidéo passe à la version suivante.",
   "sous_etapes": [
    {
     "id": "E3.1",
     "titre": "La revue du client",
     "qui": "moi",
     "etat": "validee",
     "depuis": null,
     "valide_le": null,
     "citation": "c'est parfait",
     "sorties": [
      {
       "chemin": "docs/pipeline/revue.json",
       "existe": true
      }
     ],
     "decisions": []
    }
   ],
   "etat": "faite"
  }
 ],
 "liens": {
  "maquette": "https://maquettes.example.org/design/covoiturage-facile/",
  "app": "https://app.example",
  "video": "https://montage.example.org/essai/?code=abc"
 },
 "construction": {
  "en_cours": false,
  "phase": "fini",
  "tour": 0,
  "bloque": null,
  "jalons": [
   {
    "id": "M1",
    "titre": "Prix",
    "statut": "fait"
   }
  ],
  "app_url": "https://app.example",
  "video": {
   "url": "https://montage.example.org/essai/?code=abc",
   "version": "V1"
  }
 },
 "tour": 0,
 "tours": [
  {
   "tour": 1,
   "verdict": "good",
   "date": "2026-10-26T10:19:02Z",
   "citation": "c'est parfait",
   "version_video": "V1"
  }
 ],
 "close": true,
 "lance_le": "2026-10-26T10:19:01Z",
 "version_video": "V1",
 "regles": [
  "Une seule question par message ; toute question à choix est en A/B/C avec une option D « autre chose, précise-moi » écrite en clair parmi les autres.",
  "Jamais de question technique pendant qu'on parle d'usage : note-la dans docs/pipeline/questions-techniques.md, la spécification la tranchera seule.",
  "Ne pose pas une question dont la réponse se déduit du pitch ou d'une décision déjà prise : tranche et dis-le en une ligne.",
  "Chaque choix de l'utilisateur s'enregistre avec l'outil `decision`, ses mots exacts en citation, sous sa sous-étape.",
  "Une sous-étape « agent » se présente (outil `avancer`, etat « a_valider ») puis n'est validée (« validee ») que sur une réponse explicite de l'utilisateur, citée mot pour mot.",
  "Réponses courtes : le résultat d'abord, en points, sans préambule ni conclusion qui répète.",
  "Quand l'utilisateur demande de revenir sur une sous-étape (souvent depuis le volet), appelle l'outil `rouvrir` avec sa raison, et reprends-la.",
  "Pas de squelette (skeleton) dans ce mode : le pitch et les questions d'usage se font en texte, la maquette d'E1.6 est le seul support visuel ; n'écris pas docs/pipeline/skeleton-url.txt, aucun contrôle ne le demande."
 ],
 "attend": null,
 "sous_etape_courante": null,
 "consigne": null,
 "brief": {
  "noeud": "concevoir",
  "sys": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/sys.md",
  "brief": "/tmp/tmptwh0yhlf/flux/state/webapp/covoiturage-facile-2026-10-27-090000/concevoir/brief.md"
 }
} as Vue
