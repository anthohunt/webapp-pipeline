// Mode « web app » : conduit une run de la pipeline web app en 3 étapes (design :
// docs/2026-10-24-webapp-3-etapes-design.md). /webapp <projet> rattache CETTE session à la run du projet : elle
// seule reçoit le volet de suivi, la bande au-dessus de l'invite, les consignes de l'agent et ses outils. L'état vit
// dans les fichiers de la run sur le serveur, tenus par le programme (programme/webapp.py) ; le mod n'en garde qu'une
// copie pour dessiner.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Fichier, Rattachement, SousEtape, Vue } from '../types'
import { PROGRAMME, SSH_WINDOWS, argvPour, lireReponse, reglerProgramme, slug } from './programme'
import type { Reponse } from './programme'
import { ETAT, QUI, bienvenue, contexteReprise, heure, protocole } from './textes'

const PANE = 'webapp'
const PANE_FICHIER = 'webapp-fichier'
const HOTE_DEFAUT = 'utilisateur@serveur-des-runs'
const cleSession = (id: string) => `session:${id}`

const rattachement = atom({ plugin: 'webapp', key: 'rattachement' } as const, null)
const vue = atom({ plugin: 'webapp', key: 'vue' } as const, null)
const erreur = atom({ plugin: 'webapp', key: 'erreur' } as const, null)
const deplie = atom({ plugin: 'webapp', key: 'deplie' } as const, [])
const fichier = atom({ plugin: 'webapp', key: 'fichier' } as const, null)
const local = atom({ plugin: 'webapp', key: 'local' } as const, null)
const clientSsh = atom({ plugin: 'webapp', key: 'ssh' } as const, null)
const occupe = atom({ plugin: 'webapp', key: 'occupe' } as const, null)

// Les outils de l'agent, déclarés seulement quand la session se rattache. Chacun est une commande du programme.
type Outil = { nom: string; commande: string; description: string; schema: Record<string, unknown>; requis: string[] }
const OUTILS: Outil[] = [
  {
    nom: 'etat', commande: 'etat', requis: [],
    description: "Web app : l'état de la run (étapes, sous-étapes, ce qui attend l'utilisateur, construction, liens), lu dans ses fichiers.",
    schema: {},
  },
  {
    nom: 'decision', commande: 'decision', requis: ['sous_etape', 'resume', 'citation'],
    description: "Web app : enregistre un choix de l'utilisateur sous sa sous-étape (E1.2…E3.1), avec ses mots exacts et l'heure. `option` : la lettre choisie (A, B, C, D) ou « autre ».",
    schema: {
      sous_etape: { type: 'string', description: 'ex. E1.3' },
      resume: { type: 'string', description: 'Le choix, en une ligne' },
      citation: { type: 'string', description: "Les mots de l'utilisateur, mot pour mot" },
      option: { type: 'string', enum: ['A', 'B', 'C', 'D', 'autre'] },
    },
  },
  {
    nom: 'avancer', commande: 'avancer', requis: ['sous_etape', 'etat'],
    description: "Web app : change l'état d'une sous-étape de l'étape 1 (E1.2 à E1.7) : en_cours, a_valider (ton travail est présenté, il attend l'utilisateur), validee (seulement sur sa réponse explicite, citée mot pour mot). Les sorties de la sous-étape doivent exister. Valider ouvre la suivante.",
    schema: {
      sous_etape: { type: 'string' },
      etat: { type: 'string', enum: ['en_cours', 'a_valider', 'validee'] },
      citation: { type: 'string', description: "Obligatoire pour validee : la réponse de l'utilisateur, mot pour mot" },
    },
  },
  {
    nom: 'rouvrir', commande: 'rouvrir', requis: ['sous_etape', 'raison'],
    description: "Web app : rouvre une sous-étape de l'étape 1 (seulement à la demande de l'utilisateur, avant la construction) ; dis pourquoi.",
    schema: { sous_etape: { type: 'string' }, raison: { type: 'string' } },
  },
  {
    nom: 'cloturer', commande: 'cloturer', requis: [],
    description: "Web app : fin de l'étape 1 (après la spécification, E1.8). Le programme passe le contrôle du nœud 1 du moteur ; rouge = la liste de ce qui manque, à corriger avant de rappeler.",
    schema: {},
  },
  {
    nom: 'lancer', commande: 'lancer', requis: [],
    description: "Web app : lance l'étape 2 sur le serveur (construction, ou tour de retours), ou la relance si elle est bloquée.",
    schema: {},
  },
  {
    nom: 'retours', commande: 'retours', requis: ['retours', 'citation'],
    description: "Web app (étape 3) : enregistre les retours du client pour le tour suivant. Chaque retour : dit (ses mots exacts, rapportés par l'utilisateur), attendu (un critère vérifiable sur l'app), et si tu le sais histoire (US-x.y) et ecran (id de screens.json). Ensuite, outil `revue` verdict retours.",
    schema: {
      retours: {
        type: 'array',
        items: {
          type: 'object',
          properties: { dit: { type: 'string' }, attendu: { type: 'string' }, histoire: { type: 'string' }, ecran: { type: 'string' } },
          required: ['dit', 'attendu'],
        },
      },
      citation: { type: 'string', description: "Les mots de l'utilisateur qui transmet ces retours, mot pour mot" },
    },
  },
  {
    nom: 'revue', commande: 'revue', requis: ['verdict', 'citation'],
    description: "Web app (étape 3) : le verdict du client sur ce tour. good = la run est close ; retours = la construction repart toute seule sur les retours enregistrés (outil `retours` d'abord).",
    schema: {
      verdict: { type: 'string', enum: ['good', 'retours'] },
      citation: { type: 'string', description: "Les mots de l'utilisateur, mot pour mot" },
    },
  },
  {
    nom: 'lire', commande: 'lire', requis: ['chemin'],
    description: 'Web app : lit un fichier de la run (chemin relatif au workspace).',
    schema: { chemin: { type: 'string' } },
  },
]

