#!/usr/bin/env python3
"""Controller for RAISHO Youzan weekly analysis modes."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_distributor_report import build_distributor_report  # noqa: E402
from build_weekly_tables import build_tables  # noqa: E402
from create_audit_note import build_note  # noqa: E402
from create_backend_audit_report import build_report  # noqa: E402


DEFAULT_BASE = Path("/Users/wisemantong/Desktop/有赞后台分析/周报")


def ensure_week_dir(base_dir: Path, week_label: str) -> Path:
    week_dir = base_dir / week_label
    week_dir.mkdir(parents=True, exist_ok=True)
    (week_dir / "原始数据").mkdir(exist_ok=True)
    (week_dir / "巡检证据").mkdir(exist_ok=True)
    return week_dir


def write_run_log(week_dir: Path, lines: list[str]) -> Path:
    log_path = week_dir / "运行日志.md"
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# 运行日志\n\n"
    entry = "\n".join([f"## {date.today().isoformat()}", *[f"- {line}" for line in lines], ""])
    log_path.write_text(existing.rstrip() + "\n\n" + entry, encoding="utf-8")
    return log_path


def create_or_keep_audit_note(week_dir: Path, week_label: str, date_range: str, overwrite: bool) -> Path:
    audit_note = week_dir / "后台巡检记录.md"
    if overwrite or not audit_note.exists():
        audit_note.write_text(build_note(week_label, date_range), encoding="utf-8")
    return audit_note


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["weekly", "distributor", "backend-audit"])
    parser.add_argument("--week-label", required=True)
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE))
    parser.add_argument("--date-range", default="")
    parser.add_argument("--detail", help="Core order-item detail export containing yz_open_id")
    parser.add_argument("--audit-note", help="Backend audit note markdown path")
    parser.add_argument("--distributor", help="Distributor name for distributor mode")
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--overwrite-audit-note", action="store_true")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser()
    week_dir = ensure_week_dir(base_dir, args.week_label)
    outputs: list[Path] = []

    if args.mode == "weekly":
        if not args.detail:
            raise SystemExit("--detail is required for weekly mode")
        audit_note = Path(args.audit_note).expanduser() if args.audit_note else create_or_keep_audit_note(
            week_dir, args.week_label, args.date_range, args.overwrite_audit_note
        )
        workbook = build_tables(Path(args.detail).expanduser(), week_dir, args.week_label, audit_note)
        outputs.extend([audit_note, workbook])

    elif args.mode == "distributor":
        if not args.detail:
            raise SystemExit("--detail is required for distributor mode")
        if not args.distributor:
            raise SystemExit("--distributor is required for distributor mode")
        output_dir = week_dir / "分销商分析"
        workbook, summary = build_distributor_report(
            Path(args.detail).expanduser(),
            output_dir,
            args.week_label,
            args.distributor,
            args.exact,
        )
        outputs.extend([workbook, summary])

    elif args.mode == "backend-audit":
        audit_note = Path(args.audit_note).expanduser() if args.audit_note else create_or_keep_audit_note(
            week_dir, args.week_label, args.date_range, args.overwrite_audit_note
        )
        report = build_report(audit_note, week_dir, args.week_label)
        outputs.extend([audit_note, report])

    log = write_run_log(week_dir, [f"mode={args.mode}", *[f"output={path}" for path in outputs]])
    outputs.append(log)
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()

