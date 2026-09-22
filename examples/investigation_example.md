# Robin Investigation

**Query:** synthetic security research

**Refined Query:** synthetic security research report

**Model:** ollama:example-model

**Preset:** Balanced

**Timestamp:** 2026-09-22T20:01:00

**Crawler configuration:**
- max_depth: 1
- max_pages: 5
- scope: same_host

## Findings

Synthetic example only. The investigation demonstrates the Robin V1 persistence and export schema without using live or dark-web data.

## Crawled Sources

1. Synthetic Root — http://example.test/root (depth=0, parent=root)
2. Synthetic Child — http://example.test/child (depth=1, parent=http://example.test/root)

## Extracted Entities

### Emails
- analyst@example.test

### Domains
- example.test

### IPs
- 192.0.2.10

### CVEs
- CVE-2099-99999

### Handles
- @synthetic_analyst
