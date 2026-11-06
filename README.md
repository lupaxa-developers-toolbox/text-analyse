<p align="center">
  <a href="https://github.com/lupaxa-developers-toolbox">
    <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/developers-toolbox/readme-logo.png" alt="Developers Toolbox" />
  </a>
</p>

<h1 align="center">Text Analyse</h1>

Analyse prose for readability, and source code for rough size and
complexity metrics. The library returns one result object. The
`text-analyse` command prints that result as a table.

The PyPI name is `lupaxa-text-analyse`. The import path is
`lupaxa.text_analyse`. The console script is `text-analyse`. `lupaxa` is
a namespace package — there is no `lupaxa/__init__.py`.

Public names: `analyse`, `analyse_text`, `analyse_code`, `looks_like_code`,
`fetch_text`, `describe_flesch_score`, `reading_age_band`,
`TextAnalyseError`, `FetchError`, `__version__`, `get_version()`.

## Install

```bash
pip install lupaxa-text-analyse
```

Requires Python 3.10 or newer, plus `httpx`, `beautifulsoup4`, and `rich`.

## Library

```python
from lupaxa.text_analyse import analyse, analyse_code, analyse_text, fetch_text

analyse("The cat sat on the mat.")
analyse(open("README.md", encoding="utf-8").read(), source="README.md")
analyse_code(open("script.py", encoding="utf-8").read())
fetch_text("https://example.com")
```

`analyse` uses `mode="auto"` unless you pass `text` or `code`. Pass
`source` as the file name when you have one. A documentation suffix
selects text mode, and a Markdown file is scored after fenced code,
HTML tags, and link URLs are removed. Text results include the
reading-age band, the Flesch description, and a language judgement.
Pass `wpm` to change the reading-time estimate.

`fetch_text` follows redirects, sends a `text-analyse` user-agent, and
refuses bodies over 2 MB. HTML pages drop navigation, headers, footers,
and sidebars. The article's headings, paragraphs, and list items become
the text, with a blank line between them.

> **Note:** Readability scores are for continuous English prose. The
> syllable counter, sentence splitter, and code metrics are heuristics.
> Auto mode treats a sample as code when code symbols exceed 3% of the
> characters. Words such as "for" and "from" do not, on their own. An
> HTML page, or a Markdown, reStructuredText, or AsciiDoc file, is
> analysed as text. Markdown scores ignore fenced code, HTML, and link
> URLs. Pass `--mode code` to force code metrics.

## CLI

The default format is a table. `--format text` prints the same figures
as aligned lines. `--format json` prints the result object.

```bash
text-analyse article.txt
text-analyse --url https://example.com
text-analyse --min-flesch 60 README.md
text-analyse docs/ --check --min-flesch 60
text-analyse --mode code script.py
cat notes.txt | text-analyse --wpm 180 --reading-age-scheme us
text-analyse --version
```

| Flag                   | Meaning                                                 |
| ---------------------- | ------------------------------------------------------- |
| `path`                 | Files or documentation directories. Stdin when omitted. |
| `--file`, `-f`         | File path. Do not combine with `path` or `--url`.       |
| `--url`, `-u`          | Fetch a URL. HTML is read as the article.               |
| `--format`, `-F`       | `table` (default), `text`, or `json`.                   |
| `--mode`, `-m`         | `auto` (default), `text`, or `code`.                    |
| `--wpm`                | Reading speed for the time estimate (default 200).      |
| `--min-flesch`         | Fail when the Flesch Reading Ease score is lower.       |
| `--max-grade`          | Fail when the Flesch–Kincaid grade is higher.           |
| `--check`              | Print only files that fail a readability threshold.     |
| `--reading-age-scheme` | `uk` (default) or `us`.                                 |
| `--version`            | Print `text-analyse x.y.z` and exit `0`.                |

| Result                          | Exit |
| ------------------------------- | ---- |
| Report printed                  | `0`  |
| Readability check failed        | `1`  |
| Empty input, bad path, or fetch | `1`  |
| More than one input source      | `1`  |
| Readability check on code only  | `2`  |
| `--check` without a threshold   | `2`  |

A single file is one metrics table. It includes the mode, the language
judgement, and the reading time at the chosen speed. Several files, or a
directory, print one row per file. A directory is walked for Markdown,
reStructuredText, AsciiDoc, and plain-text files. `--check` prints only
the rows that miss a threshold. Code reports for one file are a single
table with the mode, the line counts, and the file-level complexity heuristic.

## Development

```bash
make init
make python-install-dev
make python-check
```

<a href="https://github.com/the-lupaxa-project">
    <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>
