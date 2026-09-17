import json
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_file, stream_with_context

from researchmind.config import Config, AVAILABLE_MODELS, UPLOAD_DIR
from researchmind.paper_loader import (
    load_paper_from_path,
    load_paper_from_arxiv,
    extract_arxiv_id,
    fetch_arxiv_metadata,
)
from researchmind.storage import storage
from researchmind.core.agent import PaperAnalysisAgent, MODULE_PROMPTS, PaperAnalysisResult, AnalysisSection
from researchmind.core.chat_engine import PaperChatEngine
from researchmind.core.comparative import PaperComparisonAgent
from researchmind.exporter import PaperExporter

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64MB max PDF upload


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    if request.method == "POST":
        data = request.get_json() or {}
        if "api_key" in data and data["api_key"].strip():
            Config.set_api_key(data["api_key"].strip())
        if "default_model" in data and data["default_model"].strip():
            Config.set_default_model(data["default_model"].strip())
        return jsonify({
            "status": "success",
            "api_key_configured": Config.is_api_key_configured(),
            "default_model": Config.get_default_model(),
        })

    return jsonify({
        "api_key_configured": Config.is_api_key_configured(),
        "default_model": Config.get_default_model(),
        "available_models": AVAILABLE_MODELS,
    })


@app.route("/api/papers", methods=["GET"])
def list_papers():
    papers = storage.list_papers()
    return jsonify({"papers": papers})


