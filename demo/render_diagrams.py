"""Render PlantUML diagrams to PNG or SVG images for training video.

Supports three rendering methods:
  1. Local PlantUML jar (fastest, requires Java)
  2. PlantUML online server (no install needed)
  3. Skip rendering and open .puml files directly in IDE/VS Code

Usage:
    python demo/render_diagrams.py              # Auto-detect method (PNG)
    python demo/render_diagrams.py --online     # Use PlantUML server (PNG)
    python demo/render_diagrams.py --local      # Use local plantuml.jar (PNG)
    python demo/render_diagrams.py --svg        # Render SVG via online server
    python demo/render_diagrams.py --svg --local  # Render SVG via local jar
    python demo/render_diagrams.py --list       # Just list the files in order

Output:  docs/diagrams/rendered/*.png  or  docs/diagrams/rendered/*.svg
"""

import io
import os
import subprocess
import sys
import zlib
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import urllib.request
import base64

DIAGRAMS_DIR = Path("docs/diagrams")
WALKTHROUGH_DIR = DIAGRAMS_DIR / "walkthrough"
RENDERED_DIR = DIAGRAMS_DIR / "rendered"

# Ordered list of diagrams for the training walkthrough
WALKTHROUGH_ORDER = [
    # Architecture walkthrough — progressive highlight
    ("architecture_step0_overview.puml", "Full AMI Architecture Overview"),
    ("architecture_step1_meters.puml", "Step 1: Landis+Gyr Meter Fleet"),
    ("architecture_step2_comms.puml", "Step 2: Communication Pathways"),
    ("architecture_step3_hes.puml", "Step 3: Gridstream HES (Head-End)"),
    ("architecture_step4_mdm.puml", "Step 4: Core MDMS / VEE Pipeline"),
    ("architecture_step5_analytics.puml", "Step 5: Gridstream Analytics"),
    ("architecture_step6_api.puml", "Step 6: CIM REST API Layer"),
    ("architecture_step7_integration.puml", "Step 7: Client Integration Points"),
    # Software component diagrams
    ("component_step1_simulator.puml", "Software: Simulator Layer"),
    ("component_step2_api.puml", "Software: API Layer & Routers"),
]

# Original diagrams (non-walkthrough)
ORIGINAL_DIAGRAMS = [
    ("sequence_get_readings.puml", "Sequence: Get Meter Readings"),
    ("sequence_startup.puml", "Sequence: Application Startup"),
    ("use_case.puml", "Use Case Diagram"),
]

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"


def plantuml_encode(text: str) -> str:
    """Encode PlantUML text for the online server URL."""
    compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    return _encode64(compressed)


