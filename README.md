<div align="center">
   <img src=".github/assets/logo.png" alt="Logo" width="300">
   <br><a href="https://github.com/apurvsinghgautam/robin/actions/workflows/release.yml"><img alt="Release" src="https://github.com/apurvsinghgautam/robin/actions/workflows/release.yml/badge.svg"></a> <a href="https://github.com/apurvsinghgautam/robin/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/apurvsinghgautam/robin"></a> <a href="https://hub.docker.com/r/apurvsg/robin"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/apurvsg/robin"></a>
   <p align="center">
 <a href="https://www.star-history.com/apurvsinghgautam/robin"><img src="https://api.star-history.com/badge?repo=apurvsinghgautam/robin&type=trending" alt="GitHub Trending Repository of the Day" /></a>
</p>
   <h1>Robin: AI-Powered Dark Web OSINT Tool</h1>

   <p>Robin is an AI-powered tool for conducting dark web OSINT investigations. It leverages LLMs to refine queries, filter search results from dark web search engines, and provide an investigation summary.</p>
   <a href="#installation">Installation</a> &bull; <a href="#troubleshooting">Troubleshooting</a> &bull; <a href="#contributing">Contributing</a> &bull; <a href="#acknowledgements">Acknowledgements</a><br><br>
</div>

![Demo](.github/assets/screen-ui.png)

## Robin V1 branch

`robin-v1-simple` is the portability-focused V1 branch built on the frozen Robin V0 baseline.
It keeps the existing `refine -> search -> filter -> scrape/crawl -> summary -> save` workflow
and adds a bounded crawler, deterministic entity extraction, richer investigation persistence,
portable exports, and Streamlit controls for the new crawl/export functionality.

### V0 vs V1

| Area | V0 baseline | V1 (`robin-v1-simple`) |
| --- | --- | --- |
| Acquisition | Existing seed-page scrape workflow | Existing workflow plus bounded breadth-first crawling |
| Crawl controls | No V1 recursive crawl controls | Depth 0-2, page cap 1-50, same-host scope |
| Entity extraction | No V1 deterministic entity record | Onion URLs, emails, domains, IPs, hashes, CVEs, handles |
| Persistence | Legacy investigation JSON | Crawl config plus per-page metadata, text and entities |
| Export | Saved investigation data | JSON, CSV and Markdown downloads |
| Compatibility | Frozen V0 behavior | Legacy investigation files still load without migration |

V1 intentionally does not add a database, WARC storage, graph analysis, dynamic-JS crawling,
or a new LLM/provider layer.

## Architecture
![Workflow](.github/assets/robin-workflow.png)

---

## Features

- ⚙️ **Modular Architecture** – Clean separation between search, scrape, and LLM workflows.
- 🤖 **Multi-Model Support** – OpenAI, Claude, Gemini, Mistral, OpenRouter, Ollama, or any OpenAI-compatible API (LM Studio, llama.cpp, Groq, etc.).
- 🔄 **Live Model List** – Models are discovered from each provider at startup, so new releases appear on their own and retired ones disappear. No hardcoded list to go stale.
- 🎚️ **Tunable Depth** – Sidebar controls for how many results to filter, how many pages to scrape, and how much of each page the model reads, with the token cost shown before you run.
- 🌐 **Web UI** – Streamlit-based interface for interactive investigations.
- 💬 **Conversational Follow-ups** – Ask grounded follow-up questions about an investigation without re-running the search — answered from that investigation's own data.
- 🔀 **One-Click Pivots** – Suggested follow-up queries surfaced from the findings; click one to launch a fresh investigation.
- 🐳 **Docker-Ready** – Recommended Docker deployment for clean, isolated usage.
- 🔍 **Honest Results** – When nothing relevant is found, Robin says so instead of summarizing whatever it happened to scrape.
- 📝 **Custom Reporting** – Save investigation output to file for reporting or further analysis.
- 🧩 **Extensible** – Easy to plug in new search engines, models, or output formats.

---

## ⚠️ Disclaimer
> This tool is intended for educational and lawful investigative purposes only. Accessing or interacting with certain dark web content may be illegal depending on your jurisdiction. The author is not responsible for any misuse of this tool or the data gathered using it.
>
> Use responsibly and at your own risk. Ensure you comply with all relevant laws and institutional policies before conducting OSINT investigations.
>
> Additionally, Robin leverages third-party APIs (including LLMs). Be cautious when sending potentially sensitive queries, and review the terms of service for any API or model provider you use.

## Installation

### Requirements

- Git.
- Python with `venv`. The dependency freeze in `requirements.lock.txt` was produced from the
  validated V1.5 environment on **Python 3.14.3 / pip 26.2.1 / Windows**.
- Tor for live `.onion` search. Robin currently expects a SOCKS5h proxy at
  `127.0.0.1:9050`.
- At least one working LLM provider: a configured cloud API key, local Ollama, or another
  provider already supported by Robin.

For the most reproducible install, use `requirements.lock.txt`. `requirements.txt` remains the
unversioned dependency declaration for development/upstream compatibility.

### Quick Start - Windows PowerShell

