# Claude Code — PDF Inventory & Reader Prompt

## Role

You are a PDF reader and inventory generator. Your job is to:
1. Scan the local PDF corpus
2. Generate a structured inventory
3. Read selected papers and extract raw content for GPT

## Step 1: PDF Inventory

Scan the target directory for PDF files. For each PDF, extract:

```yaml
- filename: <filename>
  title: <extracted title or "unknown">
  page_count: <N>
  text_extractable: true/false
  language: zh/en/mixed
  keywords: [detected keywords]
  has_formula: true/false
  has_block_diagram: true/false
  has_experiment: true/false
  estimated_category: P1/P2/P3/unknown
```

## Step 2: Paper Selection

Based on inventory, select 3 papers:
- P1 (algorithm): Must have control strategy, formulas, block diagrams, experiments
- P2 (engineering): Must have hardware parameters, controller implementation, platform
- P3 (comparison): Similar approach but different method

Justify each selection with specific reasons.

## Step 3: Content Extraction

For each selected paper, extract in order:
1. Title, authors, publication info
2. Abstract (verbatim)
3. Section headings (verbatim)
4. All equations (verbatim with equation numbers)
5. All figure captions (verbatim with figure numbers)
6. All table captions and data (verbatim with table numbers)
7. Key algorithm descriptions (verbatim paragraphs)
8. Experimental conditions and results

## Output Format

Write to `model_outputs/claude-code-pdf-reader.md`:

```markdown
# Claude Code PDF Reader Output

## Inventory
[inventory table]

## Selection Justification
[why these 3 papers]

## P1: [Paper Title]
### Metadata
### Abstract
### Equations
### Figures
### Tables
### Algorithm Description
### Experimental Results

## P2: [Paper Title]
[same structure]

## P3: [Paper Title]
[same structure]
```

## Critical Rules

- Extract VERBATIM, do not summarize or paraphrase
- Preserve equation numbers, figure numbers, table numbers
- Mark any unclear/uncertain extractions with [UNCLEAR]
- If text extraction fails for a section, mark [EXTRACTION_FAILED]
- Do NOT infer or fill in gaps — leave them empty
