"""
Reference Library Query CLI

Busca referências de animação, estilo visual e identidade de clientes.

Uso:
  python -m src.query "particle background dark"
  python -m src.query --category animations/three-js
  python -m src.query --category visual/color-systems --tag finance
  python -m src.query --id three-js-particle-systems
  python -m src.query --client acme-corp
"""

import argparse
import json
import sys
from pathlib import Path

REFERENCES_DIR = Path(__file__).parent.parent / "references"
INDEX_FILE = REFERENCES_DIR / "index.json"


def load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        print(f"Erro: index.json não encontrado em {INDEX_FILE}", file=sys.stderr)
        sys.exit(1)
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))["entries"]


def load_reference(file_path: str) -> dict:
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(__file__).parent.parent / file_path
    return json.loads(path.read_text(encoding="utf-8"))


def search(keywords: list[str], category: str | None = None, tag: str | None = None) -> list[dict]:
    # Normaliza keywords: split frases passadas como string única
    flat_kws = []
    for kw in keywords:
        flat_kws.extend(kw.lower().split())

    entries = load_index()
    results = []

    for entry in entries:
        # Filtros diretos
        if category and not entry["category"].startswith(category):
            continue
        if tag and tag.lower() not in [t.lower() for t in entry.get("tags", [])]:
            continue

        # Score por keywords
        if flat_kws:
            searchable = " ".join([
                entry.get("title", ""),
                entry.get("description", ""),
                " ".join(entry.get("tags", [])),
                " ".join(entry.get("use_cases_short", [])),
            ]).lower()
            score = sum(1 for kw in flat_kws if kw in searchable)
            if score == 0:
                continue
            results.append((score, entry))
        else:
            results.append((0, entry))

    return [e for _, e in sorted(results, key=lambda x: -x[0])]


def search_for_marketing_os(brief: dict) -> list[dict]:
    """
    Ponto de entrada para o MarketingOS.
    Recebe um dict com campos do brief e retorna referências relevantes.
    """
    keywords = []
    if brief.get("sector"):
        keywords.append(brief["sector"])
    if brief.get("style"):
        keywords.append(brief["style"])
    if brief.get("animations"):
        keywords.extend(brief["animations"] if isinstance(brief["animations"], list) else [brief["animations"]])
    if brief.get("mood"):
        keywords.extend(brief["mood"].split())
    if brief.get("tags"):
        keywords.extend(brief["tags"])

    return search(keywords, category=brief.get("category"))


def print_entry(entry: dict, verbose: bool = False) -> None:
    cat = entry["category"]
    title = entry["title"]
    desc = entry["description"]
    tags = ", ".join(entry.get("tags", [])[:6])
    file = entry["file"]

    print(f"\n  [{cat}] {title}")
    print(f"  {desc}")
    print(f"  Tags: {tags}")
    print(f"  Arquivo: {file}")

    if verbose:
        print(f"\n  Use cases: {', '.join(entry.get('use_cases_short', []))}")
        complexity = entry.get("complexity")
        if complexity:
            print(f"  Complexidade: {complexity}")


def cmd_search(args: argparse.Namespace) -> None:
    keywords = args.keywords or []
    results = search(keywords, category=args.category, tag=args.tag)

    if not results:
        print("Nenhuma referência encontrada.")
        return

    print(f"\nEncontradas {len(results)} referência(s):")
    for entry in results:
        print_entry(entry, verbose=args.verbose)
    print()


def cmd_get(args: argparse.Namespace) -> None:
    entries = load_index()
    match = next((e for e in entries if e["id"] == args.id), None)

    if not match:
        print(f"Referência '{args.id}' não encontrada.", file=sys.stderr)
        sys.exit(1)

    ref = load_reference(match["file"])
    print(json.dumps(ref, ensure_ascii=False, indent=2))


def cmd_client(args: argparse.Namespace) -> None:
    path = REFERENCES_DIR / "identities" / args.slug / "identity.json"
    if not path.exists():
        print(f"Identidade '{args.slug}' não encontrada em {path}", file=sys.stderr)
        sys.exit(1)
    identity = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(identity, ensure_ascii=False, indent=2))


def cmd_list(args: argparse.Namespace) -> None:
    entries = load_index()

    if args.category:
        entries = [e for e in entries if e["category"].startswith(args.category)]

    by_category: dict[str, list] = {}
    for e in entries:
        by_category.setdefault(e["category"], []).append(e)

    for cat, items in sorted(by_category.items()):
        print(f"\n{cat}/")
        for item in items:
            print(f"  {item['id']:<40} {item['description'][:60]}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.query",
        description="Busca no diretório de referências do MarketingOS",
    )
    sub = parser.add_subparsers(dest="command")

    # search
    s = sub.add_parser("search", help="Busca por keywords, categoria ou tag")
    s.add_argument("keywords", nargs="*", help="Palavras-chave (ex: 'dark particle scroll')")
    s.add_argument("--category", "-c", help="Filtrar por categoria (ex: animations/three-js)")
    s.add_argument("--tag", "-t", help="Filtrar por tag específica")
    s.add_argument("--verbose", "-v", action="store_true")

    # get
    g = sub.add_parser("get", help="Retorna a referência completa (JSON) por ID")
    g.add_argument("id", help="ID da referência (ex: three-js-particle-systems)")

    # client
    c = sub.add_parser("client", help="Retorna a identidade de um cliente")
    c.add_argument("slug", help="Slug do cliente (ex: acme-corp)")

    # list
    l = sub.add_parser("list", help="Lista todas as referências disponíveis")
    l.add_argument("--category", "-c", help="Filtrar por categoria")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "client":
        cmd_client(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        # Comportamento padrão: search por keywords passados direto
        if len(sys.argv) > 1:
            keywords = sys.argv[1:]
            results = search(keywords)
            if not results:
                print("Nenhuma referência encontrada.")
            else:
                print(f"\nEncontradas {len(results)} referência(s):")
                for entry in results:
                    print_entry(entry)
                print()
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
