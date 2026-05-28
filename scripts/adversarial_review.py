#!/usr/bin/env python3
"""Adversarial Review: devil's advocate + defense + three-way fusion.

Usage:
  python3 scripts/adversarial_review.py <artifact> <review> [--mode bridge|mock] [--timeout N]
"""
import argparse, json, re, sys, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from tf_orchestrator import Finding, Review, parse_review

ACCEPT_VERDICTS = {"PASS", "PASS_WITH_NOTES"}
_JSON_TPL = '```json\n{json}\n```\n'
_ATK = ("You are a devil's advocate. Find flaws the original reviewer missed. "
        "## Artifact\n```markdown\n{artifact}\n```\n"
        "## Original Review\n```markdown\n{review}\n```\n"
        "Look for: unchallenged assumptions, logical gaps, understated severity, "
        "inflated scores, contradictions. If the review is thorough, say so.\n"
        "Respond with a JSON block: {json} Then a brief narrative.")
_DEF = ("You are a defense reviewer. Evaluate whether a devil's advocate attack "
        "on the original review is valid.\n"
        "## Artifact\n```markdown\n{artifact}\n```\n"
        "## Original Review\n```markdown\n{review}\n```\n"
        "## Attack\n```markdown\n{attack}\n```\n"
        "Evaluate each attack finding. Defend the original where correct. "
        "Acknowledge valid attack points. Give your own score.\n"
        "Respond with a JSON block: {json} Then a brief narrative.")
_ATK_JSON = ('{"reviewer_role":"attacker","score":0-100,'
             '"verdict":"PASS|PASS_WITH_NOTES|FAIL",'
             '"confidence":"HIGH|MEDIUM|LOW",'
             '"findings":[{"id":"ATT-001","severity":"CRITICAL|HIGH|MEDIUM|LOW",'
             '"blocking":true|false,"evidence_path":null,'
             '"claim":"what is wrong","correction":"what to do"}],'
             '"final_recommendation":"ACCEPT|REPAIR|ESCALATE"}')
_DEF_JSON = ('{"reviewer_role":"defender","score":0-100,'
             '"verdict":"PASS|PASS_WITH_NOTES|FAIL",'
             '"confidence":"HIGH|MEDIUM|LOW",'
             '"findings":[{"id":"DEF-001","severity":"CRITICAL|HIGH|MEDIUM|LOW",'
             '"blocking":true|false,"evidence_path":null,'
             '"claim":"assessment","correction":"what to do"}],'
             '"final_recommendation":"ACCEPT|REPAIR|ESCALATE"}')
_MOCK_ATK = ('{"reviewer_role":"attacker","score":72,"verdict":"PASS_WITH_NOTES",'
             '"confidence":"MEDIUM","findings":[{"id":"ATT-001","severity":"MEDIUM",'
             '"blocking":false,"evidence_path":null,'
             '"claim":"Review assumes all edge cases covered without evidence",'
             '"correction":"Add explicit edge-case analysis"}],'
             '"final_recommendation":"REPAIR"}')
_MOCK_DEF = ('{"reviewer_role":"defender","score":80,"verdict":"PASS_WITH_NOTES",'
             '"confidence":"MEDIUM","findings":[{"id":"DEF-001","severity":"LOW",'
             '"blocking":false,"evidence_path":null,'
             '"claim":"ATT-001 is partially valid but not blocking",'
             '"correction":"Note for future runs, no repair needed"}],'
             '"final_recommendation":"ACCEPT"}')


@dataclass
class AdversarialResult:
    original_review: Dict
    attack_review: Dict
    defense_review: Dict
    fused_gate_decision: str
    fused_confidence: str
    fused_score_avg: float
    attack_new_findings: int
    wall_seconds: float
    memory_recorded: bool = False


def _json_block(text: str) -> Optional[Dict]:
    for m in re.finditer(r"```json\s*\n(.*?)```", text, re.DOTALL):
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
    return None


def _mock(out: Path, data: str) -> str:
    content = f"# Review\n\n```json\n{data}\n```\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return content


def _bridge(prompt: str, out: Path, timeout: int) -> str:
    from tf_agent_executor import AgentExecutor, AgentTask
    pp = out.parent / "prompts" / (out.stem + "_prompt.md")
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(prompt, encoding="utf-8")
    r = AgentExecutor().execute_one(AgentTask(
        subproblem_id=out.stem, prompt_path=str(pp),
        artifact_path=str(out), timeout=timeout))
    if not r.success:
        raise RuntimeError(f"Bridge failed: {r.error}")
    return out.read_text(encoding="utf-8")


