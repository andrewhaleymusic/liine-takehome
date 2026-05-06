import argparse
import logging
import subprocess

import uvicorn

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.etl.service import run_etl

logger = logging.getLogger(__name__)


def _run_tool(args: list[str]) -> int:
    completed = subprocess.run(args, check=False)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="liine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("serve")

    etl_parser = subparsers.add_parser("etl")
    etl_parser.add_argument(
        "--truncate",
        action="store_true",
        help="Delete existing runtime data before loading the CSV.",
    )

    subparsers.add_parser("test")
    subparsers.add_parser("fmt")
    subparsers.add_parser("lint")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)

    command = args.command

    if command == "serve":
        uvicorn.run(
            "app.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=False,
        )
        return 0

    if command == "etl":
        return run_etl(settings, truncate=args.truncate)

    if command == "test":
        return _run_tool(["pytest", "-q"])

    if command == "fmt":
        format_commands = [
            ["isort", "app", "tests"],
            ["black", "app", "tests"],
        ]
        for format_command in format_commands:
            return_code = _run_tool(format_command)
            if return_code != 0:
                return return_code
        return 0

    if command == "lint":
        lint_commands = [
            ["black", "--check", "app", "tests"],
            ["isort", "--check-only", "app", "tests"],
            ["mypy", "app"],
            ["pytest", "-q"],
        ]
        for lint_command in lint_commands:
            return_code = _run_tool(lint_command)
            if return_code != 0:
                return return_code
        return 0

    parser.error(f"Unknown subcommand: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