/** Où joindre le programme : en local sur le serveur des runs, sinon par SSH (celui de Git sous Windows). */
async function transport($: EngineInterface): Promise<{ ici: boolean; ssh: string }> {
  let ici = await read($, local)
  let ssh = await read($, clientSsh)
  if (ici === null || ssh === null) {
    const existe = (chemin: string) => $.fs.stat(chemin).then(() => true, () => false)
    ici = await existe(PROGRAMME)
    ssh = (await existe(SSH_WINDOWS)) ? SSH_WINDOWS : 'ssh'
    const i = ici, c = ssh
    await update($, local, () => i)
    await update($, clientSsh, () => c)
  }
  return { ici, ssh }
}

/** Appelle une commande du programme ; un échec de transport devient un refus lisible, jamais une exception. */
async function appeler<T>($: EngineInterface, h: string, commande: string, args: Record<string, unknown>, timeoutMs = 60_000): Promise<Reponse<T>> {
  try {
    const { ici, ssh } = await transport($)
    const r = await $.process.run(argvPour(ici, h, commande, ssh), { stdin: JSON.stringify(args), timeoutMs })
    return lireReponse<T>(r.stdout, r.stderr, r.exitCode)
  } catch (err) {
    return { ok: false, refus: `Programme injoignable : ${String(err).slice(0, 300)}` }
  }
}

async function rafraichir($: EngineInterface, h: string): Promise<Vue | null> {
  const r = await read($, rattachement)
  if (!r) return null
  const avant = await read($, vue)
  const rep = await appeler<Vue>($, h, 'etat', { run: r.run })
  if (!rep.ok) {
    await update($, erreur, () => rep.refus)
    return avant
  }
  const v = rep.resultat
  await update($, vue, () => v)
  await update($, erreur, () => null)
  await signalerTransitions($, avant, v)
  return v
}

/** Ce qui vaut un toast : un jalon fini, la vidéo prête, une construction bloquée. */
async function signalerTransitions($: EngineInterface, avant: Vue | null, apres: Vue) {
  if (!avant) return
  const fait = (v: Vue) => new Set((v.construction?.jalons ?? []).filter(j => j.statut === 'fait').map(j => j.id))
  const a = fait(avant)
  for (const j of apres.construction?.jalons ?? []) {
    if (j.statut === 'fait' && !a.has(j.id)) $.ui.toast(`Web app : jalon ${j.id}${j.titre ? ` (${j.titre})` : ''} construit.`)
  }
  if (apres.etape_courante === 3 && avant.etape_courante !== 3 && !apres.close) {
    $.ui.toast(`Web app : construction finie, la vidéo ${apres.version_video ?? ''} est prête pour la revue.`)
  }
  if (apres.construction?.bloque && !avant.construction?.bloque) $.ui.toast(`Web app : construction bloquée — ${apres.construction.bloque}`)
}