@app.route("/api/papers/<paper_id>", methods=["GET"])
def get_paper(paper_id):
    paper = storage.get_paper(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404
    analysis = storage.get_analysis(paper_id)
    return jsonify({
        "paper": paper.to_dict(),
        "analysis": analysis.to_dict() if analysis else None,
    })


@app.route("/api/papers/<paper_id>", methods=["DELETE"])
def delete_paper(paper_id):
    storage.delete_paper(paper_id)
    return jsonify({"status": "deleted", "paper_id": paper_id})


@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file attached"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    dest_path = UPLOAD_DIR / file.filename
    # Handle filename collision
    counter = 1
    orig_stem = dest_path.stem
    while dest_path.exists():
        dest_path = UPLOAD_DIR / f"{orig_stem}_{counter}.pdf"
        counter += 1

    file.save(dest_path)

    try:
        paper = load_paper_from_path(dest_path)
        storage.save_paper(paper)
        return jsonify({
            "status": "success",
            "paper": paper.to_dict(),
        })
    except Exception as e:
        return jsonify({"error": f"Failed to parse PDF: {str(e)}"}), 500


@app.route("/api/arxiv", methods=["POST"])
def fetch_arxiv():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "No arXiv query or ID provided"}), 400

    try:
        paper = load_paper_from_arxiv(query)
        storage.save_paper(paper)
        return jsonify({
            "status": "success",
            "paper": paper.to_dict(),
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch arXiv paper: {str(e)}"}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json() or {}
    paper_id = data.get("paper_id")
    model = data.get("model") or Config.get_default_model()
    sections = data.get("sections") or list(MODULE_PROMPTS.keys())

    paper = storage.get_paper(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    if not Config.is_api_key_configured():
        return jsonify({"error": "GEMINI_API_KEY is not configured. Please add your key in Settings."}), 400

    def generate_events():
        agent = PaperAnalysisAgent(model_name=model)
        result = PaperAnalysisResult(
            paper_id=paper.id,
            paper_title=paper.title,
            model_used=model,
            metadata=paper.to_dict(),
        )

        total_sections = len(sections)
        yield f"data: {json.dumps({'event': 'start', 'total': total_sections})}\n\n"

        for idx, sec_key in enumerate(sections, 1):
            sec_title = MODULE_PROMPTS.get(sec_key, (sec_key, ""))[0]
            yield f"data: {json.dumps({'event': 'section_start', 'key': sec_key, 'title': sec_title, 'index': idx, 'total': total_sections})}\n\n"

            try:
                sec_res = agent.analyze_section(paper, sec_key)
                result.sections[sec_key] = sec_res
                yield f"data: {json.dumps({'event': 'section_done', 'key': sec_key, 'title': sec_title, 'content': sec_res.content, 'duration': sec_res.generation_time_s})}\n\n"
            except Exception as ex:
                yield f"data: {json.dumps({'event': 'section_error', 'key': sec_key, 'title': sec_title, 'error': str(ex)})}\n\n"

        # Persist completed analysis only if at least one section succeeded
        if result.sections:
            storage.save_analysis(result)
        yield f"data: {json.dumps({'event': 'complete', 'paper_id': paper.id, 'success_count': len(result.sections), 'total': total_sections})}\n\n"

    return Response(stream_with_context(generate_events()), mimetype="text/event-stream")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    paper_id = data.get("paper_id")
    message = data.get("message", "").strip()
    model = data.get("model") or Config.get_default_model()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Empty message"}), 400

    paper = storage.get_paper(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    if not Config.is_api_key_configured():
        return jsonify({"error": "GEMINI_API_KEY is not configured. Please add your key in Settings."}), 400

    def generate_chat_stream():
        engine = PaperChatEngine(paper, model_name=model)
        # Restore prior conversation history
        for item in history:
            engine.history.append(
                item if hasattr(item, "role") else type("Msg", (), {"role": item.get("role"), "content": item.get("content")})()
            )

        try:
            for chunk in engine.ask_stream(message):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate_chat_stream()), mimetype="text/event-stream")


@app.route("/api/chat/starters/<paper_id>", methods=["GET"])
def get_chat_starters(paper_id):
    paper = storage.get_paper(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    if not Config.is_api_key_configured():
        return jsonify({
            "questions": [
                "What is the primary contribution of this work?",
                "How does the methodology compare to prior state-of-the-art?",
                "What are the major limitations and threats to validity?",
                "What datasets and benchmarks were evaluated?",
            ]
        })

    try:
        engine = PaperChatEngine(paper)
        questions = engine.generate_starter_questions()
        return jsonify({"questions": questions})
    except Exception as e:
        return jsonify({
            "questions": [
                "What is the primary contribution of this work?",
                "How does the methodology compare to prior state-of-the-art?",
                "What are the major limitations and threats to validity?",
                "What datasets and benchmarks were evaluated?",
            ]
        })


@app.route("/api/compare", methods=["POST"])
def compare():
    data = request.get_json() or {}
    paper_ids = data.get("paper_ids", [])
    model = data.get("model") or Config.get_default_model()

    if len(paper_ids) < 2:
        return jsonify({"error": "At least 2 papers are required for comparison"}), 400

    papers = []
    for pid in paper_ids:
        p = storage.get_paper(pid)
        if p:
            papers.append(p)

    if len(papers) < 2:
        return jsonify({"error": "Could not find at least 2 valid papers in storage"}), 400

    if not Config.is_api_key_configured():
        return jsonify({"error": "GEMINI_API_KEY is not configured"}), 400

    def generate_compare_stream():
        comparator = PaperComparisonAgent(model_name=model)
        try:
            for chunk in comparator.compare_stream(papers):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate_compare_stream()), mimetype="text/event-stream")


@app.route("/api/export/<paper_id>", methods=["GET"])
def export_analysis(paper_id):
    export_fmt = request.args.get("format", "md").lower()
    analysis = storage.get_analysis(paper_id)
    if not analysis:
        return jsonify({"error": "No analysis found for this paper"}), 404

    safe_title = "".join(c for c in analysis.paper_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    safe_title = safe_title[:40] or "analysis"

    if export_fmt in ("md", "markdown"):
        content = PaperExporter.to_markdown(analysis)
        return Response(
            content,
            mimetype="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="analysis_{safe_title}.md"'},
        )
    elif export_fmt == "html":
        content = PaperExporter.to_html(analysis)
        return Response(
            content,
            mimetype="text/html",
            headers={"Content-Disposition": f'attachment; filename="analysis_{safe_title}.html"'},
        )
    elif export_fmt == "json":
        content = PaperExporter.to_json(analysis)
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": f'attachment; filename="analysis_{safe_title}.json"'},
        )
    return jsonify({"error": "Unsupported export format"}), 400


def create_app():
    return app


if __name__ == "__main__":
    port = int(Config.get_api_key() and 5000 or 5000)
    app.run(host="127.0.0.1", port=port, debug=True)

