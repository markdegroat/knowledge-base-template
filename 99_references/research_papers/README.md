---
tags: [reference, fundamentals, knowledge-management]
related: []
summary: "Folder guide for the research-papers staging area: one subfolder per paper with the raw PDF and an LLM-generated summary note."
status: draft
---

# Research Paper Digests

Academic and industry papers related to this knowledge base's topic, each with an LLM-generated summary that distills its relevance to the vault.

## Folder Structure

Each paper gets its own subfolder:

```
research_papers/
  short_paper_title/
    short_paper_title.pdf      # the raw paper (or a link, if the PDF cannot be stored)
    short_paper_title.md       # the summary note, from TEMPLATE_research_paper.md
```

- **Folder name**: `snake_case_short_title/`, derived from the paper title.
- **Summary note**: a structured note created from `TEMPLATE_research_paper.md`.

## How Notes Get Here

An ingest step (manual or agent-assisted):
1. Takes a paper (PDF, link, or pasted content)
2. Distills the knowledge relevant to this knowledge base's scope
3. Adds inline full-path wiki-links to existing notes where the content overlaps
4. Saves the raw paper and the summary in a new subfolder here

## This Is a Staging Area

Summary notes are **LLM-generated digests**, less curated than the core buckets. Expect overlap across papers, conflicting findings, and varying relevance. Curation into the core buckets is a separate, human-directed step.

## Status Flow

1. **Downloaded**: raw PDF saved, no summary yet
2. **Ingested**: summary created, `status: draft`
3. **Reviewed** by a person (optional)
4. **Decomposed** into core-bucket notes: move to `_archive/` or keep as a reference
