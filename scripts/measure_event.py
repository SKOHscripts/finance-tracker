#!/usr/bin/env python3
"""Mesure la trajectoire de marche autour d'un evenement du playbook.

Interroge CoinGecko et renvoie le rendement de l'actif sur les fenetres
demandees, en absolu et en relatif a un actif de reference. Sert a remplir le
tableau d'une fiche du playbook avec des chiffres releves plutot que des
chiffres de memoire.

Le relatif compte plus que l'absolu : un actif qui perd 12 % pendant que la
reference perd 14 % n'a rien subi de particulier.

Aucune dependance externe. Python 3.11+.

Usage:
    python scripts/measure_event.py --asset monero --date 2024-02-20
    python scripts/measure_event.py --asset usd-coin --date 2023-03-10 --peg
"""

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests

API = "https://api.coingecko.com/api/v3"

# Le plan gratuit CoinGecko ne sert que les 365 derniers jours d'historique.
FREE_PLAN_DAYS = 365


def http_get(path, params, api_key=None, retries=4):
    """GET CoinGecko avec backoff. Renvoie le JSON decode.

    Utilise `requests` comme le reste du projet plutot que urllib : l'URL est
    construite a partir d'une constante de module, donc le schema ne peut pas
    deriver vers file:// ou un protocole exotique.
    """
    headers = {"Accept": "application/json", "User-Agent": "crypto-signal/1.0"}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    delay = 2.0
    for attempt in range(retries):
        try:
            response = requests.get(
                f"{API}{path}", params=params, headers=headers, timeout=30
                )
            if response.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            if response.status_code >= 400:
                raise RuntimeError(
                    f"CoinGecko HTTP {response.status_code} sur {path}"
                    )
            return response.json()
        except requests.exceptions.RequestException as exc:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"Reseau indisponible sur {path}: {exc}") from exc
    raise RuntimeError(f"Echec apres {retries} tentatives sur {path}")


def daily_closes(prices):
    by_day = {}
    for ts_ms, price in prices:
        day = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()
        by_day[day] = price
    return by_day


def fetch_series(coin_id, start, end, api_key):
    params = {
        "vs_currency": "usd",
        "from": int(datetime.combine(start, datetime.min.time(), timezone.utc).timestamp()),
        "to": int(datetime.combine(end, datetime.max.time(), timezone.utc).timestamp()),
    }
    payload = http_get(f"/coins/{coin_id}/market_chart/range", params, api_key)
    closes = daily_closes(payload.get("prices", []))
    if not closes:
        raise RuntimeError(
            f"Aucune donnee pour '{coin_id}' entre {start} et {end}. "
            "Verifie l'identifiant CoinGecko et la fenetre demandee."
        )
    return closes


def price_on(closes, target):
    """Cloture du jour, ou du jour utile le plus proche dans les 3 jours suivants."""
    for offset in range(0, 4):
        day = target + timedelta(days=offset)
        if day in closes:
            return closes[day], day
    for offset in range(1, 4):
        day = target - timedelta(days=offset)
        if day in closes:
            return closes[day], day
    return None, None


def pct(new, old):
    return None if not old else (new / old - 1.0) * 100.0


def measure(asset_closes, bench_closes, event_day, windows, pre_days):
    base_a, base_day = price_on(asset_closes, event_day)
    base_b, _ = price_on(bench_closes, event_day)
    if base_a is None:
        raise RuntimeError(f"Pas de cotation pour l'actif autour du {event_day}.")

    rows = []
    pre_a, _ = price_on(asset_closes, event_day - timedelta(days=pre_days))
    pre_b, _ = price_on(bench_closes, event_day - timedelta(days=pre_days))
    if pre_a is not None:
        abs_pre = pct(base_a, pre_a)
        rel_pre = None
        if pre_b is not None and base_b is not None:
            rel_pre = abs_pre - pct(base_b, pre_b)
        rows.append({"fenetre": f"J-{pre_days}", "absolu": abs_pre, "relatif": rel_pre})

    for w in windows:
        after_a, _ = price_on(asset_closes, event_day + timedelta(days=w))
        after_b, _ = price_on(bench_closes, event_day + timedelta(days=w))
        abs_move = pct(after_a, base_a) if after_a is not None else None
        rel_move = None
        if abs_move is not None and after_b is not None and base_b is not None:
            bench_move = pct(after_b, base_b)
            rel_move = None if bench_move is None else abs_move - bench_move
        rows.append({"fenetre": f"J+{w}", "absolu": abs_move, "relatif": rel_move})

    return base_day, rows


