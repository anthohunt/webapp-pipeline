// Le pont vers le programme du module (programme/webapp.py) : en local sur le serveur des runs, par SSH ailleurs.
// Les paramètres passent en JSON sur l'entrée standard (aucun échappement de shell), la réponse revient en JSON.
// Fonctions pures : l'appel lui-même (qui tient $) est dans register.tsx.

/** Emplacement du programme sur le serveur des runs : réglage `programme` du module (voir le README du dépôt). */
export const PROGRAMME_DEFAUT = '/opt/webapp-pipeline/mod/programme/webapp.py'
export let PROGRAMME = PROGRAMME_DEFAUT
export function reglerProgramme(chemin: string | undefined): void {
  PROGRAMME = chemin || PROGRAMME_DEFAUT
}

export type Reponse<T> = { ok: true; resultat: T } | { ok: false; refus: string }

/** Le client SSH sous Windows : celui de Git (l'OpenSSH de Windows lancé par Claude Code reste bloqué, essai du 15/10). */
export const SSH_WINDOWS = 'C:\\Program Files\\Git\\usr\\bin\\ssh.exe'

/** La ligne de commande : python3 en local, sinon SSH vers l'hôte (l'utilisateur qui possède les runs). */
export function argvPour(local: boolean, hote: string, commande: string, ssh = 'ssh'): string[] {
  if (local) return ['python3', '-B', PROGRAMME, commande]
  return [
    ssh, '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', hote,
    `python3 -B ${PROGRAMME} ${commande}`,
  ]
}

/** La réponse du programme : sa dernière ligne JSON, ou un refus lisible. */
export function lireReponse<T>(stdout: string, stderr: string, code: number): Reponse<T> {
  const ligne = stdout.trim().split('\n').pop() ?? ''
  if (!ligne) return { ok: false, refus: `Programme muet (code ${code}) : ${stderr.trim().slice(0, 300)}` }
  try {
    return JSON.parse(ligne) as Reponse<T>
  } catch {
    return { ok: false, refus: `Réponse illisible du programme : ${ligne.slice(0, 300)}` }
  }
}

/** « Covoiturage Facile » → « covoiturage-facile » : la même règle que le programme. */
export function slug(texte: string): string {
  return texte.toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40)
}
