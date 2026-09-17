import os
import re
import uuid
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
import xml.etree.ElementTree as ET
import requests
from pypdf import PdfReader
from researchmind.config import UPLOAD_DIR


class PaperMetadata:
    def __init__(
        self,
        id: str,
        title: str,
        authors: List[str],
        abstract: str,
        published: str = "",
        arxiv_id: Optional[str] = None,
        pdf_path: str = "",
        num_pages: int = 0,
        word_count: int = 0,
        doi: Optional[str] = None,
        categories: Optional[List[str]] = None,
        full_text: str = "",
        pages_text: Optional[List[Dict[str, Any]]] = None,
    ):
        self.id = id
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.published = published
        self.arxiv_id = arxiv_id
        self.pdf_path = pdf_path
        self.num_pages = num_pages
        self.word_count = word_count
        self.doi = doi
        self.categories = categories or []
        self.full_text = full_text
        self.pages_text = pages_text or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "published": self.published,
            "arxiv_id": self.arxiv_id,
            "pdf_path": self.pdf_path,
            "num_pages": self.num_pages,
            "word_count": self.word_count,
            "doi": self.doi,
            "categories": self.categories,
            "full_text": self.full_text,
            "pages_text": self.pages_text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperMetadata":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", "Untitled"),
            authors=data.get("authors", []),
            abstract=data.get("abstract", ""),
            published=data.get("published", ""),
            arxiv_id=data.get("arxiv_id"),
            pdf_path=data.get("pdf_path", ""),
            num_pages=data.get("num_pages", 0),
            word_count=data.get("word_count", 0),
            doi=data.get("doi"),
            categories=data.get("categories", []),
            full_text=data.get("full_text", ""),
            pages_text=data.get("pages_text", []),
        )


def extract_arxiv_id(input_str: str) -> Optional[str]:
    """
    Extract arXiv ID from input string (URL, ID with/without version).
    Examples:
      - 1706.03762
      - 1706.03762v5
      - https://arxiv.org/abs/1706.03762
      - https://arxiv.org/pdf/1706.03762.pdf
      - arxiv:1706.03762
      - math/0211159
    """
    input_str = input_str.strip()
    # Match modern arXiv IDs: YYMM.NNNNN(vN)?
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", input_str)
    if match:
        return match.group(1)
    # Match legacy arXiv IDs: arch-ive/YYMMNNN
    match_legacy = re.search(r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)", input_str, re.IGNORECASE)
    if match_legacy:
        return match_legacy.group(1)
    return None