def peg_deviation(closes, event_day, windows):
    """Ecart au peg, pour un stablecoin. Un stable ne se lit pas en momentum."""
    rows = []
    for offset in [0] + list(windows):
        price, day = price_on(closes, event_day + timedelta(days=offset))
        if price is None:
            continue
        rows.append({
            "fenetre": "J+0" if offset == 0 else f"J+{offset}",
            "prix": price,
            "ecart_peg_pct": (price - 1.0) * 100.0,
            "jour_retenu": day.isoformat(),
        })
    return rows


def fmt(value):
    return "" if value is None else f"{value:+.2f} %"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, help="Identifiant CoinGecko, ex. monero")
    parser.add_argument("--date", required=True, help="Date de l'evenement, AAAA-MM-JJ")
    parser.add_argument("--benchmark", default="bitcoin", help="Actif de reference du relatif")
    parser.add_argument("--windows", default="1,7,30", help="Fenetres apres l'evenement, en jours")
    parser.add_argument("--pre", type=int, default=30,
                        help="Fenetre avant l'evenement, pour detecter l'anticipation")
    parser.add_argument("--peg", action="store_true",
                        help="Mesure l'ecart au peg au lieu du rendement. Pour un stablecoin.")
    parser.add_argument("--json", action="store_true", help="Sortie JSON au lieu du tableau")
    args = parser.parse_args()

    try:
        event_day = date.fromisoformat(args.date)
    except ValueError as exc:
        raise SystemExit(
            f"Date invalide : {args.date!r}. Format attendu AAAA-MM-JJ."
            ) from exc

    windows = [int(w) for w in args.windows.split(",") if w.strip()]
    api_key = os.environ.get("COINGECKO_API_KEY")

    age = (date.today() - event_day).days
    if age > FREE_PLAN_DAYS and not api_key:
        raise SystemExit(
            f"Evenement vieux de {age} jours. Le plan gratuit CoinGecko ne sert que "
            f"{FREE_PLAN_DAYS} jours d'historique.\n"
            "Renseigne COINGECKO_API_KEY avec une cle donnant acces a l'historique "
            "long, ou laisse la fiche en statut a_mesurer. Ne remplis pas le tableau "
            "de memoire."
        )
    if event_day > date.today():
        raise SystemExit(f"Evenement dans le futur : {event_day}. Rien a mesurer.")

    start = event_day - timedelta(days=args.pre + 5)
    end = min(event_day + timedelta(days=max(windows) + 5), date.today())

    asset_closes = fetch_series(args.asset, start, end, api_key)
    time.sleep(2.5)

    if args.peg:
        rows = peg_deviation(asset_closes, event_day, windows)
        out = {"asset": args.asset, "date": args.date, "mode": "peg", "rows": rows}
        if args.json:
            json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
            print()
            return
        print(f"\n{args.asset} — ecart au peg autour du {args.date}\n")
        print("| Fenetre | Prix | Ecart au peg |")
        print("|---------|------|--------------|")
        for r in rows:
            print(f"| {r['fenetre']:<7} | {r['prix']:.4f} | {r['ecart_peg_pct']:+.2f} % |")
        print("\nJours retenus :", ", ".join(f"{r['fenetre']}={r['jour_retenu']}" for r in rows))
        return

    bench_closes = fetch_series(args.benchmark, start, end, api_key)
    base_day, rows = measure(asset_closes, bench_closes, event_day, windows, args.pre)

    out = {
        "asset": args.asset,
        "benchmark": args.benchmark,
        "date": args.date,
        "jour_de_base_retenu": base_day.isoformat(),
        "mode": "rendement",
        "rows": rows,
    }
    if args.json:
        json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return

    print(f"\n{args.asset} autour du {args.date}, relatif a {args.benchmark}")
    if base_day != event_day:
        print(f"Jour de base retenu : {base_day} (pas de cotation le {event_day})")
    print()
    ref = args.benchmark.upper()
    entete = f"Relatif {ref}"
    print(f"| Fenetre | Absolu | {entete} |")
    print(f"|---------|--------|{'-' * (len(entete) + 2)}|")
    for r in rows:
        print(f"| {r['fenetre']:<7} | {fmt(r['absolu']):>8} | {fmt(r['relatif']):>{len(entete)}} |")
    print("\nColle ce tableau dans la fiche, puis ecris la trajectoire retenue")
    print("en une phrase, au passe, sans extrapolation.")


if __name__ == "__main__":
    main()