def fuse_three(orig: Review, atk: Optional[Dict], defe: Optional[Dict]) -> Tuple[str, str, float, int]:
    scores, verdicts = {"original": orig.score}, {"original": orig.verdict}
    blocking = [f for f in orig.findings if f.blocking]
    atk_n = 0
    for label, data in [("attacker", atk), ("defender", defe)]:
        if not data:
            continue
        scores[label] = data.get("score", 0)
        verdicts[label] = data.get("verdict", "FAIL")
        for f in data.get("findings", []):
            atk_n += label == "attacker"
            if f.get("blocking"):
                blocking.append(Finding(id=f.get("id","?"), severity=f.get("severity","MEDIUM"),
                    blocking=True, status="open", evidence_path=None,
                    claim=f.get("claim",""), correction=f.get("correction","")))
    avg = sum(scores.values()) / len(scores) if scores else 0
    decision = "ACCEPT" if not blocking and all(v in ACCEPT_VERDICTS for v in verdicts.values()) and avg >= 80 else "REPAIR"
    v = list(verdicts.values())
    conf = "HIGH" if len(set(v)) == 1 else "MEDIUM" if len(set(v)) <= 2 else "LOW"
    return decision, conf, round(avg, 1), atk_n


def record_memory(res: AdversarialResult) -> bool:
    p = REPO_ROOT / "knowledge" / "orchestrator" / "outcome_memory.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"run_id": f"adversarial-{int(time.time())}", "task_id": "adversarial_review",
           "task_type": "adversarial_review", "gate_status": res.fused_gate_decision,
           "wall_seconds": res.wall_seconds, "attack_new_findings": res.attack_new_findings,
           "confidence": res.fused_confidence,
           "original_score": res.original_review.get("score", 0),
           "attack_score": res.attack_review.get("score", 0),
           "defense_score": res.defense_review.get("score", 0),
           "fused_score_avg": res.fused_score_avg}
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return True


def run(artifact: Path, review: Path, run_dir: Path,
        mode: str = "bridge", timeout: int = 300) -> AdversarialResult:
    t0 = time.monotonic()
    a_text = artifact.read_text(encoding="utf-8") if artifact.exists() else "(missing)"
    r_text = review.read_text(encoding="utf-8") if review.exists() else "(missing)"
    orig = parse_review(r_text)
    atk_path, def_path = run_dir / "adversarial" / "attack_review.md", run_dir / "adversarial" / "defense_review.md"
    atk_t = _mock(atk_path, _MOCK_ATK) if mode == "mock" else \
        _bridge(_ATK.format(artifact=a_text, review=r_text, json=_ATK_JSON), atk_path, timeout)
    atk = _json_block(atk_t)
    print(f"Attack score: {atk.get('score','?') if atk else 'parse_failed'}")
    def_t = _mock(def_path, _MOCK_DEF) if mode == "mock" else \
        _bridge(_DEF.format(artifact=a_text, review=r_text, attack=atk_t, json=_DEF_JSON), def_path, timeout)
    defe = _json_block(def_t)
    print(f"Defense score: {defe.get('score','?') if defe else 'parse_failed'}")
    gate, conf, avg, atk_n = fuse_three(orig, atk, defe)
    print(f"Gate: {gate} (confidence={conf}, avg={avg})")
    wall = round(time.monotonic() - t0, 1)
    res = AdversarialResult(
        original_review={"score": orig.score, "verdict": orig.verdict, "confidence": orig.confidence,
                         "findings_count": len(orig.findings)},
        attack_review=atk or {"score": 0, "verdict": "PARSE_FAILED"},
        defense_review=defe or {"score": 0, "verdict": "PARSE_FAILED"},
        fused_gate_decision=gate, fused_confidence=conf, fused_score_avg=avg,
        attack_new_findings=atk_n, wall_seconds=wall)
    res.memory_recorded = record_memory(res)
    v_path = run_dir / "adversarial" / "adversarial_verdict.json"
    v_path.parent.mkdir(parents=True, exist_ok=True)
    v_path.write_text(json.dumps(asdict(res), indent=2, default=str), encoding="utf-8")
    print(f"=== Adversarial Review: {gate} ({wall}s) ===")
    return res


def main():
    ap = argparse.ArgumentParser(description="Adversarial Review")
    ap.add_argument("artifact_path", nargs="?", type=Path)
    ap.add_argument("review_path", nargs="?", type=Path)
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--mode", choices=["bridge", "mock"], default="bridge")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()
    if args.run_dir:
        arts, revs = list(args.run_dir.glob("**/artifact*.md")), list(args.run_dir.glob("**/review*.md"))
        if not arts or not revs:
            print("ERROR: --run-dir must contain artifact and review files", file=sys.stderr); sys.exit(1)
        artifact, review = arts[0], revs[0]
        rd = args.run_dir
    elif args.artifact_path and args.review_path:
        artifact, review = args.artifact_path, args.review_path
        rd = review.parent.parent
    else:
        ap.print_help(); sys.exit(1)
    rd.mkdir(parents=True, exist_ok=True)
    run(artifact, review, rd, args.mode, args.timeout)


if __name__ == "__main__":
    main()