def _encode64(data: bytes) -> str:
    """PlantUML's custom base64 encoding."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    result = []
    for i in range(0, len(data), 3):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        b3 = data[i + 2] if i + 2 < len(data) else 0

        result.append(chars[b1 >> 2])
        result.append(chars[((b1 & 0x3) << 4) | (b2 >> 4)])
        result.append(chars[((b2 & 0xF) << 2) | (b3 >> 6)])
        result.append(chars[b3 & 0x3F])
    return "".join(result)


def render_online(puml_path: Path, output_path: Path, fmt: str = "png") -> bool:
    """Render a .puml file using the PlantUML online server."""
    text = puml_path.read_text(encoding="utf-8")
    encoded = plantuml_encode(text)
    url = f"http://www.plantuml.com/plantuml/{fmt}/{encoded}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PlantUML-Renderer/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            output_path.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    {RED}Error: {e}{RESET}")
        return False


def render_local(puml_path: Path, output_dir: Path, fmt: str = "png") -> bool:
    """Render a .puml file using a local plantuml.jar."""
    jar = os.environ.get("PLANTUML_JAR", "plantuml.jar")
    try:
        subprocess.run(
            ["java", "-jar", jar, f"-t{fmt}", "-o", str(output_dir.resolve()), str(puml_path)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        return True
    except FileNotFoundError:
        print(f"    {RED}Java not found. Install Java or use --online.{RESET}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"    {RED}PlantUML error: {e.stderr.decode()}{RESET}")
        return False


def has_local_plantuml() -> bool:
    """Check if local PlantUML jar + Java are available."""
    jar = os.environ.get("PLANTUML_JAR", "plantuml.jar")
    try:
        subprocess.run(
            ["java", "-jar", jar, "-version"],
            capture_output=True, timeout=10,
        )
        return True
    except Exception:
        return False


def list_diagrams() -> None:
    """Print the ordered list of walkthrough diagrams."""
    print()
    print(f"  {BOLD}Architecture Walkthrough (8 steps):{RESET}")
    print(f"  {DIM}Progressive highlighting of each AMI component{RESET}")
    print()
    for i, (filename, desc) in enumerate(WALKTHROUGH_ORDER):
        path = WALKTHROUGH_DIR / filename
        exists = path.exists()
        status = f"{GREEN}exists{RESET}" if exists else f"{RED}missing{RESET}"
        print(f"    {i+1:2d}. {CYAN}{filename:<45}{RESET} {desc}  [{status}]")

    print()
    print(f"  {BOLD}Sequence & Use Case Diagrams:{RESET}")
    print()
    for i, (filename, desc) in enumerate(ORIGINAL_DIAGRAMS):
        path = DIAGRAMS_DIR / filename
        exists = path.exists()
        status = f"{GREEN}exists{RESET}" if exists else f"{RED}missing{RESET}"
        print(f"    {i+11:2d}. {CYAN}{filename:<45}{RESET} {desc}  [{status}]")
    print()


def render_all(method: str, fmt: str = "png") -> None:
    """Render all diagrams using the specified method and format."""
    RENDERED_DIR.mkdir(parents=True, exist_ok=True)

    all_diagrams = [
        (WALKTHROUGH_DIR / f, desc) for f, desc in WALKTHROUGH_ORDER
    ] + [
        (DIAGRAMS_DIR / f, desc) for f, desc in ORIGINAL_DIAGRAMS
    ]

    total = len(all_diagrams)
    success = 0

    print()
    print(f"  {BOLD}Rendering {total} diagrams to {fmt.upper()} using {method} method...{RESET}")
    print()

    for i, (path, desc) in enumerate(all_diagrams):
        output = RENDERED_DIR / path.with_suffix(f".{fmt}").name
        print(f"  [{i+1:2d}/{total}] {desc}")
        print(f"         {DIM}{path} → {output}{RESET}")

        if not path.exists():
            print(f"         {RED}Source file not found, skipping{RESET}")
            continue

        if method == "online":
            ok = render_online(path, output, fmt)
        else:
            ok = render_local(path, RENDERED_DIR, fmt)

        if ok:
            success += 1
            size_kb = output.stat().st_size / 1024
            print(f"         {GREEN}OK ({size_kb:.0f} KB){RESET}")
        print()

    print(f"  {BOLD}Done: {success}/{total} rendered to {RENDERED_DIR}/{RESET}")
    print()


def main() -> None:
    print()
    print(f"  {BOLD}PlantUML Diagram Renderer for Training Video{RESET}")
    print(f"  {DIM}Renders walkthrough diagrams with step-by-step highlighting{RESET}")
    print()

    args = sys.argv[1:]
    fmt = "svg" if "--svg" in args else "png"

    if "--list" in args:
        list_diagrams()
        return

    if "--online" in args:
        render_all("online", fmt)
    elif "--local" in args:
        render_all("local", fmt)
    else:
        # Auto-detect
        if has_local_plantuml():
            print(f"  {GREEN}Found local PlantUML jar{RESET}")
            render_all("local", fmt)
        else:
            print(f"  {YELLOW}No local PlantUML. Using online server...{RESET}")
            print(f"  {DIM}(Set PLANTUML_JAR env var or use --local for local rendering){RESET}")
            print()
            render_all("online", fmt)


if __name__ == "__main__":
    main()
