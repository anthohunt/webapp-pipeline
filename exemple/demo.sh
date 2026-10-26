#!/usr/bin/env bash
# Démonstration de bout en bout, sans compte Claude : tout ce que la pipeline fait AVANT de lancer un agent.
#
#   bash exemple/demo.sh
#
# 1. crée une run « covoiturage-facile » (projet inventé) avec le moteur flux ;
# 2. écrit le brief du nœud « concevoir » : objectif, check-list et consignes (skills/) injectées ;
# 3. passe le contrôle de fin d'étape 1 sur la run vide : rouge, avec la liste de ce qui manque ;
# 4. remplit un second espace de travail avec les livrables d'une run finie (exemple inventé)
#    et passe les contrôles du parcours, de la construction et de la revue : verts ;
# 5. lit l'état de la construction (tools/webapp-etat.py) ;
# 6. demande au lanceur de l'étape 2 ce qu'il ferait (--dry-run) : il refuse, l'étape 1 n'a rien livré.
# La suite (conversation de conception, agents de construction) exige Claude Code connecté à un compte.
set -euo pipefail
ICI="$(cd "$(dirname "$0")/.." && pwd)"
export WEBAPP_PIPELINE_HOME="${WEBAPP_PIPELINE_HOME:-$ICI}"
export FLUX_HOME="${FLUX_HOME:-$ICI/vendor/flux}"
export FLUX_WORKFLOWS_DIR="${FLUX_WORKFLOWS_DIR:-$WEBAPP_PIPELINE_HOME/workflows}"
export FLUX_SKILLS_DIR="${FLUX_SKILLS_DIR:-$WEBAPP_PIPELINE_HOME/skills}"
export FLUX_VALIDATORS_PATH="${FLUX_VALIDATORS_PATH:-$WEBAPP_PIPELINE_HOME/validators}"
export WEBAPP_VIDEO="${WEBAPP_VIDEO:-0}"
[ -f "$FLUX_HOME/runtime/run-node.py" ] || { echo "moteur flux introuvable : FLUX_HOME=$FLUX_HOME (voir le README)"; exit 1; }

titre() { printf '\n== %s\n' "$1"; }

titre "1. Nouvelle run"
WS="$(python3 "$FLUX_HOME/runtime/new-run.py" webapp covoiturage-facile | tail -1)"
echo "workspace : $WS"

titre "2. Brief du nœud « concevoir » (étape interactive : le moteur ne la lance pas)"
python3 "$FLUX_HOME/runtime/run-node.py" webapp concevoir --workspace "$WS" --brief-only
ETAT="${FLUX_STATE_DIR:-$FLUX_HOME/state}/webapp/$(basename "$WS")/concevoir"
echo "brief : $(wc -c < "$ETAT/brief.md") octets ; consignes injectées : $(grep -c '^# Pipeline Step\|^# Étape\|^# pipeline-step' "$ETAT/sys.md" || true) skill(s)"

titre "3. Contrôle de fin d'étape 1 sur la run vide (rouge attendu)"
if python3 "$FLUX_HOME/runtime/validate.py" webapp-concevoir "$WS" 2> "$WS/gate.txt"; then
  echo "inattendu : vert"; exit 1
fi
echo "rouge, $(grep -c '^ *[0-9]' "$WS/gate.txt" || true) défaut(s) ; les trois premiers :"
grep '^ *[0-9]' "$WS/gate.txt" | head -3

titre "4. Livrables d'une run finie (exemple inventé), contrôles des étapes"
FINI="$(mktemp -d)/covoiturage-facile-fini"
python3 -c "import pathlib, sys; sys.path.insert(0, '$WEBAPP_PIPELINE_HOME/tests'); import test_webapp_3_etapes as t; t.fabriquer(pathlib.Path('$FINI'))"
for v in webapp-parcours webapp-construire webapp-revue; do
  python3 "$FLUX_HOME/runtime/validate.py" "$v" "$FINI" 2>/dev/null && echo "$v : vert" || { echo "$v : rouge"; exit 1; }
done

titre "5. État de la construction"
python3 "$WEBAPP_PIPELINE_HOME/tools/webapp-etat.py" "$FINI"

titre "6. Lanceur de l'étape 2, à blanc, sur la run vide"
python3 "$WEBAPP_PIPELINE_HOME/tools/webapp-lancer.py" "$WS" --dry-run || true

titre "Fin"
echo "Tout ce qui précède tourne sans compte. La suite — la conversation de conception (/webapp-start dans Claude Code)"
echo "et les agents de construction (webapp-lancer.py sans --dry-run) — exige Claude Code connecté à un compte."
