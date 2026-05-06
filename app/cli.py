import logging
import subprocess
import sys

import uvicorn

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.etl.service import run_etl

logger = logging.getLogger(__name__)


def _run_tool(args: list[str]) -> int:
    completed = subprocess.run(args, check=False)
    return completed.returncode


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)

    if len(sys.argv) < 2:
        logger.error("Expected a subcommand: serve, etl, test, fmt, or lint.")
        return 2

    command = sys.argv[1]

    if command == "serve":
        uvicorn.run(
            "app.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=False,
        )
        return 0

    if command == "etl":
        extra_args = sys.argv[2:]
        supported_args = {"--truncate"}
        unknown_args = [arg for arg in extra_args if arg not in supported_args]
        if unknown_args:
            logger.error("Unknown etl arguments: %s", " ".join(unknown_args))
            return 2
        return run_etl(settings, truncate="--truncate" in extra_args)

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

    logger.error("Unknown subcommand: %s", command)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