async function declarerOutils($: EngineInterface) {
  for (const o of OUTILS) {
    await $.tool.register({
      name: o.nom,
      description: o.description,
      isDeferred: false,
      inputSchema: { type: 'object', properties: o.schema, required: o.requis },
    })
  }
}

async function rattacher($: EngineInterface, h: string, projet: string): Promise<{ vue: Vue } | { refus: string }> {
  const session = await $.session.id()
  const rep = await appeler<Vue>($, h, 'ouvrir', { projet, session }, 180_000)
  if (!rep.ok) return { refus: rep.refus }
  const ratt: Rattachement = { run: rep.resultat.run, projet, depuis: new Date(await $.clock.now()).toISOString() }
  await update($, rattachement, () => ratt)
  await update($, vue, () => rep.resultat)
  await update($, erreur, () => null)
  await $.store.set(cleSession(session), ratt)
  await declarerOutils($)
  void $.ui.open({ id: PANE, title: `Web app — ${rep.resultat.projet ?? projet}` })
  return { vue: rep.resultat }
}

async function ouvrirFichier($: EngineInterface, h: string, run: string, chemin: string) {
  const rep = await appeler<{ contenu: string; chemin: string }>($, h, 'lire', { run, chemin })
  const f: Fichier = rep.ok ? { chemin, contenu: rep.resultat.contenu } : { chemin, contenu: rep.refus }
  await update($, fichier, () => f)
  await $.ui.open({ id: PANE_FICHIER, title: chemin })
}

/** Le bouton « Lancer » : direct, sans passer par l'agent (un geste, pas une conversation). */
async function lancer($: EngineInterface, h: string) {
  const r = await read($, rattachement)
  if (!r || (await read($, occupe))) return
  await update($, occupe, () => 'lancement…')
  const rep = await appeler<{ mode?: string }>($, h, 'lancer', { run: r.run }, 150_000)
  await update($, occupe, () => null)
  $.ui.toast(rep.ok ? `Web app : ${rep.resultat.mode === 'retours' ? 'tour de retours' : 'construction'} lancée sur le serveur.` : `Web app : ${rep.refus}`)
  await rafraichir($, h)
}

async function dire($: EngineInterface, texte: string) {
  await $.prompt.submit({ text: texte, asUser: true })
}

const REPERE: Record<string, string> = { a_faire: '○', en_cours: '▶', a_valider: '◆', validee: '✓', bloquee: '✗' }
const couleur = (etat: string) =>
  etat === 'en_cours' ? 'cyan' : etat === 'a_valider' ? 'yellow' : etat === 'validee' ? 'green' : etat === 'bloquee' ? 'red' : undefined
const JALON: Record<string, string> = { 'a-faire': '○', 'en-cours': '▶', fait: '✓' }

