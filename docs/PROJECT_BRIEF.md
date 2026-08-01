# Project Brief: Source-Ready Book Markdown Exporter

## Product Name
Source-Ready Book Markdown Exporter

## Product Intent
To transform professional technical books and documents into high-quality, structured Markdown files optimized specifically for ingestion into ChatGPT Project Sources. This tool ensures that the resulting Markdown is more readable, searchable, and contextually aware for LLMs than raw PDFs or fragmented chapter files.

## Primary User
Software engineers, researchers, and technical professionals who use ChatGPT Projects as a personalized knowledge base and need to ingest complete books while respecting limited upload slots.

## Main Problem
ChatGPT Projects have a limited number of "Source" upload slots. Exporting a book as individual chapters (the current app behavior) consumes too many slots. Furthermore, raw PDF exports often contain layout artifacts (headers, footers, sidebars) that confuse LLM retrieval and reasoning.

## Why Native Export is Preferred
The system prioritizes native HTML/XHTML/EPUB sources over PDF because:
1. **Structural Integrity:** Semantic tags (h1-h6, code, table) are preserved.
2. **Cleanliness:** Avoids the "OCR noise" and layout reconstruction errors common in PDF parsing.
3. **Precision:** Easier to strip boilerplate and identify chapter boundaries.

## Role of Docling
Docling is utilized as a robust fallback mechanism for sources that are only available as PDFs, ensuring the pipeline can still process legacy or locked documents.

## Current Immediate Objective
Modify the existing book downloader/export application to generate one consolidated, LLM-optimized "Source-Ready" Markdown file per book, in addition to the existing per-chapter files.

## Non-Goals
- Building a new book downloader from scratch.
- Real-time web scraping (outside of the existing O'Reilly API integration).
- Providing LLM summarization or embeddings within this tool.

## Success Definition
A user can run the exporter on a book and receive a single `.md` file that, when uploaded to a ChatGPT Project, allows the model to accurately reference chapters, code blocks, and tables with minimal noise and maximum structural clarity.