```powershell
git clone https://github.com/pkomu33/robin.git
cd robin
git checkout robin-v1-simple

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt

Copy-Item .\.env.example .\.env
notepad .\.env

.\.venv\Scripts\python.exe .\scripts\smoke_test.py
.\run.ps1
```

If PowerShell blocks local scripts, run the launcher for the current process with:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Open `http://localhost:8501`.

### Quick Start - Linux / Kali

Ensure Python, `venv`, Git and Tor are available. On Debian/Kali, system packages may be installed
with the distribution package manager; `run.sh` deliberately does not install them for you.

```bash
git clone https://github.com/pkomu33/robin.git
cd robin
git checkout robin-v1-simple

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.lock.txt

cp .env.example .env
${EDITOR:-nano} .env

.venv/bin/python scripts/smoke_test.py
bash ./run.sh
```

Open `http://localhost:8501`.

### Environment configuration

Copy `.env.example` to `.env`. Do not commit `.env`; it is ignored by Git.

For a cloud provider, set only the key(s) you use:

```dotenv
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
MISTRAL_API_KEY=
OPENROUTER_API_KEY=
```

One working provider is enough for Robin to populate the model selector.

### Local Ollama

When Robin is run directly from Python rather than Docker, set:

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

Verify Ollama independently before starting Robin.

Windows PowerShell:

```powershell
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Linux:

```bash
ollama list
curl -s http://127.0.0.1:11434/api/tags
```

`OLLAMA_NUM_CTX` defaults in Robin to `32768`. Local hardware/runtime limits can require a lower
value, for example:

```dotenv
OLLAMA_NUM_CTX=8192
```

A successful Robin installation does not guarantee that every local model will run on every
GPU/CPU configuration. Ollama/CUDA/runtime failures must first be reproduced directly in Ollama.

### Tor

Live dark-web search requires Tor listening on `127.0.0.1:9050`.

Linux/Kali example:

```bash
sudo apt update
sudo apt install tor
sudo systemctl enable --now tor
ss -ltn | grep ':9050'
```

Windows verification when a Tor service is already installed:

```powershell
Test-NetConnection 127.0.0.1 -Port 9050
```

Robin's current V1 search and `.onion` scraping code uses that fixed local SOCKS endpoint.
The application itself is **not a fail-closed anonymity boundary**: clear-web URLs can be fetched
directly. For real investigations, use external network isolation (for example a dedicated
investigation VM behind a Tor/Whonix gateway) rather than relying only on application proxy logic.

### Installation smoke test

The installation check is deliberately local and does not require Tor, Internet access, Streamlit
interaction, or an LLM.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe .\scripts\smoke_test.py
```

Linux/Kali:

```bash
.venv/bin/python scripts/smoke_test.py
```

For a full regression check, run the same interpreter against:

```text
scripts/smoke_test.py
scripts/persistence_test.py
scripts/export_test.py
```

### Running Robin

Use the platform launcher:

```powershell
.\run.ps1
```

or:

```bash
bash ./run.sh
```

The launchers require an existing `.venv`; they do not install Python, Tor, Ollama, or packages.

### Investigations and exports

Saved investigations are written to:

```text
investigations/
```

Each V1 investigation can retain the selected crawl configuration and per-page records including
`parent_url`, `crawl_depth`, normalized text and deterministic entities.

From Streamlit, investigations can be downloaded as:

- JSON - full investigation structure;
- CSV - one row per crawled page with flattened entity columns;
- Markdown - readable investigation report.

Synthetic examples are available in:

```text
examples/investigation_example.json
examples/investigation_example.md
```

## Known limitations

- Full live LLM workflow validation for the V1.5 Windows development machine was deferred because
  the local Ollama `llama-server`/CUDA runtime was unstable. Regression tests and Streamlit startup
  were successful; packaging does not attempt to repair GPU/runtime issues.
- V1 still performs the legacy seed scrape and the V1 crawler separately, so seed pages can be
  fetched twice.
- Crawl scope exposed in V1 is same-host only; maximum UI depth is 2.
- JavaScript-rendered/dynamic content is not handled by a dedicated browser engine.
- CSV intentionally flattens IPv4/IPv6 into `ips` and MD5/SHA1/SHA256 into `hashes`.
- The dependency lock is an exact freeze of the validated Windows environment. A clean-install
  validation on Linux/Kali is required before a final release tag is created.

---

## Troubleshooting

Empty model dropdown, Ollama not showing up, Tor `resolve failed` errors, 401s,
or "no results found"? See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** before
opening an issue.

---

## Contributing

Contributions are welcome. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the
pull request flow, the automated checks that run on every push, and what kinds
of change fit the tool.

---

## Acknowledgements

- Idea inspiration from [Thomas Roccia](https://x.com/fr0gger_) and his demo of [Perplexity of the Dark Web](https://x.com/fr0gger_/status/1908051083068645558).
- Tools inspiration from my [OSINT Tools for the Dark Web](https://github.com/apurvsinghgautam/dark-web-osint-tools) repository.
- LLM Prompt inspiration from [OSINT-Assistant](https://github.com/AXRoux/OSINT-Assistant) repository.
- Logo Design by my friend [Tanishq Rupaal](https://github.com/Tanq16/)
