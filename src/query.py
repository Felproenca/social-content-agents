"""
MarketingOS Reference Library — Query CLI

Uso:
  python -m src.query search "dark luxury saas"
  python -m src.query search --category sites/saas
  python -m src.query search --type competitor
  python -m src.query search --maturity stable --category motion/gsap
  python -m src.query get linear
  python -m src.query list
  python -m src.query stats
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
INDEX_FILE = ROOT / "index.json"


def load_index() -> list[dict]:
    data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return data["entries"]


def load_reference(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def search(
    keywords: list[str],
    category: str | None = None,
    ref_type: str | None = None,
    maturity: str | None = None,
) -> list[dict]:
    flat_kws = []
    for kw in keywords:
        flat_kws.extend(kw.lower().split())

    results = []
    for entry in load_index():
        if category and not entry["category"].startswith(category):
            continue
        if ref_type and entry["type"] != ref_type:
            continue
        if maturity and entry["maturity"] != maturity:
            continue

        if flat_kws:
            searchable = " ".join([
                entry.get("name", ""),
                entry.get("description", ""),
                " ".join(entry.get("tags", [])),
                " ".join(entry.get("tensions", [])),
            ]).lower()
            score = sum(1 for kw in flat_kws if kw in searchable)
            if score == 0:
                continue
            results.append((score, entry))
        else:
            results.append((0, entry))

    return [e for _, e in sorted(results, key=lambda x: -x[0])]


def search_for_agent(brief: dict) -> list[dict]:
    """
    Entry point para o MarketingOS.
    Recebe campos do brief e retorna referências relevantes ranqueadas.

    Campos suportados:
        sector         — setor da empresa (ex: "saas", "fintech", "beauty")
        style          — estilo visual desejado (ex: "dark", "clean", "editorial")
        mood           — mood/tom (ex: "luxury premium", "technical confident")
        tags           — lista de tags específicas
        industry       — nome da indústria
        acquisition_objective — o que está tentando resolver na aquisição
                                 (ex: "converter demanda existente", "gerar awareness",
                                  "reduzir fricção de avaliação", "construir confiança")
        bottleneck     — gargalo identificado (ex: "posicionamento", "confiança",
                          "fricção de conversão", "geração de demanda")
        stage          — etapa do funil (ex: "awareness", "consideration", "conversion")
        type           — tipo de referência (site, motion, visual, competitor, industry...)
        category       — categoria específica (ex: "motion/framer", "sites/saas")
        maturity       — nível de maturidade (default: "stable")

    Exemplo:
        refs = search_for_agent({
            "acquisition_objective": "reduzir fricção de avaliação",
            "bottleneck": "confiança",
            "sector": "fintech",
            "style": "dark"
        })
    """
    keywords = []
    for field in ["sector", "style", "mood", "tags", "industry",
                  "acquisition_objective", "bottleneck", "stage"]:
        val = brief.get(field)
        if val:
            if isinstance(val, list):
                keywords.extend(val)
            else:
                keywords.extend(str(val).split())

    results = search(
        keywords,
        category=brief.get("category"),
        ref_type=brief.get("type"),
        maturity=brief.get("maturity", "stable"),
    )

    # Boost entradas com acquisition_role quando há objetivo de aquisição
    if brief.get("acquisition_objective") or brief.get("bottleneck"):
        acq_kws = []
        for field in ["acquisition_objective", "bottleneck", "stage"]:
            val = brief.get(field)
            if val:
                acq_kws.extend(str(val).lower().split())

        boosted = []
        for entry in results:
            acq_role = entry.get("acquisition_role", "").lower()
            boost = sum(1 for kw in acq_kws if kw in acq_role)
            boosted.append((boost, entry))
        results = [e for _, e in sorted(boosted, key=lambda x: -x[0])]

    return results


# ── CLI commands ──────────────────────────────────────────────────────────────

def cmd_search(args: argparse.Namespace) -> None:
    results = search(
        args.keywords or [],
        category=args.category,
        ref_type=args.type,
        maturity=args.maturity,
    )
    if not results:
        print("Nenhuma referência encontrada.")
        return
    print(f"\n{len(results)} referência(s):\n")
    for entry in results:
        _print_entry(entry, verbose=args.verbose)
    print()


def cmd_get(args: argparse.Namespace) -> None:
    entries = load_index()
    match = next((e for e in entries if e["id"] == args.id), None)
    if not match:
        print(f"ID '{args.id}' não encontrado.", file=sys.stderr)
        sys.exit(1)
    ref = load_reference(match["path"])
    print(json.dumps(ref, ensure_ascii=False, indent=2))


def cmd_list(args: argparse.Namespace) -> None:
    entries = load_index()
    if args.category:
        entries = [e for e in entries if e["category"].startswith(args.category)]
    if args.type:
        entries = [e for e in entries if e["type"] == args.type]

    by_cat: dict[str, list] = {}
    for e in entries:
        by_cat.setdefault(e["category"], []).append(e)

    for cat, items in sorted(by_cat.items()):
        print(f"\n{cat}/")
        for item in items:
            maturity_badge = {"stable": "✓", "growing": "~", "seed": "·", "outdated": "!", "deprecated": "✗"}.get(item["maturity"], "?")
            print(f"  {maturity_badge} {item['id']:<40} {(item.get('description') or '')[:55]}")
    print()


def cmd_stats(_: argparse.Namespace) -> None:
    data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    stats = data.get("stats", {})
    print(f"\nTotal de referências: {stats.get('total', '?')}")
    print("\nPor tipo:")
    for k, v in stats.get("by_type", {}).items():
        if v > 0:
            print(f"  {k:<20} {v}")
    print("\nPor maturity:")
    for k, v in stats.get("by_maturity", {}).items():
        if v > 0:
            print(f"  {k:<20} {v}")
    print()


def _print_entry(entry: dict, verbose: bool = False) -> None:
    print(f"  [{entry['type']}] [{entry['maturity']}] {entry['name']}")
    if entry.get("description"):
        print(f"  {entry['description']}")
    tensions = entry.get("tensions", [])
    if tensions:
        print(f"  Tensions: {' · '.join(tensions)}")
    if verbose:
        print(f"  Tags: {', '.join(entry.get('tags', []))}")
        print(f"  Path: {entry['path']}")
    print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m src.query", description="MarketingOS Reference Library")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("search", help="Busca por keywords, tipo, categoria ou maturity")
    s.add_argument("keywords", nargs="*")
    s.add_argument("--category", "-c")
    s.add_argument("--type", "-t", dest="type")
    s.add_argument("--maturity", "-m")
    s.add_argument("--verbose", "-v", action="store_true")

    g = sub.add_parser("get", help="Retorna o JSON completo de uma referência por ID")
    g.add_argument("id")

    ll = sub.add_parser("list", help="Lista todas as referências agrupadas por categoria")
    ll.add_argument("--category", "-c")
    ll.add_argument("--type", "-t", dest="type")

    sub.add_parser("stats", help="Resumo do estado do repositório")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif len(sys.argv) > 1:
        # shorthand: python -m src.query dark luxury
        results = search(sys.argv[1:])
        if not results:
            print("Nenhuma referência encontrada.")
        else:
            print(f"\n{len(results)} referência(s):\n")
            for e in results:
                _print_entry(e)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