def fetch_arxiv_metadata(arxiv_id: str) -> Dict[str, Any]:
    """
    Fetches paper metadata from arXiv Atom API with automatic HTML scraping fallback.
    """
    clean_id = re.sub(r"v\d+$", "", arxiv_id)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ResearchMind/1.0"}

    # Attempt 1: Try official Atom API
    try:
        url = f"https://export.arxiv.org/api/query?id_list={clean_id}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
            entry = root.find("atom:entry", ns)
            if entry is not None:
                title_elem = entry.find("atom:title", ns)
                title = re.sub(r"\s+", " ", title_elem.text.strip()) if title_elem is not None and title_elem.text else "Untitled"

                summary_elem = entry.find("atom:summary", ns)
                abstract = re.sub(r"\s+", " ", summary_elem.text.strip()) if summary_elem is not None and summary_elem.text else ""

                published_elem = entry.find("atom:published", ns)
                published = published_elem.text.strip()[:10] if published_elem is not None and published_elem.text else ""

                authors = []
                for a in entry.findall("atom:author", ns):
                    name_elem = a.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                doi_elem = entry.find("arxiv:doi", ns)
                doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

                categories = [cat.get("term") for cat in entry.findall("atom:category", ns) if cat.get("term")]

                return {
                    "title": title,
                    "abstract": abstract,
                    "published": published,
                    "authors": authors,
                    "doi": doi,
                    "categories": categories,
                    "pdf_url": f"https://arxiv.org/pdf/{clean_id}.pdf",
                    "arxiv_id": arxiv_id,
                }
    except Exception:
        pass  # Fall through to HTML fallback

    # Attempt 2: Fallback to HTML scraping of arXiv abs page
    try:
        abs_url = f"https://arxiv.org/abs/{clean_id}"
        resp = requests.get(abs_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            html = resp.text
            # Extract title
            title_match = re.search(r'<h1 class="title mathjax"><span class="descriptor">Title:</span>(.*?)</h1>', html, re.DOTALL)
            title = re.sub(r"\s+", " ", title_match.group(1).strip()) if title_match else f"arXiv Paper {clean_id}"

            # Extract abstract
            abs_match = re.search(r'<blockquote class="abstract mathjax">\s*<span class="descriptor">Abstract:</span>(.*?)</blockquote>', html, re.DOTALL)
            abstract = re.sub(r"\s+", " ", abs_match.group(1).strip()) if abs_match else ""

            # Extract authors
            authors_match = re.search(r'<div class="authors"><span class="descriptor">Authors:</span>(.*?)</div>', html, re.DOTALL)
            authors = []
            if authors_match:
                for a in re.findall(r'<a\s+[^>]*>(.*?)</a>', authors_match.group(1)):
                    authors.append(a.strip())

            # Extract date
            date_match = re.search(r'\[Submitted on ([^\]]+)\]', html)
            published = date_match.group(1).strip() if date_match else ""

            return {
                "title": title,
                "abstract": abstract,
                "published": published,
                "authors": authors,
                "doi": None,
                "categories": [],
                "pdf_url": f"https://arxiv.org/pdf/{clean_id}.pdf",
                "arxiv_id": arxiv_id,
            }
    except Exception as e:
        raise ValueError(f"Failed to fetch metadata for arXiv ID {arxiv_id}: {str(e)}")

    raise ValueError(f"Could not retrieve details for arXiv ID {arxiv_id}")


def download_arxiv_pdf(arxiv_id: str, dest_dir: Path = UPLOAD_DIR) -> Path:
    """
    Downloads the PDF for an arXiv paper and stores it in dest_dir.
    """
    clean_id = re.sub(r"v\d+$", "", arxiv_id)
    dest_path = dest_dir / f"arxiv_{clean_id.replace('/', '_')}.pdf"

    if dest_path.exists() and dest_path.stat().st_size > 1000:
        return dest_path

    pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    headers = {"User-Agent": "ResearchMind-AI/1.0 (academic-research-tool)"}
    resp = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
    resp.raise_for_status()

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return dest_path


def parse_pdf(file_path: Path | str) -> Dict[str, Any]:
    """
    Parses a local PDF file, extracting text page-by-page.
    Returns:
      - pages_text: List[{"page": int, "text": str}]
      - full_text: string with page demarcations
      - num_pages: int
      - word_count: int
      - detected_title: estimated title from first page
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at {path}")

    reader = PdfReader(str(path))
    num_pages = len(reader.pages)
    pages_text = []
    full_text_parts = []
    total_words = 0

    for i, page in enumerate(reader.pages):
        try:
            page_str = page.extract_text() or ""
        except Exception:
            page_str = ""
        page_num = i + 1
        pages_text.append({"page": page_num, "text": page_str})
        full_text_parts.append(f"--- [Page {page_num}] ---\n{page_str}\n")
        total_words += len(page_str.split())

    full_text = "\n".join(full_text_parts)

    # Simple heuristic to extract a likely title from page 1 if not otherwise known
    detected_title = path.stem.replace("_", " ").replace("-", " ").title()
    if pages_text and pages_text[0]["text"]:
        lines = [line.strip() for line in pages_text[0]["text"].split("\n") if len(line.strip()) > 5]
        if lines:
            # First clean line of reasonable length
            for line in lines[:5]:
                if not line.lower().startswith(("arxiv:", "accepted as", "published as", "ieee", "springer", "under review")):
                    detected_title = line
                    break

    return {
        "num_pages": num_pages,
        "word_count": total_words,
        "pages_text": pages_text,
        "full_text": full_text,
        "detected_title": detected_title,
    }


def load_paper_from_path(file_path: Path | str) -> PaperMetadata:
    """
    Loads a local PDF paper and returns a PaperMetadata instance.
    """
    path = Path(file_path)
    parsed = parse_pdf(path)

    # Compute a unique hash ID based on path + file content
    file_bytes = path.read_bytes()
    paper_id = hashlib.sha256(file_bytes[:4096] + str(path.stat().st_size).encode()).hexdigest()[:12]

    # Try extracting abstract from first 2 pages
    abstract = ""
    first_two_pages = " ".join([p["text"] for p in parsed["pages_text"][:2]])
    abs_match = re.search(r"(?:Abstract|ABSTRACT)[\s:—–\-]+(.*?)(?=(?:Introduction|1\.|1\s+Introduction|Index Terms|Keywords|I\.))", first_two_pages, re.DOTALL | re.IGNORECASE)
    if abs_match:
        abstract = re.sub(r"\s+", " ", abs_match.group(1).strip())[:2000]

    return PaperMetadata(
        id=paper_id,
        title=parsed["detected_title"],
        authors=[],
        abstract=abstract,
        pdf_path=str(path.resolve()),
        num_pages=parsed["num_pages"],
        word_count=parsed["word_count"],
        full_text=parsed["full_text"],
        pages_text=parsed["pages_text"],
    )


def load_paper_from_arxiv(input_val: str) -> PaperMetadata:
    """
    Given an arXiv ID or URL, fetches metadata, downloads PDF, extracts text,
    and returns a PaperMetadata instance.
    """
    arxiv_id = extract_arxiv_id(input_val)
    if not arxiv_id:
        raise ValueError(f"Could not parse a valid arXiv identifier from: {input_val}")

    meta = fetch_arxiv_metadata(arxiv_id)
    pdf_path = download_arxiv_pdf(arxiv_id)
    parsed = parse_pdf(pdf_path)

    paper_id = f"arxiv_{re.sub(r'[^a-zA-Z0-9]', '_', arxiv_id)}"

    return PaperMetadata(
        id=paper_id,
        title=meta["title"],
        authors=meta["authors"],
        abstract=meta["abstract"],
        published=meta["published"],
        arxiv_id=meta["arxiv_id"],
        pdf_path=str(pdf_path.resolve()),
        num_pages=parsed["num_pages"],
        word_count=parsed["word_count"],
        doi=meta["doi"],
        categories=meta["categories"],
        full_text=parsed["full_text"],
        pages_text=parsed["pages_text"],
    )
