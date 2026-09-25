"""Record the CPU, core count, memory, and operating system of this machine."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from ngram_cache_bench.results import MACHINE_PATH, Machine, write_rows


def cpu_name() -> str:
    system = platform.system()
    if system == "Darwin":
        # The standard library reports only "arm" on Apple silicon, so we ask sysctl for the model name.
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    if system == "Linux":
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
        raise SystemExit("/proc/cpuinfo has no model name")
    raise SystemExit(f"unsupported platform {system}")


def os_name() -> str:
    system = platform.system()
    if system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    if system == "Linux":
        return platform.freedesktop_os_release()["PRETTY_NAME"]
    raise SystemExit(f"unsupported platform {system}")


def run() -> None:
    page_size = os.sysconf("SC_PAGE_SIZE")
    page_count = os.sysconf("SC_PHYS_PAGES")
    cores = os.cpu_count()
    if cores is None:
        raise SystemExit("cannot count the CPU cores")
    machine = Machine(cpu=cpu_name(), cores=cores, memory_bytes=page_size * page_count, os=os_name())
    write_rows(MACHINE_PATH, [machine])
