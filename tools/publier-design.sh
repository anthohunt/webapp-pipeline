#!/usr/bin/env bash
# publier-design.sh <workspace> [nom de run] — expose le squelette et le mockup en HTTP.
#
# Les artifacts claude.ai appartiennent au compte qui les publie et restent privés :
# une personne qui n'a pas ce compte ne peut pas ouvrir la page. Le test du mockup est
# la seule barrière humaine de l'étape — il ne peut pas dépendre d'un compte. On copie
# donc les deux pages dans un dossier servi par un serveur web public.
#
# Réglages (voir .env.example) :
#   DESIGN_PUBLISH_DIR  dossier local servi en HTTP (ex. /var/www/design)
#   PUBLIC_BASE_URL     son adresse publique (ex. https://maquettes.example.org/design)
set -euo pipefail
WS="${1:?usage: publier-design.sh <workspace> [nom de run]}"
# Le nom de run se passe explicitement : un dossier de transit ne doit pas donner son nom
# au dossier publié.
RUN="${2:-$(basename "$WS")}"
: "${DESIGN_PUBLISH_DIR:?réglage DESIGN_PUBLISH_DIR absent (dossier servi en HTTP), voir .env.example}"
: "${PUBLIC_BASE_URL:?réglage PUBLIC_BASE_URL absent (adresse publique de ce dossier), voir .env.example}"
DST="$DESIGN_PUBLISH_DIR/$RUN"
BASE="${PUBLIC_BASE_URL%/}/$RUN"

mkdir -p "$DST"
copie=0
for f in skeleton.html mockup.html; do
  if [ -f "$WS/docs/pipeline/design/$f" ]; then
    cp "$WS/docs/pipeline/design/$f" "$DST/$f"
    copie=1
  fi
done
[ "$copie" = 1 ] || { echo "rien à publier : aucun skeleton.html ni mockup.html dans $WS"; exit 1; }

# Une page d'entrée, pour n'avoir qu'une adresse à donner.
cat > "$DST/index.html" <<HTML
<!doctype html><meta charset="utf-8"><title>Design — $RUN</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:44rem;margin:3rem auto;padding:0 1.2rem;background:#faf9f6;color:#24211c}
a{display:block;padding:.9rem 1rem;margin:.5rem 0;border:1px solid #e4e0d8;border-radius:10px;background:#fff;color:inherit;text-decoration:none}
a:hover{border-color:#7a5c3a}small{color:#6b655c}</style>
<h1>Design — $RUN</h1>
<a href="mockup.html"><b>Le mockup</b><br><small>prototype cliquable + panneau des gestes — c'est ce qu'on teste</small></a>
<a href="skeleton.html"><b>Le squelette du cadrage</b><br><small>les écrans et les décisions qui les fixent</small></a>
HTML

chmod -R a+rX "$DST"
echo "$BASE/"
[ -f "$DST/mockup.html" ] && echo "$BASE/mockup.html"
[ -f "$DST/skeleton.html" ] && echo "$BASE/skeleton.html"
exit 0
