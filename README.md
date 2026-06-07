---
title: Lawyer Assistant
emoji: ⚖️
colorFrom: yellow
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: contract_reviewer/app.py
pinned: false
---

# Lawyer Assistant

A Gradio app for legal document work:

- **Contract review** — upload a `.docx` contract and get a copy back with highlighted
  issues and reviewer-note paragraphs.
- **Process mind map** — upload a law, regulation, or procedure and get a process
  flowchart of the steps, decision/authority gates, required documents, deadlines, and
  article references. Exportable as an SVG image, HTML, Mermaid, DOT, or JSON.

## Configuration

Set these under **Settings → Variables and secrets** on the Space:

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Secret | Yes | Used for all model calls. |
| `OPENAI_BASE_URL` | Variable | No | For OpenAI-compatible providers. |
| `CONTRACT_REVIEWER_MODEL` | Variable | No | Defaults to `gpt-5.4-mini`. |

> **Note:** This Space is public, so any visitor's uploads are sent to the OpenAI API
> on the configured key. Watch usage/billing accordingly.

## Running locally

```bash
pip install -r requirements.txt
# Graphviz system binary is needed for the SVG export:
#   Windows: winget install graphviz
#   macOS:   brew install graphviz
#   Debian/Ubuntu: sudo apt-get install graphviz
export OPENAI_API_KEY=sk-...
python -m contract_reviewer.app
```
