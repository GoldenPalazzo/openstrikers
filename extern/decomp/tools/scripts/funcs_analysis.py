#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, cast

import humanfriendly
import prettytable

type ReportDict = dict[str, ReportValue]
type ReportList = list[ReportValue]
type ReportValue = ReportDict | ReportList | str

ROOT = Path(__file__).parents[2]
MODULE = "main"
REPORT_PATH = "build/G4QE01/report.json"

SKIP_SYMBOLS = {
}


@dataclass(frozen=True)
class Function:
    name: str
    unit: str
    size: int
    matched: float
    address: int


def create_trie(units: list[str]) -> re.Pattern[str]:
    return re.compile(
        rf"^{MODULE}/(?:{'|'.join(map(re.escape, units))})(?=/|$)" if units else ".*"
    )


def get_report() -> ReportDict:

    def run_ninja():
        proc = subprocess.run(
            cmd := ["ninja", REPORT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            print(stdout := proc.stdout.decode(), file=sys.stderr)
            print(stderr := proc.stderr.decode(), file=sys.stderr)

            raise subprocess.CalledProcessError(
                proc.returncode,
                " ".join(cmd),
                stdout,
                stderr,
            )

    run_ninja()

    with ROOT.joinpath(REPORT_PATH).open("r") as fp:
        report = cast(ReportDict, json.load(fp))

    return report


def print_funcs(
    units: list[str],
    size: tuple[int, int],
    matched: tuple[float, float],
    address: tuple[int, int],
    max_results: int,
    names_only: bool,
    by_address: bool,
    by_file: bool,
    file_summary: bool,
    max_name_length: int,
    show_full_names: bool,
):
    trie = create_trie(units)
    report = get_report()

    results: list[Function] = []

    for unit in map(
        lambda u: cast(ReportDict, u),
        cast(ReportList, report["units"]),
    ):

        unit_name = cast(str, unit["name"])
        m = trie.match(unit_name)
        if m is None:
            continue

        unit_name = unit_name.removeprefix(f"{MODULE}/")

        functions = cast(list[ReportDict], unit.get("functions", []))
        for function in functions:
            func_name = cast(str, function["name"])

            if func_name in SKIP_SYMBOLS:
                continue

            func_size = int(cast(str, function["size"]))
            if func_size < size[0] or func_size > size[1]:
                continue

            func_matched = float(cast(str, function.get("fuzzy_match_percent", 0)))
            if func_matched < matched[0] or func_matched > matched[1]:
                continue

            func_addr = int(
                cast(dict[str, str], function.get("metadata", {})).get(
                    "virtual_address", "0"
                )
            )
            if func_addr < address[0] or func_addr > address[1]:
                continue

            results.append(
                Function(
                    func_name,
                    unit_name,
                    func_size,
                    func_matched,
                    func_addr,
                )
            )

    # Handle file summary mode
    if file_summary:
        from collections import defaultdict
        file_counts = defaultdict(int)
        file_sizes = defaultdict(int)

        for f in results:
            file_path = (ROOT / "src" / f.unit).with_suffix(".cpp" if f.unit.startswith("Game/") else ".c").relative_to(ROOT)
            file_counts[str(file_path)] += 1
            file_sizes[str(file_path)] += f.size

        # Sort by count (descending), then by total size (descending)
        sorted_files = sorted(file_counts.items(), key=lambda x: (-x[1], -file_sizes[x[0]]))

        summary_table = prettytable.PrettyTable()
        summary_table.field_names = ["File", "Functions", "Total Size"]
        summary_table.align["File"] = "l"
        summary_table.align["Functions"] = "r"
        summary_table.align["Total Size"] = "r"
        summary_table.set_style(prettytable.TableStyle.PLAIN_COLUMNS)

        for file_path, count in sorted_files:
            summary_table.add_row([
                file_path,
                str(count),
                humanfriendly.format_size(file_sizes[file_path])
            ])

        print("Files with most easy functions:")
        print(summary_table)
        return

    # Determine sorting key
    def get_sort_key(f):
        if by_file:
            return (f.unit, f.address)
        elif by_address:
            return f.address
        else:
            return (f.size, f.address)

    results.sort(key=get_sort_key)
    if max_results > 0:
        results = results[:max_results]

    if names_only:
        for name in map(lambda f: f.name, results):
            print(name)
    else:
        table = prettytable.PrettyTable()
        table.field_names = ["Address", "File", "Function", "Size", "Matched"]
        table.align["Address"] = "c"
        table.align["File"] = "l"
        table.align["Function"] = "l"
        table.align["Size"] = "r"
        table.align["Matched"] = "r"
        table.set_style(prettytable.TableStyle.PLAIN_COLUMNS)

        # Group by file for better readability
        current_file = None
        for f in results:
            file_path = (ROOT / "src" / f.unit).with_suffix(".cpp" if f.unit.startswith("Game/") else ".c").relative_to(ROOT)

            # Add separator line when file changes
            if by_file and current_file != str(file_path):
                if current_file is not None:
                    table.add_row(["", "", "", "", ""], divider=True)
                current_file = str(file_path)

            # Truncate long function names for readability
            func_name = f.name
            if not show_full_names and len(func_name) > max_name_length:
                func_name = func_name[:max_name_length-3] + "..."

            table.add_row([
                f"{f.address:08X}",
                str(file_path),
                func_name,
                humanfriendly.format_size(f.size),
                f"{f.matched:.2f}%",
            ])

        print(table)
        
        # Show full function names for truncated ones
        if not show_full_names:
            truncated_funcs = [f for f in results if len(f.name) > max_name_length]
            if truncated_funcs:
                print(f"\nFull function names for truncated entries:")
                for f in truncated_funcs:
                    print(f"  {f.address:08X}: {f.name}")


def main():
    def sanitize_path(s: str) -> str:
        p = PurePosixPath(s.replace("\\", "/"))
        s = str(p.parent / p.stem)
        parents = [
            ROOT.as_posix(),
            "build/G4QE01",
            "src",
            "asm",
            "obj",
            "/",
        ]
        while True:
            prev = s
            for parent in parents:
                s = s.removeprefix(parent)
            if prev == s:
                break

        return s

    def sanitize_hex(s: str) -> int:
        return int(s.removeprefix("0x"), 16)

    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "units",
        nargs="*",
        type=sanitize_path,
        metavar="UNITS",
        help="directories or files to search",
    )
    _ = parser.add_argument(
        "-s",
        "--min-size",
        type=int,
        default=0,
        metavar="BYTES",
        help="the minimum size for a function",
    )
    _ = parser.add_argument(
        "-S",
        "--max-size",
        type=int,
        default=512,
        metavar="BYTES",
        help="the maximum size for a function (default 512)",
    )
    _ = parser.add_argument(
        "-v",
        "--min-virtual-address",
        dest="min_address",
        type=sanitize_hex,
        default=0,
        metavar="HEX",
        help="the minimum virtual address for a function",
    )
    _ = parser.add_argument(
        "-V",
        "--max-virtual-address",
        dest="max_address",
        type=sanitize_hex,
        default=0xFFFFFFFF,
        metavar="HEX",
        help="the maximum virtual address for a function",
    )
    _ = parser.add_argument(
        "-m",
        "--min-matched",
        type=float,
        default=0,
        metavar="PERCENT",
        help="the minimum fuzzy match %% for a function",
    )
    _ = parser.add_argument(
        "-M",
        "--max-matched",
        type=float,
        default=0,
        metavar="PERCENT",
        help="the maximum fuzzy match %% for a function (default 0%%)",
    )
    _ = parser.add_argument(
        "-n",
        "--max-results",
        type=lambda n: max(0, int(n)),
        default=0,
        metavar="RESULTS",
        help="the maximum number of functions to display",
    )
    _ = parser.add_argument(
        "-o",
        "--names-only",
        action="store_true",
        help="print only function names",
    )
    _ = parser.add_argument(
        "-a",
        "--order-by-address",
        dest="by_address",
        action="store_true",
        help="sort functions by address instead of size",
    )
    _ = parser.add_argument(
        "-f",
        "--order-by-file",
        dest="by_file",
        action="store_true",
        help="sort functions by file name",
    )
    _ = parser.add_argument(
        "--file-summary",
        action="store_true",
        help="show summary of easy functions per file",
    )
    _ = parser.add_argument(
        "--max-name-length",
        type=int,
        default=50,
        metavar="LENGTH",
        help="maximum function name length before truncation (default 50)",
    )
    _ = parser.add_argument(
        "--show-full-names",
        action="store_true",
        help="show full function names without truncation",
    )
    args = parser.parse_args()

    print_funcs(
        cast(list[str], args.units),
        (cast(int, args.min_size), cast(int, args.max_size)),
        (cast(float, args.min_matched), cast(float, args.max_matched)),
        (cast(int, args.min_address), cast(int, args.max_address)),
        cast(int, args.max_results),
        cast(bool, args.names_only),
        cast(bool, args.by_address),
        cast(bool, args.by_file),
        cast(bool, args.file_summary),
        cast(int, args.max_name_length),
        cast(bool, args.show_full_names),
    )


if __name__ == "__main__":
    main()