export const register: Register = (on, options) => {
  const H = typeof options?.hote === 'string' && options.hote ? options.hote : HOTE_DEFAUT
  reglerProgramme(typeof options?.programme === 'string' ? options.programme : undefined)

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'webapp',
      description: 'Web app : ouvrir ou reprendre la run d’un projet dans cette session (volet de suivi, 3 étapes)',
      argumentHint: '<projet> | off',
    })
    const session = await $.session.id()
    const connu = (await $.store.get(cleSession(session))) as Rattachement | undefined
    if (connu) await rattacher($, H, connu.projet)
    $.clock.every(30_000, () => void rafraichir($, H))
    return next(e)
  })

  on('command.run', { command: 'webapp' }, async ($, e) => {
    const arg = e.args.trim()
    const r = await read($, rattachement)
    if (arg === 'off') {
      if (!r) return { text: "Cette session n'est rattachée à aucune run web app." }
      await update($, rattachement, () => null)
      await update($, vue, () => null)
      await $.store.delete(cleSession(await $.session.id()))
      await $.ui.close({ id: PANE })
      await $.ui.close({ id: PANE_FICHIER })
      return { text: `Session détachée de la run « ${r.run} » : elle redevient une session normale.` }
    }
    if (arg === '') {
      if (r) {
        await $.ui.open({ id: PANE, title: `Web app — ${r.projet}` })
        const v = await rafraichir($, H)
        return { text: `Run « ${r.run} » — ce qui t'attend : ${v?.attend?.quoi ?? 'rien'}.` }
      }
      const rep = await appeler<{ runs: { run: string; projet: string | null }[] }>($, H, 'liste', {})
      const liste = rep.ok ? rep.resultat.runs.map(x => x.projet ?? x.run) : []
      return { text: `Ouvre un projet : /webapp <projet>.${liste.length ? ` Projets existants : ${[...new Set(liste)].join(', ')}.` : ''}` }
    }
    const projet = slug(arg)
    if (!projet) return { text: 'Nom de projet invalide.' }
    if (r && r.projet !== projet) return { text: `Cette session est déjà rattachée au projet « ${r.projet} » : /webapp off d'abord.` }
    const res = await rattacher($, H, projet)
    if ('refus' in res) return { text: `Le module n'a pas pu ouvrir le projet : ${res.refus}` }
    const v = res.vue
    const pitchOuvert = v.etapes[0]?.sous_etapes.find(x => x.id === 'E1.1')?.etat === 'en_cours'
    if (v.neuf || pitchOuvert) {
      return {
        text: bienvenue(v),
        context: ["Le mode web app vient d'ouvrir la run ; le message de bienvenue ci-dessus est affiché. Ne pose aucune question : le prochain message de l'utilisateur est le pitch (le module l'enregistre seul). Lis d'abord les consignes du graphe indiquées dans tes consignes."],
      }
    }
    return { text: `Projet « ${projet} » repris (run ${v.run}) — ce qui t'attend : ${v.attend?.quoi ?? 'rien'}.`, context: [contexteReprise(v)] }
  })

  on('prompt.compose', async ($, e, next) => {
    const res = await next(e)
    const r = await read($, rattachement)
    const v = await read($, vue)
    if (!r || !v) return res
    return { sections: [...res.sections, { id: 'webapp:protocole', text: protocole(v), scope: 'session' as const }] }
  })

  on('prompt.submit', async ($, e, next) => {
    const r = await read($, rattachement)
    const kind = e.origin?.kind
    const parUtilisateur = kind === 'composer' || kind === 'bridge' || kind === 'sdk'
    if (!r || !parUtilisateur || e.text.trim().startsWith('/')) return next(e)
    const v = await read($, vue)
    // E1.1 : le premier message après l'ouverture est le pitch, gardé mot pour mot.
    if (v?.etapes[0]?.sous_etapes.find(s => s.id === 'E1.1')?.etat === 'en_cours') {
      const rep = await appeler($, H, 'pitch', { run: r.run, citation: e.text.trim() })
      if (rep.ok) await rafraichir($, H)
    }
    return next(e)
  })

  for (const o of OUTILS) {
    on('tool.call', { tool: `mcp__webapp__${o.nom}` }, async ($, e) => {
      const r = await read($, rattachement)
      if (!r) return { deny: "Cette session n'est pas rattachée à une run web app (/webapp <projet>)." }
      const { tool: _t, tool_use_id: _id, ...args } = e as unknown as Record<string, unknown>
      const long = o.commande === 'cloturer' || o.commande === 'lancer' || o.commande === 'revue'
      const rep = await appeler<Record<string, unknown>>($, H, o.commande, { ...args, run: r.run }, long ? 330_000 : 60_000)
      if (!rep.ok) return { result: `Refusé : ${rep.refus}` }
      const v = await rafraichir($, H)
      if (o.commande === 'etat') return { result: v ? protocole(v) : 'État illisible.' }
      if (o.commande === 'lire') return { result: String(rep.resultat.contenu ?? '') }
      return { result: JSON.stringify(rep.resultat) + (v ? `\nCe qui attend l'utilisateur maintenant : ${v.attend?.quoi ?? 'rien'}.` : '') }
    })
  }

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const r = await read($, rattachement)
    if (!r) return next(e)
    const v = await read($, vue)
    const { Box, Text } = $.ui.resolve(e)
    const et = v?.etapes.find(x => x.n === v.etape_courante)
    const c = v?.construction
    const jalons = c?.jalons ?? []
    const suivi = v && v.etape_courante === 2 && v.lance_le && !c?.bloque
      ? ` · ${v.tour > 0 ? `tour de retours ${v.tour}${c?.phase === 'tournage' ? ', tournage de la vidéo' : ''}` : c?.phase === 'tournage' ? 'tournage de la vidéo' : `jalons ${jalons.filter(j => j.statut === 'fait').length}/${jalons.length || '?'}`}`
      : ''
    return (
      <Box>
        <Text color="cyan">Web app</Text>
        <Text dimColor>
          {' '}· {v?.projet ?? r.projet}
          {v?.close ? ' · livrée' : et ? ` · étape ${et.n} ${et.titre}` : ''}
          {suivi}
          {v?.attend ? ` · t'attend : ${v.attend.quoi}` : ''}
        </Text>
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button, Link } = $.ui.resolve(e)
    const r = await read($, rattachement)
    const v = await read($, vue)
    const err = await read($, erreur)
    const deplies = await read($, deplie)
    const occ = await read($, occupe)
    if (!r) return <Text dimColor>Aucune run web app rattachée à cette session (/webapp &lt;projet&gt;).</Text>
    if (!v) return <Text color={err ? 'red' : undefined} dimColor={!err}>{err ? `Programme injoignable : ${err}` : 'Lecture de la run…'}</Text>
    const c = v.construction
    const e31 = v.etapes[2]?.sous_etapes[0]
    const lien = (cle: string, titre: string, url: string | null) =>
      url ? (
        <Box key={`lien-${cle}`} flexDirection="row" gap={1}>
          <Text bold>{titre}</Text>
          <Link href={url} label={url.replace(/^https?:\/\//, '').slice(0, 60)} />
          <Button key={`copier-${cle}`} plain onPress={press => void $.ui.copy({ text: url, surface: press.surface })}>
            <Text color="cyan">copier</Text>
          </Button>
        </Box>
      ) : null
    const ligne = (s: SousEtape) => (
      <Box key={`se-${s.id}`} flexDirection="column" paddingLeft={2}>
        <Text dimColor={s.etat === 'a_faire'}>
          <Text color={couleur(s.etat)}>{REPERE[s.etat] ?? '○'}</Text> {s.titre}
          {s.etat === 'a_valider' || s.etat === 'bloquee' ? <Text color={couleur(s.etat)}> · {ETAT[s.etat]}</Text> : null}
          {s.qui !== 'moi' && s.etat !== 'validee' ? <Text dimColor> · {QUI[s.qui]}</Text> : null}
        </Text>
        {s.decisions.length && s.etat !== 'a_faire' ? (
          <Text key={`dec-${s.id}`} dimColor>  {(s.decisions[s.decisions.length - 1]?.resume ?? "").slice(0, 80)}</Text>
        ) : null}
        {s.sorties.filter(x => x.existe && /\.(md|json)$/.test(x.chemin)).length && s.etat !== 'a_faire' ? (
          <Box key={`sorties-${s.id}`} flexDirection="row" gap={1} paddingLeft={2}>
            {s.sorties.filter(x => x.existe && /\.(md|json)$/.test(x.chemin)).map(x => (
              <Button key={`f-${x.chemin}`} plain onPress={() => ouvrirFichier($, H, v.run, x.chemin)}>
                <Text color="cyan">↳ {(x.chemin.split('/').pop() ?? x.chemin).replace(/\.(md|json)$/, '')}</Text>
              </Button>
            ))}
          </Box>
        ) : null}
      </Box>
    )
    return (
      <Box flexDirection="column" gap={1} paddingX={1}>
        <Text bold>
          Web app · {v.projet ?? v.run}
          {v.tour ? <Text dimColor> · tour {v.tour}</Text> : null}
          {v.close ? <Text color="green"> · livrée</Text> : null}
          {err ? <Text color="red"> · relevé en retard</Text> : null}
        </Text>
        {v.attend ? (
          <Box key="attend" flexDirection="column" borderStyle="round" borderColor="yellow" paddingX={1}>
            <Text>
              <Text bold color="yellow">À toi :</Text> {v.attend.quoi}
            </Text>
            {v.attend.action === 'lancer' ? (
              <Button key="lancer" variant="primary" onPress={() => lancer($, H)}>
                {occ ?? (c?.bloque ? 'Relancer' : 'Lancer la construction')}
              </Button>
            ) : null}
            {v.attend.sous_etape === 'E3.1' ? (
              <Box key="revue" flexDirection="row" gap={1}>
                <Button key="good" variant="primary" onPress={() => dire($, "Le client a vu la vidéo et testé l'app : c'est good.")}>
                  C'est bon
                </Button>
                <Button key="retours" onPress={() => dire($, "Le client a des retours, je te les donne.")}>
                  Il a des retours
                </Button>
              </Box>
            ) : null}
          </Box>
        ) : v.close ? (
          <Text color="green">Run close : le client a validé.</Text>
        ) : (
          <Text dimColor>Rien ne t'attend{v.etape_courante === 2 ? ' : la construction avance seule' : ''}.</Text>
        )}
        {v.liens.maquette || v.liens.app || v.liens.video ? (
          <Box key="liens" flexDirection="column">
            {lien('maquette', 'Maquette', v.liens.maquette)}
            {lien('app', 'App', v.liens.app)}
            {lien('video', `Vidéo${v.version_video ? ` ${v.version_video}` : ''}`, v.liens.video)}
          </Box>
        ) : null}
        {v.etapes.map(et => {
          const ouverte = (et.n === v.etape_courante) !== deplies.includes(et.n)
          return (
            <Box key={`etape-${et.n}`} flexDirection="column">
              <Button
                key={`basculer-${et.n}`}
                plain
                onPress={() => update($, deplie, l => (l.includes(et.n) ? l.filter(n => n !== et.n) : [...l, et.n]))}
              >
                <Text bold={et.n === v.etape_courante} dimColor={et.etat === 'fermee'}>
                  {ouverte ? '▾' : '▸'} {et.n}. {et.titre}
                </Text>
                {et.etat === 'faite' ? <Text color="green"> ✓</Text> : null}
              </Button>
              {ouverte
                ? et.sous_etapes.flatMap(se => {
                    const l = [ligne(se)]
                    // Les jalons se rangent sous la sous-étape « La construction », avant la vidéo.
                    if (se.id === 'E2.1' && c && !c.indisponible && (c.jalons ?? []).length) l.push(
                      <Box key="jalons" flexDirection="column" paddingLeft={4}>
                        {(c.jalons ?? []).map(j => (
                          <Text key={`jalon-${j.id}`} dimColor={j.statut === 'a-faire'}>
                            <Text color={j.statut === 'fait' ? 'green' : j.statut === 'en-cours' ? 'cyan' : undefined}>{JALON[j.statut ?? ''] ?? '○'}</Text> {j.id}
                            {j.titre ? ` ${j.titre}` : ''}
                          </Text>
                        ))}
                      </Box>
                    )
                    return l
                  })
                : null}
              {ouverte && et.n === 2 && c?.bloque ? (
                <Text key="bloque" color="red">  Bloquée : {c.bloque}</Text>
              ) : null}
              {ouverte && et.n === 2 && c?.indisponible ? (
                <Text key="indispo" dimColor>  Suivi indisponible : {c.indisponible}</Text>
              ) : null}
              {ouverte && et.n === 3 && v.tours.length ? (
                <Box key="tours" flexDirection="column" paddingLeft={4}>
                  {v.tours.map(t => (
                    <Text key={`tour-${t.tour}`}>
                      <Text color={t.verdict === 'good' ? 'green' : 'yellow'}>{t.verdict === 'good' ? '✓' : '↺'}</Text> tour {t.tour}
                      {t.version_video ? ` · vidéo ${t.version_video}` : ''} · {heure(t.date)} <Text dimColor>« {t.citation.slice(0, 60)} »</Text>
                    </Text>
                  ))}
                </Box>
              ) : null}
              {ouverte && et.n === 3 && e31?.etat === 'a_faire' && !v.close ? (
                <Text key="attente-revue" dimColor>    s'ouvre quand la vidéo est prête</Text>
              ) : null}
            </Box>
          )
        })}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE_FICHIER }, async ($, e) => {
    const { Box, Text, Markdown, Code } = $.ui.resolve(e)
    const f = await read($, fichier)
    if (!f) return <Text dimColor>Aucun fichier ouvert.</Text>
    return (
      <Box flexDirection="column" paddingX={1}>
        {f.chemin.endsWith('.md') ? <Markdown text={f.contenu} /> : <Code language="json" source={f.contenu} />}
      </Box>
    )
  })
}
