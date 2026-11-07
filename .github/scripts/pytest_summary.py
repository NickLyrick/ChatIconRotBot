"""Render a pytest JUnit XML report as Markdown for the GitHub job summary.

Usage: python pytest_summary.py pytest-report.xml >> "$GITHUB_STEP_SUMMARY"
"""

import sys
import xml.etree.ElementTree as ET


def main(path: str) -> None:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))

    total = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0)) for s in suites)
    errors = sum(int(s.get("errors", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)
    passed = total - failures - errors - skipped
    seconds = sum(float(s.get("time", 0)) for s in suites)

    icon = "✅" if failures + errors == 0 else "❌"
    print(f"## {icon} Tests\n")
    print("| Passed | Failed | Errors | Skipped | Total | Time |")
    print("|---|---|---|---|---|---|")
    print(f"| {passed} | {failures} | {errors} | {skipped} | {total} | {seconds:.1f}s |")

    broken = [
        (case, problem)
        for case in root.iter("testcase")
        for problem in case
        if problem.tag in ("failure", "error")
    ]
    if broken:
        print("\n### Failed tests\n")
        for case, problem in broken:
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            message = (problem.get("message") or "").strip()
            print(f"<details><summary><code>{name}</code></summary>\n")
            if message:
                print(f"{message}\n")
            print(f"```\n{(problem.text or '').strip()}\n```\n</details>\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
