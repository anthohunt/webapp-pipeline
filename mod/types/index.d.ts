// Contrat du mod webapp : ce que le volet et la bande lisent (la vue rendue par programme/webapp.py).

export type EtatSousEtape = 'a_faire' | 'en_cours' | 'a_valider' | 'validee' | 'bloquee'

export type Decision = {
  a: string
  sous_etape: string
  resume: string
  citation: string
  option?: string | null
}

export type SousEtape = {
  id: string
  titre: string
  qui: 'moi' | 'agent' | 'programme'
  etat: EtatSousEtape
  depuis?: string | null
  valide_le?: string | null
  citation?: string | null
  sorties: { chemin: string; existe: boolean }[]
  decisions: Decision[]
}

export type Etape = {
  n: number
  titre: string
  resume: string
  etat: 'ouverte' | 'fermee' | 'faite'
  sous_etapes: SousEtape[]
}

export type Jalon = { id: string; titre?: string; statut?: string }

/** Le suivi de l'étape 2, rendu par flux/tools/webapp-etat.py (contrat du 24/10). */
export type Construction = {
  indisponible?: string
  en_cours?: boolean
  phase?: string
  tour?: number
  jalon_courant?: string | null
  jalons?: Jalon[]
  app_url?: string | null
  video?: { url?: string | null; version?: string | null } | null
  bloque?: string | null
  derniere_passe?: Record<string, unknown> | null
}

export type Attente = { quoi: string; sous_etape?: string; action?: 'lancer' }

export type Tour = { tour: number; verdict: 'good' | 'retours'; date: string; citation: string; version_video?: string | null }

export type Vue = {
  run: string
  projet: string | null
  workspace: string
  etape_courante: number
  etapes: Etape[]
  liens: { maquette: string | null; app: string | null; video: string | null }
  construction: Construction | null
  tour: number
  tours: Tour[]
  close: boolean
  lance_le: string | null
  version_video: string | null
  attend: Attente | null
  sous_etape_courante: string | null
  consigne: string | null
  brief: { noeud: string; sys: string; brief: string }
  regles: string[]
  neuf?: boolean
}

/** Une session rattachée à une run : elle seule a le volet, la bande, les consignes et les outils. */
export type Rattachement = { run: string; projet: string; depuis: string }

export type Fichier = { chemin: string; contenu: string } | null

declare module 'claude-code' {
  interface PluginState {
    webapp: {
      rattachement: Rattachement | null
      vue: Vue | null
      erreur: string | null
      deplie: number[]
      fichier: Fichier
      local: boolean | null
      ssh: string | null
      occupe: string | null
    }
  }
}
