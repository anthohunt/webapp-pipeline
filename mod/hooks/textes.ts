// Les textes du mod : les consignes de l'agent (prompt système de la session rattachée) et les messages à
// l'utilisateur. Fonctions pures, testées par les tests du mod.

import type { Vue } from '../types'

export const ETAT: Record<string, string> = {
  a_faire: 'à faire', en_cours: 'en cours', a_valider: 'à valider', validee: 'validée', bloquee: 'bloquée',
}

export const QUI: Record<string, string> = { moi: 'toi', agent: 'Claude, tu valides', programme: 'automatique' }

/** « 2026-10-27T09:14:00Z » → « 09:14 » (heure de Paris). */
export function heure(iso: string | null | undefined): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Paris' })
  } catch {
    return iso.slice(11, 16)
  }
}

export function bienvenue(v: Vue): string {
  return [
    `Web app « ${v.projet ?? v.run} » — run ${v.run} ouverte.`,
    '',
    '3 étapes : 1. Concevoir (ici, avec le client) · 2. Construire (seul, sur le serveur, avec la vidéo) · 3. Revue (le client regarde la vidéo et teste l’app).',
    '',
    'Donne le pitch de l’app : le tien, ou celui du client, avec ses mots.',
  ].join('\n')
}

export function contexteReprise(v: Vue): string {
  const derniere = v.etapes.flatMap(e => e.sous_etapes).flatMap(s => s.decisions).slice(-1)[0]
  return [
    `Reprise de la run ${v.run} (projet ${v.projet ?? '?'}), étape ${v.etape_courante}.`,
    v.sous_etape_courante ? `Sous-étape en cours : ${v.sous_etape_courante}.` : '',
    derniere ? `Dernière décision (${derniere.sous_etape}) : ${derniere.resume} — « ${derniere.citation} ».` : '',
    `Ce qui attend l'utilisateur : ${v.attend?.quoi ?? 'rien'}.`,
    'Relis les fichiers de la run avant de répondre ; résume en 3 à 5 lignes où on en est, puis reprends.',
  ].filter(Boolean).join('\n')
}

/** Le protocole de l'agent : ajouté au prompt système de la seule session rattachée. */
export function protocole(v: Vue): string {
  const courante = v.etapes.flatMap(e => e.sous_etapes).find(s => s.id === v.sous_etape_courante)
  const lignes = [
    '# Mode web app (module webapp)',
    '',
    `Cette session conduit la run **${v.run}** de la pipeline web app (projet « ${v.projet ?? '?'} »).`,
    `Workspace de la run (travaille DEDANS, tous les chemins y sont relatifs) : ${v.workspace}`,
    '',
    '## Les 3 étapes',
    '1. **Concevoir** — en conversation avec l’utilisateur (souvent avec le client à côté) : pitch, questions d’usage, cahier des charges, parcours utilisateur, user stories, maquette cliquable, test de la maquette par le client, puis spécification en autonomie.',
    '2. **Construire** — automatique sur le serveur (bouton du volet ou outil `lancer`) : un groupe d’écrans à la fois, un constructeur puis un vérificateur indépendant ; puis la vidéo de démonstration (mod tournage) publiée sur la table de montage.',
    '3. **Revue** — le client regarde la vidéo et teste l’app ; l’utilisateur te rapporte ses mots. « Good » clôt la run (outil `revue`) ; des retours (outil `retours` puis `revue`) relancent la construction sur ces seuls points.',
    '',
    `## Où on en est : étape ${v.etape_courante}${courante ? `, sous-étape ${courante.id} — ${courante.titre} (${ETAT[courante.etat] ?? courante.etat})` : ''}`,
    v.consigne ? `Consigne : ${v.consigne}` : '',
    v.attend ? `Ce qui attend l’utilisateur : ${v.attend.quoi}.` : 'Rien n’attend l’utilisateur.',
    v.tour ? `Tour de retours n°${v.tour}.` : '',
    '',
    '## Les consignes détaillées du graphe (étape 1)',
    `Au début de l’étape 1 et à chaque reprise, lis ${v.brief.sys} puis ${v.brief.brief} : ce sont les protocoles du nœud « ${v.brief.noeud} » du graphe flux (comment cadrer, dessiner, publier, spécifier). Ils priment pour le COMMENT ; ce module prime pour l’ORDRE des sous-étapes et les validations.`,
    '',
    '## Règles',
    ...v.regles.map(r => `• ${r}`),
    '• Écris à l’utilisateur avec de vraies puces « • », options A/B/C/D, jamais d’emoji, jamais de punchline.',
    '',
    '## Tes outils (module webapp)',
    '• `decision` : un choix de l’utilisateur, ses mots exacts, sous sa sous-étape.',
    '• `avancer` : en_cours → a_valider (tu présentes) → validee (sur sa réponse explicite, citée). Les sorties de la sous-étape doivent exister.',
    '• `rouvrir` : revenir sur une sous-étape de l’étape 1, avec la raison (avant la construction seulement).',
    '• `cloturer` : fin de l’étape 1, passe le contrôle du moteur ; s’il est rouge, corrige et rappelle-le.',
    '• `lancer` : démarre (ou relance, si bloquée) la construction sur le serveur.',
    '• `retours` puis `revue` : la revue du client (étape 3).',
    '• `etat` : relire l’état ; `lire` : lire un fichier de la run.',
  ]
  return lignes.filter((l, i, a) => l !== '' || a[i - 1] !== '').join('\n')
}
