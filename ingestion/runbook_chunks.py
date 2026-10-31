import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config import settings


@dataclass(frozen=True)
class RunbookChunk:
    chunk_id: str
    runbook: str
    section: str
    text: str


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def split_runbook(
    runbook_path: Path,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[RunbookChunk]:
    """Split a Markdown runbook into stable, section-tagged chunks."""
    size = chunk_size if chunk_size is not None else settings.runbook_chunk_size
    overlap = (
        chunk_overlap if chunk_overlap is not None else settings.runbook_chunk_overlap
    )
    if overlap >= size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "heading_1"),
            ("##", "heading_2"),
            ("###", "heading_3"),
        ],
        strip_headers=True,
    )
    section_documents = markdown_splitter.split_text(
        runbook_path.read_text(encoding="utf-8")
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        add_start_index=True,
    )

    chunks: list[RunbookChunk] = []
    runbook_name = runbook_path.stem
    for section_document in section_documents:
        section = " > ".join(
            str(section_document.metadata[key])
            for key in ("heading_1", "heading_2", "heading_3")
            if section_document.metadata.get(key)
        ) or "Introduction"
        section_chunks = text_splitter.split_documents([section_document])
        for chunk_index, document in enumerate(section_chunks, start=1):
            digest = hashlib.sha256(
                f"{runbook_name}\0{section}\0{chunk_index}\0{document.page_content}".encode(
                    "utf-8"
                )
            ).hexdigest()[:12]
            chunk_id = (
                f"rb-{_slug(runbook_name)}-{_slug(section)}-"
                f"{chunk_index:03d}-{digest}"
            )
            chunks.append(
                RunbookChunk(
                    chunk_id=chunk_id,
                    runbook=runbook_name,
                    section=section,
                    text=document.page_content,
                )
            )
    return chunks


def load_runbook_chunks(runbook_dir: Path) -> list[RunbookChunk]:
    """Load and split every Markdown runbook in stable filename order."""
    chunks: list[RunbookChunk] = []
    for runbook_path in sorted(runbook_dir.glob("*.md")):
        chunks.extend(split_runbook(runbook_path))
    return chunks
