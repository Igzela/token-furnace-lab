# Algorithm Extraction Rubric

## Overview

5-dimension evaluation rubric for PDF-to-algorithm extraction quality. Total: 100 points.

## Dimensions

### 1. Accuracy (30 points)

**Definition**: Formulas, variables, and experimental conditions are extracted correctly. No inference presented as fact.

| Score | Criteria |
|-------|----------|
| 25-30 | All equations verbatim correct, variables match paper, no inference-as-fact |
| 18-24 | Minor equation errors (subscripts, superscripts), most variables correct |
| 10-17 | Some equations correct, some variables misidentified, some inference-as-fact |
| 0-9 | Major equation errors, variables wrong, frequent inference-as-fact |

**Check items**:
- [ ] Equation numbers preserved
- [ ] Variable names match paper
- [ ] Units preserved
- [ ] No [INFERRED] items presented as fact
- [ ] Experimental values match paper

### 2. Completeness (20 points)

**Definition**: Coverage of problem, algorithm, formulas, experiments, and applicability boundaries.

| Score | Criteria |
|-------|----------|
| 17-20 | All sections of algorithm card filled, no null values |
| 12-16 | Most sections filled, 1-2 null values |
| 6-11 | Several sections incomplete, 3-5 null values |
| 0-5 | Many sections empty, extraction is partial |

**Check items**:
- [ ] Problem definition complete
- [ ] Algorithm description complete (inputs, outputs, equations, pseudocode)
- [ ] Implementation details present
- [ ] Experimental results present
- [ ] Applicability boundaries stated

### 3. Implementability (25 points)

**Definition**: Can be converted to pseudocode, control flow, or engineering plan.

| Score | Criteria |
|-------|----------|
| 21-25 | Pseudocode is directly implementable, all parameters specified |
| 15-20 | Pseudocode is mostly clear, some parameters need estimation |
| 8-14 | Pseudocode is vague, many parameters missing |
| 0-7 | No pseudocode or pseudocode is incomprehensible |

**Check items**:
- [ ] Pseudocode exists and is step-by-step
- [ ] Control loop structure clear
- [ ] Input/output variables specified with types/units
- [ ] Sampling/computation requirements stated
- [ ] Tuning guidance provided

### 4. Evidence Quality (15 points)

**Definition**: Every key conclusion has page number, figure number, equation number, or table source.

| Score | Criteria |
|-------|----------|
| 13-15 | Every claim has specific reference (page, eq, fig, table) |
| 9-12 | Most claims have references, some generic |
| 5-8 | Some claims have references, many generic or missing |
| 0-4 | Few or no references, claims unsubstantiated |

**Check items**:
- [ ] Equations reference original numbers
- [ ] Figures reference original captions
- [ ] Tables reference original data
- [ ] Key claims have page numbers
- [ ] No [UNCLEAR] or [EXTRACTION_FAILED] without explanation

### 5. Project Relevance (10 points)

**Definition**: Can serve the 22µF DC-Link + sensorless FOC + pump scenario.

| Score | Criteria |
|-------|----------|
| 9-10 | Directly applicable to target scenario, minimal modification needed |
| 6-8 | Mostly applicable, some adaptation needed |
| 3-5 | Partially applicable, significant adaptation needed |
| 0-2 | Not applicable or irrelevant to target scenario |

**Check items**:
- [ ] Addresses small DC-Link capacitance
- [ ] Compatible with sensorless FOC
- [ ] Feasible on TMS320F28035
- [ ] Applicable to pump load
- [ ] Relevance score and justification provided

## Verdict Criteria

| Verdict | Score Range | Description |
|---------|-------------|-------------|
| PASS | 75-100 | Implementable algorithm flow with evidence |
| PASS_WITH_NOTES | 50-74 | Useful direction but gaps in parameters, formulas, or experiments |
| FAIL | 0-49 | Summary only, not convertible; or missing evidence; or hallucinations |

## Usage

```bash
# Evaluate extraction quality
# 1. Score each dimension
# 2. Sum total
# 3. Apply verdict threshold
# 4. Document findings in extraction-quality-report.md
```
