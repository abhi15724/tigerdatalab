"""End-to-end local-first AI training dataset pipeline."""
from __future__ import annotations
from pathlib import Path
import csv, json
from typing import Any
from .datasets import to_sft, split_records
from .dedup import deduplicate
from .privacy import mask_record

def _read(source: str | Path) -> list[dict[str, Any]]:
    path = Path(source)
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f: return [dict(x) for x in csv.DictReader(f)]
    if path.suffix.lower() == ".jsonl":
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8")); return value if isinstance(value, list) else [value]
    raise ValueError("Supported formats: CSV, JSON and JSONL")

class AIDataset:
    def __init__(self, source: str | Path, task: str = "sft"):
        self.source, self.task, self.rows = str(source), task.lower(), _read(source)
        self.prepared: list[dict[str, Any]] = []
        self.stats: dict[str, Any] = {}

    def run(self) -> "AIDataset":
        if self.task not in {"sft", "text"}: raise ValueError("Supported tasks: sft, text")
        records=[]; rejected=0; pii={}
        for row in self.rows:
            item = to_sft(row) if self.task == "sft" else {"text": " ".join(str(v).strip() for v in row.values() if str(v).strip())}
            if not item or not any(str(v).strip() for v in item.values()): rejected += 1; continue
            item, found = mask_record(item)
            for k,v in found.items(): pii[k]=pii.get(k,0)+v
            records.append(item)
        records, duplicates = deduplicate(records)
        self.prepared=records
        self.stats={"input_records":len(self.rows),"output_records":len(records),"duplicates_removed":duplicates,"rejected_records":rejected,"pii_masked":pii,"task":self.task}
        return self

    def summary(self) -> dict[str, Any]: return dict(self.stats)

    def quality(self) -> dict[str, Any]:
        total=max(len(self.rows),1); retained=len(self.prepared)
        completeness=100.0 if retained else 0.0
        retention=retained/total*100
        return {"overall":round(completeness*.7+retention*.3,2),"records":retained,"retention":round(retention,2),"completeness":completeness}

    def export(self, directory: str | Path, train_ratio: float=.8, validation_ratio: float=.1) -> Path:
        if not self.prepared: self.run()
        out=Path(directory); out.mkdir(parents=True,exist_ok=True)
        for name, records in split_records(self.prepared,train_ratio,validation_ratio).items():
            with (out/f"{name}.jsonl").open("w",encoding="utf-8") as f:
                for record in records: f.write(json.dumps(record,ensure_ascii=False)+"\n")
        quality=self.quality()
        (out/"quality_report.json").write_text(json.dumps(quality,indent=2),encoding="utf-8")
        (out/"lineage.json").write_text(json.dumps({"source":self.source,"task":self.task,"pipeline":["ingest","sft_format","pii_mask","deduplicate","quality","split","export"],"stats":self.stats},indent=2),encoding="utf-8")
        (out/"dataset_card.md").write_text(f"# TigerDataLab Dataset\n\n- Source: `{self.source}`\n- Task: `{self.task}`\n- Records: {len(self.prepared)}\n- Quality: {quality['overall']}\n",encoding="utf-8")
        return out

def prepare(source: str | Path, task: str="sft") -> AIDataset: return AIDataset(source,task)
