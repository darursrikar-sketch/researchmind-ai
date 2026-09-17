import sys
import argparse
from pathlib import Path
from researchmind.config import Config, AVAILABLE_MODELS
from researchmind.paper_loader import load_paper_from_path, load_paper_from_arxiv, extract_arxiv_id
from researchmind.core.agent import PaperAnalysisAgent, MODULE_PROMPTS
from researchmind.core.chat_engine import PaperChatEngine
from researchmind.core.comparative import PaperComparisonAgent
from researchmind.storage import storage
from researchmind.exporter import PaperExporter


def resolve_paper(input_val: str):
    """Detects whether input is an arXiv identifier/URL or a local file path."""
    if extract_arxiv_id(input_val) and not Path(input_val).exists():
        print(f"[*] Detected arXiv identifier. Fetching metadata and PDF for {input_val}...")
        paper = load_paper_from_arxiv(input_val)
    else:
        path = Path(input_val)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {input_val}")
        print(f"[*] Loading local PDF: {path.name}...")
        paper = load_paper_from_path(path)
    return paper


def handle_analyze(args):
    paper = resolve_paper(args.input)
    storage.save_paper(paper)
    print(f"\n[+] Loaded Paper: '{paper.title}'")
    if paper.authors:
        print(f"    Authors: {', '.join(paper.authors)}")
    print(f"    Pages: {paper.num_pages} | Words: {paper.word_count}")

    model = args.model or Config.get_default_model()
    print(f"[*] Initializing Paper Analysis Agent with model: {model}")
    agent = PaperAnalysisAgent(model_name=model)

    sections_to_run = args.sections.split(",") if args.sections else list(MODULE_PROMPTS.keys())

    print("\n" + "=" * 60)
    print("STARTING ACADEMIC ANALYSIS")
    print("=" * 60)

    def progress(title, cur, total):
        print(f"\n[{cur}/{total}] {title}...")

    result = agent.analyze_all(paper, selected_sections=sections_to_run, progress_callback=progress)
    storage.save_analysis(result)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    for key, section in result.sections.items():
        print(f"\n>>> {section.title} ({section.generation_time_s}s) <<<")
        print("-" * 50)
        print(section.content)
        print()

    # Handle export if requested
    if args.export:
        out_fmt = args.export.lower()
        out_path = args.out or f"analysis_{paper.id}.{out_fmt if out_fmt != 'markdown' else 'md'}"
        if out_fmt in ("md", "markdown"):
            content = PaperExporter.to_markdown(result)
        elif out_fmt == "html":
            content = PaperExporter.to_html(result)
        elif out_fmt == "json":
            content = PaperExporter.to_json(result)
        else:
            print(f"Unknown format: {out_fmt}. Skipping export.")
            return

        Path(out_path).write_text(content, encoding="utf-8")
        print(f"[+] Saved analysis report to: {out_path}")


def handle_chat(args):
    paper = resolve_paper(args.input)
    storage.save_paper(paper)
    print(f"\n[+] Loaded Paper: '{paper.title}'")
    print(f"    Pages: {paper.num_pages}")

    model = args.model or Config.get_default_model()
    chat_engine = PaperChatEngine(paper, model_name=model)

    print("\n[*] Generating suggested discussion questions...")
    starters = chat_engine.generate_starter_questions()
    print("\nSuggested Questions:")
    for idx, q in enumerate(starters, 1):
        print(f"  {idx}. {q}")

    print("\n" + "=" * 60)
    print("INTERACTIVE PAPER CHAT (Type 'exit' or 'quit' to end)")
    print("=" * 60 + "\n")

    while True:
        try:
            query = input("\nYou: ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("Exiting chat.")
                break

            print("\nResearchMind: ", end="", flush=True)
            for chunk in chat_engine.ask_stream(query):
                print(chunk, end="", flush=True)
            print("\n")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break


def handle_compare(args):
    if len(args.inputs) < 2:
        print("[-] Error: At least 2 papers are required for comparative analysis.")
        return

    papers = []
    for inp in args.inputs:
        papers.append(resolve_paper(inp))

    model = args.model or Config.get_default_model()
    print(f"\n[*] Comparing {len(papers)} papers using {model}...")
    for p in papers:
        print(f"  - {p.title} ({p.num_pages} pages)")

    comparator = PaperComparisonAgent(model_name=model)
    print("\n" + "=" * 60)
    print("COMPARATIVE SYNTHESIS")
    print("=" * 60 + "\n")

    for chunk in comparator.compare_stream(papers):
        print(chunk, end="", flush=True)
    print("\n")


def handle_list(args):
    papers = storage.list_papers()
    if not papers:
        print("No papers found in local workspace.")
        return

    print(f"\n=== Saved Papers in Workspace ({len(papers)}) ===")
    for p in papers:
        authors = ", ".join(p["authors"][:2]) + ("..." if len(p["authors"]) > 2 else "")
        print(f"ID: {p['id']} | Title: {p['title']}")
        print(f"   Authors: {authors or 'N/A'} | Pages: {p['num_pages']} | arXiv: {p['arxiv_id'] or 'N/A'}")
        print()


def handle_config(args):
    if args.set_key:
        Config.set_api_key(args.set_key)
        print(f"[+] GEMINI_API_KEY set successfully.")
    elif args.set_model:
        Config.set_default_model(args.set_model)
        print(f"[+] Default model set to: {args.set_model}")
    else:
        key_status = "Configured" if Config.is_api_key_configured() else "Not set (set with --set-key)"
        print(f"Gemini API Key: {key_status}")
        print(f"Default Model:  {Config.get_default_model()}")
        print("\nAvailable Models:")
        for m in AVAILABLE_MODELS:
            print(f"  - {m['id']}: {m['name']} ({m['desc']})")


def main():
    parser = argparse.ArgumentParser(
        description="ResearchMind AI - Autonomous Academic Paper Analysis Agent"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Analyze
    p_analyze = subparsers.add_parser("analyze", help="Run comprehensive academic analysis")
    p_analyze.add_argument("input", help="Local PDF path or arXiv identifier (e.g. 1706.03762)")
    p_analyze.add_argument("--model", help="Gemini model to use (gemini-3.7-flash, gemini-2.5-pro)")
    p_analyze.add_argument("--sections", help="Comma-separated sections to run (summary,methodology,review,benchmarks,limitations,implementation)")
    p_analyze.add_argument("--export", choices=["md", "html", "json"], help="Export analysis report to file format")
    p_analyze.add_argument("--out", help="Output file path for export")

    # Chat
    p_chat = subparsers.add_parser("chat", help="Interactive grounded Q&A with the paper")
    p_chat.add_argument("input", help="Local PDF path or arXiv identifier")
    p_chat.add_argument("--model", help="Gemini model to use")

    # Compare
    p_compare = subparsers.add_parser("compare", help="Compare 2 or more research papers")
    p_compare.add_argument("inputs", nargs="+", help="2 or more paper paths or arXiv identifiers")
    p_compare.add_argument("--model", help="Gemini model to use")

    # List
    subparsers.add_parser("list", help="List papers saved in local workspace")

    # Config
    p_cfg = subparsers.add_parser("config", help="Manage API key and settings")
    p_cfg.add_argument("--set-key", help="Set GEMINI_API_KEY")
    p_cfg.add_argument("--set-model", help="Set default Gemini model")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "analyze":
            handle_analyze(args)
        elif args.command == "chat":
            handle_chat(args)
        elif args.command == "compare":
            handle_compare(args)
        elif args.command == "list":
            handle_list(args)
        elif args.command == "config":
            handle_config(args)
    except Exception as e:
        print(f"\n[-] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

