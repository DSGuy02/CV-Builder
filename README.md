# ATS CV Builder

Generates ATS-friendly CVs in **HTML**, **PDF**, and **DOCX** from a simple Markdown input file.
Targets a **1-page layout** by default, and naturally extends to multiple pages if content requires it.

---

## Quick Start

```bash
# 1. Set up the virtual environment (first time only)
bash setup_venv.sh

# 2. Activate it
source .venv/bin/activate

# 3. Build the CV
python cv_builder.py input/cv_template.md
```

Outputs are written to the `output/` folder:
- `output/cv_template.html`
- `output/cv_template.pdf`
- `output/cv_template.docx`

---

## Input File Format

Input files live in `input/` and use a structured Markdown format.
Copy `input/cv_template.md` as a starting point.

### Structure Overview

```
## META
name: Your Name
profession: Your Job Title
email: you@example.com
phone: +1234567890
links:
  - [LinkedIn](https://linkedin.com/in/yourprofile)
  - [GitHub](https://github.com/yourhandle)

---

## SUMMARY
enabled: true
---
Your summary paragraph here.

---

## EXPERIENCE
enabled: true
---

### Company Name
role: Job Title
date: Jan 2023 - Present
bullets:
  - Did something impactful.
  - Used [Tool Name](https://tool.com) to achieve X.

---

## EDUCATION
enabled: true
---

### University Name
degree: Bachelor of Science
field: Computer Science
date: 2019 - 2023
bullets:
  - Result: First Class Honours

---

## PROJECTS
enabled: true
---

### Project Name
bullets:
  - Built X using Y. [View Project](https://link.com)

---

## SKILLS
enabled: true
---
Python, Go, Docker, AWS, Git

---

## HONORS & AWARDS
enabled: true
---

### Award Name
org: Awarding Organisation
date: Month Year
bullets:
  - Brief description of the award.
```

---

## Header

The top of every CV is automatically **centred** across all output formats (HTML, PDF, DOCX):

```
         Your Name
      Your Job Title
email  •  phone  •  Location  •  LinkedIn  •  GitHub
```

The contact line preserves the **exact order** of items as written in your Markdown input (`email`, `phone`, `extras`, `links`).

### `profession` field

The `profession` line is **optional**. Add it under `name` in `## META` to display a job title or role beneath your name:

```yaml
## META
name: Jane Smith
profession: Senior Software Engineer
```

Leave it out entirely to omit it — no blank line will appear.

### `extras` field

Use `extras:` to add arbitrary items to your contact line (such as location, certifications, work authorization, or status). Items appear in the exact position you place them in `## META`:

```yaml
## META
name: Jane Smith
profession: Senior Software Engineer
email: jane@example.com
phone: +1 (555) 000-0000
extras:
  - Dublin, Ireland
links:
  - [LinkedIn](https://linkedin.com/in/janesmith)
```

---

## Skills Auto-Separator

You don't need to type `•` manually in the skills section. Just list your skills separated by **commas**, **pipes**, or **bullets** — the builder normalises them all to `•` automatically:

```
## SKILLS
enabled: true
---
Python, Go, Docker, AWS, Git
```

```
## SKILLS
enabled: true
---
Python | Go | Docker | AWS | Git
```

```
## SKILLS
enabled: true
---
Python • Go • Docker • AWS • Git
```

All three produce the same output: `Python • Go • Docker • AWS • Git`

> **Note:** This only applies to flat tag lists. Paragraph text in other sections (like SUMMARY) is never affected.

---

## Adding / Omitting Sections

Set `enabled: false` on any section to exclude it from the output:

```
## PROJECTS
enabled: false
```

You can also add entirely new sections by following the same pattern — any `## SECTION NAME` block is picked up automatically:

```
## CERTIFICATIONS
enabled: true
---

### AWS Solutions Architect
org: Amazon Web Services
date: Jan 2023
bullets:
  - Associate level.
```

---

## Adding Links

Use standard Markdown link syntax anywhere in bullet points or text fields:

```
[Display Text](https://url.com)
```

Links render as clickable hyperlinks in HTML and DOCX, and as coloured text in PDF.

---

## Document Titles

All output formats include a document title derived from your name and profession:

| Format | Where |
|--------|-------|
| HTML | `<title>` tag in `<head>` |
| PDF | Embedded via HTML `<title>` (picked up by WeasyPrint) |
| DOCX | `File → Properties → Title` and `Author` fields |

The title format is `Name — Profession` if a profession is set, otherwise just `Name`.

---

## CLI Options

```
python cv_builder.py [input_file] [-o OUTPUT_DIR] [-n NAME] [--no-html] [--no-pdf] [--no-docx]
```

| Flag | Description |
|------|-------------|
| `input_file` | Path to your `.md` file (default: `input/cv_template.md`) |
| `-o`, `--output-dir` | Directory to save generated files (default: `output`) |
| `-n`, `--name` | Custom base filename without extension (default: input file name) |
| `--no-html` | Skip HTML generation |
| `--no-pdf` | Skip PDF generation |
| `--no-docx` | Skip DOCX generation |

---

## Requirements

- Python 3.10+
- `pyyaml` — config parsing
- `weasyprint` — PDF generation
- `python-docx` — DOCX generation

Install all with:
```bash
pip install -r requirements.txt
```

> **Note:** WeasyPrint may require system libraries on some platforms.
> See [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) if you hit install issues.

---

## Project Structure

```
.
├── cv_builder.py        # Main script
├── requirements.txt     # Python dependencies
├── setup_venv.sh        # Venv setup script
├── README.md            # This file
├── input/
│   ├── cv_template.md   # Your CV data (edit this)
│   └── test_cv.md       # Example with edge cases
└── output/              # Generated files (auto-created)
```
