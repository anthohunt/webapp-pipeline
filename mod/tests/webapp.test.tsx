import { describe, expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'

import { VUE_A_LANCER, VUE_A_VALIDER, VUE_BLOQUEE, VUE_CLOSE, VUE_CONSTRUCTION, VUE_NEUF, VUE_REVUE, VUE_TEST_MAQUETTE } from './fixtures'

const BASE = { sections: [{ id: 'intro', text: 'base', scope: 'shared' as const }] }
const COMPOSE = { model: 'claude-opus-5-5', promptModel: 'claude-opus-5-5', surfaces: [], tools: [], outputStyle: null, traits: [] }
const OUTIL = 'mcp__webapp__'
const PANE = { plugin: 'webapp', component: 'Pane', requestId: 'webapp', props: { title: 'Web app', isFocused: true, bodyColumns: 90, placement: 'dock', scroll: { offset: 0, bodyRows: 60 }, view: {} } } as const
const BANDE = { plugin: 'webapp', component: 'AbovePrompt', requestId: 'band', props: { bodyColumns: 160 } } as const

type Appel = { commande: string; args: Record<string, unknown> }

/** Le monde sous le mod : le programme répond par commande (vues fabriquées par le vrai programme). */
function monde(on: On, reponses: Record<string, unknown>) {
  const appels: Appel[] = []
  const outils: string[] = []
  const soumis: string[] = []
  const toasts: string[] = []
  mock.store(on)
  mock.clock(on, { now: Date.parse('2026-10-27T09:00:00Z') })
  mock.env(on, {})
  on('fs.stat', async () => ({ value: { kind: 'file', size: 1, mtimeMs: 0 } }) as never)
  on('process.run', async (_$, e) => {
    const commande = String(e.argv[e.argv.length - 1])
    const args = JSON.parse(String(e.init?.stdin ?? '{}')) as Record<string, unknown>
    appels.push({ commande, args })
    const r = typeof reponses[commande] === 'function' ? (reponses[commande] as () => unknown)() : reponses[commande] ?? {}
    return { value: { exitCode: 0, stdout: JSON.stringify(r && (r as { refus?: string }).refus ? { ok: false, refus: (r as { refus: string }).refus } : { ok: true, resultat: r }) + '\n', stderr: '' } } as never
  })
  on('tool.register', async (_$, e) => (outils.push((e as { name: string }).name), { value: { tool: `${OUTIL}${(e as { name: string }).name}` } }) as never)
  on('ui.open', async () => ({ value: { isPlaced: true } }) as never)
  on('ui.close', async () => ({ value: undefined }) as never)
  on('ui.toast', async (_$, e) => (toasts.push(String((e as { text?: string }).text ?? e)), { value: undefined }) as never)
  on('command.register', async () => ({ value: undefined }) as never)
  on('session.id', async () => ({ value: 'session-test' }) as never)
  on('session.start', async (_$, e) => ({ cwd: (e as { cwd: string }).cwd }) as never)
  on('prompt.compose', () => BASE)
  on('prompt.submit', async (_$, e) => (soumis.push(e.text), { text: e.text }) as never)
  return { appels, outils, soumis, toasts }
}

const ouvrir = (args: string) => ({ command: 'webapp', args, origin: { kind: 'composer' }, presentation: { isFullscreen: true, columns: 160 } }) as never
const sections = async ($: { prompt: { compose: (i: never) => Promise<{ sections: readonly { id: string; text: string }[] }> } }) => (await $.prompt.compose(COMPOSE as never)).sections

describe('seule la session rattachée est une session web app', () => {
  test('session non rattachée : même prompt système, aucun outil, outil refusé', async ($, on) => {
    const { appels, outils } = monde(on, {})
    await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' } as never)
    expect((await sections($ as never)).map(s => s.id)).toEqual(['intro'])
    expect(outils).toEqual([])
    expect(appels).toEqual([])
    const r = await $.tool.call({ tool: `${OUTIL}avancer`, sous_etape: 'E1.2', etat: 'a_valider' } as never)
    expect(JSON.stringify(r)).toContain("n'est pas rattachée")
  })

  test('/webapp <projet> rattache : bienvenue, outils, consignes ; /webapp off détache', async ($, on) => {
    const { appels, outils } = monde(on, { ouvrir: VUE_NEUF, etat: VUE_NEUF })
    await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' } as never)
    const r = await $.command.run(ouvrir('Covoiturage Facile'))
    expect(r.text).toContain('Donne le pitch')
    expect(appels[0]).toEqual({ commande: 'ouvrir', args: { projet: 'covoiturage-facile', session: 'session-test' } })
    expect(outils).toEqual(['etat', 'decision', 'avancer', 'rouvrir', 'cloturer', 'lancer', 'retours', 'revue', 'lire'])
    const s = await sections($ as never)
    expect(s.map(x => x.id)).toEqual(['intro', 'webapp:protocole'])
    expect(s[1]?.text).toContain(VUE_NEUF.workspace)
    expect(s[1]?.text).toContain('sous-étape E1.1 — Le pitch')
    expect(s[1]?.text).toContain('« autre chose, précise-moi »')
    expect(s[1]?.text).toContain(VUE_NEUF.brief.sys)
    const off = await $.command.run(ouvrir('off'))
    expect(off.text).toContain('session normale')
    expect((await sections($ as never)).map(x => x.id)).toEqual(['intro'])
  })

  test('une session déjà rattachée se rattache seule au redémarrage', async ($, on) => {
    const { appels } = monde(on, { ouvrir: VUE_A_VALIDER, etat: VUE_A_VALIDER })
    await $.command.run(ouvrir('covoiturage-facile'))
    await $.session.start({ surface: 'desktop', isInteractive: true, cwd: '/work' } as never)
    expect(appels.filter(a => a.commande === 'ouvrir').length).toBe(2)
    expect((await sections($ as never)).map(x => x.id)).toContain('webapp:protocole')
  })
})

describe('étape 1 — concevoir', () => {
  test('le premier message après l’ouverture est le pitch, mot pour mot', async ($, on) => {
    const { appels } = monde(on, { ouvrir: VUE_NEUF, etat: VUE_A_VALIDER, pitch: {} })
    await $.command.run(ouvrir('covoiturage-facile'))
    await $.prompt.submit({ text: 'Une app pour partager les frais de trajet', origin: { kind: 'composer' } } as never)
    expect(appels.find(a => a.commande === 'pitch')?.args).toEqual({ run: VUE_NEUF.run, citation: 'Une app pour partager les frais de trajet' })
    await $.prompt.submit({ text: 'A', origin: { kind: 'composer' } } as never)
    expect(appels.filter(a => a.commande === 'pitch').length).toBe(1)
  })

  test("un outil de l'agent passe au programme avec la run de la session", async ($, on) => {
    const { appels } = monde(on, { ouvrir: VUE_A_VALIDER, etat: VUE_A_VALIDER, decision: { decision: { citation: 'en voiture' } } })
    await $.command.run(ouvrir('covoiturage-facile'))
    const r = await $.tool.call({ tool: `${OUTIL}decision`, sous_etape: 'E1.2', resume: 'Usage en voiture', citation: 'en voiture', option: 'A' } as never)
    expect(JSON.stringify(r)).toContain('en voiture')
    expect(appels.find(a => a.commande === 'decision')?.args).toEqual({ run: VUE_A_VALIDER.run, sous_etape: 'E1.2', resume: 'Usage en voiture', citation: 'en voiture', option: 'A' })
  })

  test('un refus du programme revient à l’agent, lisible', async ($, on) => {
    monde(on, { ouvrir: VUE_A_VALIDER, etat: VUE_A_VALIDER, cloturer: { refus: 'contrôle de l’étape 1 rouge — C12 : parcours sans écran' } })
    await $.command.run(ouvrir('covoiturage-facile'))
    const r = await $.tool.call({ tool: `${OUTIL}cloturer` } as never)
    expect(JSON.stringify(r)).toContain('C12 : parcours sans écran')
  })

  test('volet : ce qui attend en tête, étape 1 dépliée, décision et fichier ouvrable', async ($, on) => {
    const { appels } = monde(on, { ouvrir: VUE_A_VALIDER, etat: VUE_A_VALIDER, lire: { contenu: '# Concept', chemin: 'docs/pipeline/concept.md' } })
    await $.command.run(ouvrir('covoiturage-facile'))
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({ ...PANE, surface })
      expect(await ui.find({ type: 'Text', text: 'À toi :' })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /valider les questions d'usage/ })).toBeDefined()
      for (const [i, titre] of ['Concevoir', 'Construire', 'Revue'].entries()) expect((await ui.find({ key: `basculer-${i + 1}` }))?.text).toContain(titre)
      expect(await ui.find({ type: 'Text', text: /^▾ 1\. Concevoir$/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /Usage en voiture, à plusieurs/ })).toBeDefined()
      expect(await ui.find({ type: 'Text', text: /Le cahier des charges/ })).toBeDefined()
      await ui.press({ key: 'f-docs/pipeline/concept.md' })
      expect(appels.find(a => a.commande === 'lire')?.args).toEqual({ run: VUE_A_VALIDER.run, chemin: 'docs/pipeline/concept.md' })
    }
  })

  test('test de la maquette : le lien se montre et se copie', async ($, on) => {
    monde(on, { ouvrir: VUE_TEST_MAQUETTE, etat: VUE_TEST_MAQUETTE })
    await $.command.run(ouvrir('covoiturage-facile'))
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    expect(await ui.find({ type: 'Text', text: /faire tester la maquette au client/ })).toBeDefined()
    expect(await ui.find({ type: 'Link' })).toBeDefined()
    expect(await ui.find({ key: 'copier-maquette' })).toBeDefined()
  })
})

describe('étape 2 — construire', () => {
  test('le bouton Lancer appelle le programme directement, sans passer par l’agent', async ($, on) => {
    let lance = false
    const { appels, soumis, toasts } = monde(on, {
      ouvrir: VUE_A_LANCER,
      etat: () => (lance ? VUE_CONSTRUCTION : VUE_A_LANCER),
      lancer: () => ((lance = true), { ok: true, mode: 'construction', tmux: 't' }),
    })
    await $.command.run(ouvrir('covoiturage-facile'))
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    expect((await ui.find({ key: 'lancer' }))?.text).toContain('Lancer la construction')
    await ui.press({ key: 'lancer' })
    expect(appels.find(a => a.commande === 'lancer')?.args).toEqual({ run: VUE_A_LANCER.run })
    expect(soumis).toEqual([])
    expect(toasts.join(' ')).toContain('construction lancée')
  })

  test('suivi : jalons au volet, compte dans la bande, toast au jalon fini', async ($, on) => {
    monde(on, { ouvrir: VUE_CONSTRUCTION, etat: VUE_CONSTRUCTION })
    await $.command.run(ouvrir('covoiturage-facile'))
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
    expect(await ui.find({ type: 'Text', text: /la construction avance seule/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^✓ M1 Prix$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^▶ M2 Trajet$/ })).toBeDefined()
    const bande = await $.ui.mount({ ...BANDE, surface: 'terminal' } as never)
    expect(await bande.find({ type: 'Text', text: /jalons 1\/2/ })).toBeDefined()
  })

  test('bloquée : la raison en rouge et le bouton Relancer', async ($, on) => {
    monde(on, { ouvrir: VUE_BLOQUEE, etat: VUE_BLOQUEE })
    await $.command.run(ouvrir('covoiturage-facile'))
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    expect((await ui.find({ key: 'lancer' }))?.text).toContain('Relancer')
    expect(await ui.find({ type: 'Text', text: /Bloquée : relances épuisées sur M2/ })).toBeDefined()
  })
})

describe('étape 3 — revue', () => {
  test('liens app et vidéo, deux boutons qui parlent pour l’utilisateur', async ($, on) => {
    const { soumis } = monde(on, { ouvrir: VUE_REVUE, etat: VUE_REVUE })
    await $.command.run(ouvrir('covoiturage-facile'))
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    expect(await ui.find({ key: 'lien-app' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^Vidéo V1$/ })).toBeDefined()
    await ui.press({ key: 'retours' })
    expect(soumis).toEqual(['Le client a des retours, je te les donne.'])
    await ui.press({ key: 'good' })
    expect(soumis[1]).toContain("c'est good")
  })

  test('retours puis revue : arguments transmis tels quels', async ($, on) => {
    const { appels } = monde(on, { ouvrir: VUE_REVUE, etat: VUE_REVUE, retours: { tour: 1 }, revue: { tour: 1, verdict: 'retours' } })
    await $.command.run(ouvrir('covoiturage-facile'))
    const liste = [{ dit: 'la carte est vide', attendu: 'la carte montre les magasins à moins de 5 km', ecran: 'S1' }]
    await $.tool.call({ tool: `${OUTIL}retours`, retours: liste, citation: 'il dit que la carte est vide' } as never)
    await $.tool.call({ tool: `${OUTIL}revue`, verdict: 'retours', citation: 'il veut la carte' } as never)
    expect(appels.find(a => a.commande === 'retours')?.args).toEqual({ run: VUE_REVUE.run, retours: liste, citation: 'il dit que la carte est vide' })
    expect(appels.find(a => a.commande === 'revue')?.args).toEqual({ run: VUE_REVUE.run, verdict: 'retours', citation: 'il veut la carte' })
  })

  test('run close : livrée, plus rien n’attend', async ($, on) => {
    monde(on, { ouvrir: VUE_CLOSE, etat: VUE_CLOSE })
    await $.command.run(ouvrir('covoiturage-facile'))
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    expect(await ui.find({ type: 'Text', text: /Run close : le client a validé/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /tour 1 · vidéo V1/ })).toBeDefined()
    const bande = await $.ui.mount({ ...BANDE, surface: 'terminal' } as never)
    expect(await bande.find({ type: 'Text', text: /livrée/ })).toBeDefined()
  })
})
