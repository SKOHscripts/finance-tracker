#!/usr/bin/env python3
"""Applique les vetos d'actualite au verdict du scan.

Lit le verdict de state/latest_scan.json, les drapeaux de
state/news_flags.json et les regles de docs/playbook/veto.toml, puis ecrit
state/latest_verdict.json.

Un veto ne declenche jamais un mouvement. Il ne fait que le suspendre : le
verdict final vaut CONSERVER, ROTATION, TEMPORISER ou SUSPENDU, et SUSPENDU
ne peut sortir que d'un ROTATION ou d'un TEMPORISER retenu.

Le veto s'applique position par position. Une nouvelle sur la cible suspend
toutes les rotations vers elle ; une nouvelle sur un refuge ne touche que les
temporisations.

Le script n'interprete rien. Le jugement est en amont, quand l'agente classe
une observation dans une categorie du playbook.

Aucune dependance externe. Python 3.11+.

Usage:
    python scripts/apply_news_veto.py [--today AAAA-MM-JJ] [--quiet]
"""

import argparse
import json
import sys
import tomllib
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Verdicts qu'un veto peut suspendre. CONSERVER n'est jamais suspendu : ne rien
# faire ne demande aucune route de swap.
SUSPENDABLE = {"ROTATION", "TEMPORISER"}

ROLES = ("cible", "detenu", "refuge")


def parse_day(value, champ):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Date invalide dans {champ} : {value!r}. Format attendu AAAA-MM-JJ."
            ) from exc


def resolve_roles(scan, position):
    """Associe chaque role a un identifiant CoinGecko, ou None, pour une position.

    Le scan est celui produit par `finance-tracker crypto-scan --json`. Le
    refuge vit sous `detail.temporisation.refuge_id`, et n'existe que si la
    temporisation a ete evaluee : quand une rotation passe, elle ne l'est pas.
    """
    detail = position.get("detail") or {}
    temp = detail.get("temporisation") or {}
    refuge = temp.get("refuge_id") if temp.get("applicable") else None
    candidate = (scan.get("candidate") or {}).get("id")
    return {
        "detenu": position.get("id"),
        "cible": position.get("candidate_id") or candidate,
        "refuge": refuge,
    }


def flag_is_eligible(flag, cfg_veto, today):  # pylint: disable=unused-argument
    """Renvoie (eligible, motif_du_rejet)."""
    for champ in ("date", "categorie"):
        if not flag.get(champ):
            return False, f"champ '{champ}' manquant"
    if cfg_veto["require_approved"] and flag.get("statut") != "approuve":
        return False, f"statut '{flag.get('statut', 'absent')}', approbation requise"
    if not flag.get("sources"):
        return False, "aucune source"
    return True, None


def rule_matches(rule, flag, roles):
    """Le drapeau touche-t-il le role vise par la regle."""
    if rule["categorie"] != flag["categorie"]:
        return False
    portee = rule["portee"]
    if portee == "marche":
        return flag.get("portee") == "marche"
    if portee in ROLES:
        cible = roles.get(portee)
        return cible is not None and cible in (flag.get("actifs") or [])
    raise RuntimeError(f"Portee inconnue dans veto.toml : {portee!r}")


def evaluate(verdict, flags, rules, cfg_veto, roles, today):
    applied, ignored = [], []

    for flag in flags:
        eligible, motif = flag_is_eligible(flag, cfg_veto, today)
        if not eligible:
            ignored.append({"id": flag.get("id"), "raison": motif})
            continue

        flag_day = parse_day(flag["date"], f"drapeau {flag.get('id')}")
        matched = False
        for rule in rules:
            if not rule_matches(rule, flag, roles):
                continue
            matched = True
            expire = flag_day + timedelta(days=rule["duree_jours"])
            if expire < today:
                ignored.append({
                    "id": flag.get("id"),
                    "raison": f"expire le {expire.isoformat()}, regle {rule['categorie']}/{rule['portee']}",
                })
                continue
            if verdict not in rule["suspend"]:
                ignored.append({
                    "id": flag.get("id"),
                    "raison": f"regle {rule['categorie']}/{rule['portee']} ne suspend pas {verdict}",
                })
                continue
            applied.append({
                "drapeau": flag.get("id"),
                "categorie": flag["categorie"],
                "portee_regle": rule["portee"],
                "actifs": flag.get("actifs") or [],
                "date_evenement": flag["date"],
                "expire_le": expire.isoformat(),
                "jours_restants": (expire - today).days,
                "motif": rule["motif"],
                "sources": flag.get("sources"),
            })
        if not matched:
            ignored.append({
                "id": flag.get("id"),
                "raison": f"aucune regle pour '{flag['categorie']}' sur les roles de ce scan",
            })

    final = "SUSPENDU" if applied else verdict
    return final, applied, ignored


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", default=str(ROOT / "state" / "latest_scan.json"))
    parser.add_argument("--flags", default=str(ROOT / "state" / "news_flags.json"))
    parser.add_argument("--rules", default=str(ROOT / "docs" / "playbook" / "veto.toml"))
    parser.add_argument("--out", default=str(ROOT / "state" / "latest_verdict.json"))
    parser.add_argument("--today", help="Force la date d'evaluation. Pour les tests.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    scan_path = Path(args.scan)
    if not scan_path.exists():
        raise SystemExit(
            f"Scan absent : {scan_path}. Lance d'abord finance-tracker crypto-scan --json > state/latest_scan.json."
        )
    scan = json.loads(scan_path.read_text(encoding="utf-8"))

    with open(args.rules, "rb") as fh:
        veto_cfg = tomllib.load(fh)

    today = parse_day(args.today, "--today") if args.today else date.today()

    flags_path = Path(args.flags)
    flags = json.loads(flags_path.read_text(encoding="utf-8")) if flags_path.exists() else []

    enabled = veto_cfg["veto"]["enabled"]
    rules = veto_cfg.get("regle", []) if enabled else []

    lignes = []
    for position in scan.get("positions", []):
        verdict = position.get("verdict")
        if not enabled:
            final, applied = verdict, []
            ignored = [{"id": f.get("id"), "raison": "veto.enabled est faux"} for f in flags]
            roles = resolve_roles(scan, position)
        else:
            roles = resolve_roles(scan, position)
            final, applied, ignored = evaluate(
                verdict, flags, rules, veto_cfg["veto"], roles, today)
        lignes.append({
            "id": position.get("id"),
            "symbol": position.get("symbol"),
            "verdict_scan": verdict,
            "verdict_final": final,
            "roles": roles,
            "vetos_appliques": applied,
            "drapeaux_ecartes": ignored,
        })

    # Verdict global : l'etat le plus engageant present sur une position.
    # SUSPENDU passe devant CONSERVER pour que le blocage reste visible.
    ordre = {"ROTATION": 3, "TEMPORISER": 2, "SUSPENDU": 1, "CONSERVER": 0}
    final_global = max((l["verdict_final"] for l in lignes),
                       key=lambda v: ordre.get(v, 0)) if lignes else None

    report = {
        "evaluated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "evaluation_date": today.isoformat(),
        "verdict_scan": scan.get("verdict"),
        "verdict_final": final_global,
        "candidate_id": scan.get("candidate_id"),
        "positions": lignes,
        "drapeaux_lus": len(flags),
        "regles_lues": len(rules),
        "scan_genere_le": scan.get("generated_at"),
    }
    Path(args.out).write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        print()


if __name__ == "__main__":
    main()
