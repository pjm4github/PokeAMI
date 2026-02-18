"""Training video diagram walkthrough — guided narration with PlantUML diagrams.

Walks through the architecture step by step, opening each rendered diagram
and displaying narrator talking points for that step.

Usage:
    python demo/diagrams.py              # Interactive walkthrough (all steps)
    python demo/diagrams.py --render     # Render PNGs first, then walkthrough
    python demo/diagrams.py N            # Jump to step N (1-12)

Prerequisites:
    Run `python demo/render_diagrams.py --online` first to generate PNGs,
    or use `--render` flag to render inline.

If PNGs are not available, the script displays the .puml source path
so you can open it in VS Code (with PlantUML extension) or any viewer.
"""

import io
import os
import platform
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[97m"
RESET = "\033[0m"

DIAGRAMS_DIR = Path("docs/diagrams")
WALKTHROUGH_DIR = DIAGRAMS_DIR / "walkthrough"
RENDERED_DIR = DIAGRAMS_DIR / "rendered"


def hr() -> None:
    print(f"  {DIM}{'─' * 74}{RESET}")


def open_image(path: Path) -> None:
    """Open an image file in the system's default viewer."""
    if not path.exists():
        print(f"  {YELLOW}Image not rendered yet: {path}{RESET}")
        print(f"  {DIM}Open the .puml source in VS Code with PlantUML extension,{RESET}")
        print(f"  {DIM}or run: python demo/render_diagrams.py --online{RESET}")
        return

    print(f"  {GREEN}Opening:{RESET} {CYAN}{path}{RESET}")
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(path)], check=True)
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as e:
        print(f"  {YELLOW}Could not auto-open. Open manually: {path}{RESET}")


# ── Walkthrough Steps ──────────────────────────────────────────────

STEPS = [
    # (puml_filename, rendered_png_name, title, narrator_notes)
    {
        "puml": "walkthrough/architecture_step0_overview.puml",
        "png": "architecture_step0_overview.png",
        "title": "FULL AMI ARCHITECTURE OVERVIEW",
        "notes": [
            "This is the complete Landis+Gyr AMI architecture as it exists",
            "at a typical electric utility today.",
            "",
            "At the bottom: your meter fleet — E350, E360, S4x/E650, E660.",
            "In the middle: the communication network and back-office systems.",
            "At the top: the REST API layer we're adding.",
            "",
            "Let's walk through each layer, starting with the field devices.",
        ],
    },
    {
        "puml": "walkthrough/architecture_step1_meters.puml",
        "png": "architecture_step1_meters.png",
        "title": "STEP 1: LANDIS+GYR METER FLEET",
        "notes": [
            f"{GREEN}HIGHLIGHTED: Smart Meters (field devices){RESET}",
            "",
            f"  {BOLD}E350{RESET}  — Residential basic.  1-phase, 120V, Form 2S.",
            "         RF Mesh or PLC communication.  ~40% of fleet.",
            "",
            f"  {BOLD}E360{RESET}  — Residential advanced.  1-phase, 120V, Form 2S.",
            "         Cellular LTE or RF Mesh.  ~30% of fleet.",
            "",
            f"  {BOLD}S4x/E650{RESET} — C&I polyphase.  3-phase, 240V, Form 9S/16S.",
            "            CT-rated.  Cellular LTE or RF Mesh.  ~20% of fleet.",
            "",
            f"  {BOLD}E660/Revelo{RESET} — C&I IoT grid-edge sensing platform.",
            "               3-phase, 240V, Form 16S.  Cellular LTE.  ~10% of fleet.",
            "",
            "Each meter collects 15-minute interval data: energy (Wh),",
            "demand (W), and voltage (V).  ~20% of residential meters",
            "also have reverse energy for solar generation.",
        ],
    },
    {
        "puml": "walkthrough/architecture_step2_comms.puml",
        "png": "architecture_step2_comms.png",
        "title": "STEP 2: COMMUNICATION PATHWAYS",
        "notes": [
            f"{GREEN}HIGHLIGHTED: Communication Network{RESET}",
            "",
            f"  {BOLD}RF Mesh{RESET}  — Gridstream 900 MHz mesh network.",
            "           Self-healing, multi-hop.  Used by E350, E360.",
            "",
            f"  {BOLD}PLC{RESET}     — Power Line Carrier.",
            "           Uses existing power lines.  Used by E350.",
            "",
            f"  {BOLD}Cellular LTE{RESET} — 4G/LTE wide-area network.",
            "                 Direct to carrier.  Used by E360, S4x, E660.",
            "",
            "All three pathways deliver interval data to the Head-End System.",
            "The choice depends on geography, density, and cost.",
            "Ref: L+G AMI Communication Pathway Selection Guide.",
        ],
    },
    {
        "puml": "walkthrough/architecture_step3_hes.puml",
        "png": "architecture_step3_hes.png",
        "title": "STEP 3: GRIDSTREAM HEAD-END SYSTEM (HES)",
        "notes": [
            f"{GREEN}HIGHLIGHTED: Gridstream HES — central data collection{RESET}",
            "",
            "The HES is the first point where all meter data converges.",
            "",
            f"  {BOLD}Data Collection{RESET}  — Collects 15-min interval readings",
            "                    from the entire fleet.  On-demand reads.",
            "                    Event and alarm processing.",
            "",
            f"  {BOLD}Meter Inventory{RESET} — Complete device registry.",
            "                    Firmware management.  Comm status tracking.",
            "",
            "At this point, the data is RAW — it has not been through",
            "validation or estimation.  Quality flags come from the meter",
            "and communication layer (valid, estimated, suspect, missing).",
            "",
            f"In the API: {CYAN}GET /meters/{'{'}id{'}'}/readings{RESET} returns this raw HES data",
            f"when {CYAN}validated_only=false{RESET} (the default).",
        ],
    },
    {
        "puml": "walkthrough/architecture_step4_mdm.puml",
        "png": "architecture_step4_mdm.png",
        "title": "STEP 4: CORE MDMS — VEE PIPELINE",
        "notes": [
            f"{GREEN}HIGHLIGHTED: Core MDMS with VEE pipeline{RESET}",
            "",
            "Raw readings from the HES flow into the MDM for processing.",
            "The VEE pipeline has three stages:",
            "",
            f"  {BOLD}1. Validation{RESET}  — Range checks (is the value physically possible?)",
            "                  Spike detection (> 5x rolling average).",
            "                  Null/missing detection.",
            "",
            f"  {BOLD}2. Estimation{RESET} — Linear interpolation for MISSING gaps.",
            "                  Uses nearest valid neighbors.",
            "                  Re-flags quality as 'estimated' with MDM-VEE source.",
            "",
            f"  {BOLD}3. Editing{RESET}    — Quality flag management.",
            "                  Sets is_validated = true.",
            "                  Produces billing-quality data.",
            "",
            f"In the API: {CYAN}GET /meters/{'{'}id{'}'}/readings?validated_only=true{RESET}",
            "routes through the MDM.  The demo shows MISSING counts",
            "dropping to zero after VEE processing.",
        ],
    },
    {
        "puml": "walkthrough/architecture_step5_analytics.puml",
        "png": "architecture_step5_analytics.png",
        "title": "STEP 5: GRIDSTREAM ANALYTICS",
        "notes": [
            f"{GREEN}HIGHLIGHTED: Gridstream Analytics platform{RESET}",
            "",
            f"  {BOLD}Demand Analysis{RESET}",
            "    Peak / Average / Minimum demand per meter.",
            "    Load factor = Average / Peak (0.0 to 1.0).",
            "    Time-of-use demand profiles.",
            "",
            f"  {BOLD}Voltage Monitoring{RESET}",
            "    ANSI C84.1 Range A compliance: ±5% of nominal.",
            "    For 120V: acceptable range is 114V to 126V.",
            "    For 240V: acceptable range is 228V to 252V.",
            "    Counts exceedance intervals per meter.",
            "",
            f"  {BOLD}Revenue Protection{RESET}",
            "    Reverse energy flow on non-solar meters → theft indicator.",
            "    Consumption anomalies (sudden >80% drops).",
            "    Tamper detection events.",
            "",
            f"In the API: {CYAN}GET /analytics/demand-summary{RESET}",
            f"            {CYAN}GET /analytics/voltage-summary{RESET}",
            f"            {CYAN}GET /analytics/revenue-protection-alerts{RESET}",
        ],
    },
    {
        "puml": "walkthrough/architecture_step6_api.puml",
        "png": "architecture_step6_api.png",
        "title": "STEP 6: CIM-COMPATIBLE REST API",
        "notes": [
            f"{GREEN}HIGHLIGHTED: REST API Layer — the integration point{RESET}",
            "",
            "This is what we're adding to your existing infrastructure.",
            "A thin, read-only REST layer with these endpoints:",
            "",
            f"  {CYAN}/meters{RESET}          — Device inventory (list, filter, get)",
            f"  {CYAN}/readings{RESET}        — Interval data (raw or VEE-validated)",
            f"  {CYAN}/usage-points{RESET}    — Service locations & customer mapping",
            f"  {CYAN}/analytics{RESET}       — Demand, voltage, revenue protection",
            "",
            "Key characteristics:",
            f"  • {BOLD}IEC 61968-9 CIM data models{RESET} — industry standard",
            f"  • {BOLD}OpenAPI 3.1{RESET} — auto-generated Swagger UI & ReDoc",
            f"  • {BOLD}X-API-Key authentication{RESET} — simple service-to-service",
            f"  • {BOLD}Pagination{RESET} — limit/offset on every list endpoint",
            f"  • {BOLD}Read-only{RESET} — does not modify operational systems",
        ],
    },
    {
        "puml": "walkthrough/architecture_step7_integration.puml",
        "png": "architecture_step7_integration.png",
        "title": "STEP 7: CLIENT INTEGRATION POINTS",
        "notes": [
            f"{GREEN}HIGHLIGHTED: Consuming applications at your utility{RESET}",
            "",
            f"  {BOLD}Billing System (CIS){RESET}",
            f"    → {CYAN}GET /readings?validated_only=true{RESET}",
            "    Pulls VEE-validated interval data for bill calculation.",
            "",
            f"  {BOLD}Grid Operations (OMS/ADMS){RESET}",
            f"    → {CYAN}GET /analytics/voltage-summary{RESET}",
            "    Real-time voltage quality monitoring and C84.1 compliance.",
            "",
            f"  {BOLD}Customer Portal{RESET}",
            f"    → {CYAN}GET /usage-points{RESET} + {CYAN}GET /readings{RESET}",
            "    Customer-facing usage history and service details.",
            "",
            f"  {BOLD}DERMS / DER Management{RESET}",
            f"    → {CYAN}GET /analytics/demand-summary{RESET}",
            "    Load profiles and capacity planning for DER integration.",
            "",
            "All clients connect with a simple HTTP GET + API key.",
            "Use the OpenAPI spec at /openapi.json to auto-generate",
            "client libraries in any language.",
        ],
    },
    {
        "puml": "walkthrough/component_step1_simulator.puml",
        "png": "component_step1_simulator.png",
        "title": "SOFTWARE: SIMULATOR LAYER",
        "notes": [
            f"{GREEN}HIGHLIGHTED: Internal software component architecture{RESET}",
            "",
            "The simulator layer models the three L+G systems in Python:",
            "",
            f"  {BOLD}MeterPark{RESET}      — Generates the fleet (50 meters + UsagePoints)",
            f"  {BOLD}DataGenerator{RESET}  — Produces realistic 15-min interval data",
            "                 Duck curve for residential, weekday/weekend for C&I",
            "                 Seasonal patterns, Gaussian noise, quality injection",
            f"  {BOLD}Headend{RESET}        — Raw data collection (models Gridstream HES)",
            f"  {BOLD}MDM{RESET}            — VEE pipeline (models Core MDMS)",
            f"  {BOLD}AnalyticsEngine{RESET} — Demand, voltage, revenue protection",
            f"  {BOLD}SimulatorEngine{RESET} — Facade that wires everything together",
            "",
            "In production, you would replace the simulator with actual",
            "connections to your HES, MDM, and Analytics databases/APIs.",
            "The API layer and CIM models remain unchanged.",
        ],
    },
    {
        "puml": "walkthrough/component_step2_api.puml",
        "png": "component_step2_api.png",
        "title": "SOFTWARE: API LAYER & ROUTERS",
        "notes": [
            f"{GREEN}HIGHLIGHTED: FastAPI application structure{RESET}",
            "",
            "The API layer has 6 routers (one per resource) plus auth:",
            "",
            f"  {CYAN}/health{RESET}         — No auth.  Monitoring endpoint.",
            f"  {CYAN}/meters{RESET}         — Meter inventory.  Filter by type, status, comm.",
            f"  {CYAN}/readings{RESET}       — Interval data.  Raw or validated.",
            f"  {CYAN}/usage-points{RESET}   — Service locations.  Readings per location.",
            f"  {CYAN}/reading-types{RESET}  — CIM ReadingType catalog.",
            f"  {CYAN}/analytics{RESET}      — Demand, voltage, revenue protection.",
            "",
            "Auth middleware validates X-API-Key on every request",
            "(except /health).  401 if missing or wrong.",
            "",
            "The FastAPI lifespan initializes the SimulatorEngine once",
            "on startup, then all routers query it via app.state.",
        ],
    },
    {
        "puml": "../sequence_get_readings.puml",
        "png": "sequence_get_readings.png",
        "title": "SEQUENCE: GET METER READINGS",
        "notes": [
            "This shows the full request lifecycle for the primary use case:",
            "retrieving VEE-validated meter readings.",
            "",
            f"  1. Client sends {CYAN}GET /meters/{'{'}id{'}'}/readings?validated_only=true{RESET}",
            "  2. API Router validates X-API-Key via Auth middleware",
            "  3. Router calls SimulatorEngine.get_meter_readings()",
            "  4. Since validated_only=true, engine routes to MDM",
            "  5. MDM pulls raw readings from HES",
            "  6. MDM runs VEE: Validate → Estimate → Edit",
            "  7. Validated MeterReading[] returns through the chain",
            "  8. Client receives PaginatedResponse<MeterReading> with 200 OK",
            "",
            "If validated_only=false (default), steps 4-6 are skipped",
            "and the HES returns raw data directly.",
        ],
    },
    {
        "puml": "../sequence_startup.puml",
        "png": "sequence_startup.png",
        "title": "SEQUENCE: APPLICATION STARTUP",
        "notes": [
            "This shows what happens when you run `python main.py`:",
            "",
            "  1. uvicorn starts → FastAPI lifespan event fires",
            "  2. SimulatorEngine is created with config (50 meters, 30 days)",
            "  3. MeterPark generates the fleet:",
            "     40% E350, 30% E360, 20% S4x, 10% E660",
            "     Each with UsagePoint, CommModule, address",
            "  4. DataGenerator is created",
            "  5. Headend.initialize() generates data for every meter:",
            "     For each meter → generate load curves (duck/weekday)",
            "     → inject quality (2% estimated, 0.5% suspect, 0.2% missing)",
            "  6. Simulator stored on app.state → ready to serve",
            "",
            f"  For 50 meters × 30 days × 96 intervals/day = {BOLD}~144,000 readings{RESET}",
            "  per reading type.  Startup takes a few seconds.",
        ],
    },
]


def show_step(step_num: int) -> None:
    """Display a single walkthrough step with diagram and narrator notes."""
    step = STEPS[step_num]

    # Header
    print()
    print(f"  {BOLD}{WHITE}{'=' * 74}{RESET}")
    print(f"  {BOLD}{WHITE}  [{step_num + 1}/{len(STEPS)}]  {step['title']}{RESET}")
    print(f"  {BOLD}{WHITE}{'=' * 74}{RESET}")
    print()

    # Open the rendered image
    png_path = RENDERED_DIR / step["png"]
    puml_path = WALKTHROUGH_DIR / step["puml"]
    if not puml_path.exists():
        puml_path = DIAGRAMS_DIR / step["puml"].replace("../", "")

    if png_path.exists():
        open_image(png_path)
    else:
        print(f"  {YELLOW}PNG not rendered.  Open the source directly:{RESET}")
        print(f"  {CYAN}{puml_path}{RESET}")
        print(f"  {DIM}(Run 'python demo/render_diagrams.py --online' to generate PNGs){RESET}")
    print()

    # Narrator notes
    hr()
    print(f"  {BOLD}NARRATOR NOTES:{RESET}")
    hr()
    print()
    for line in step["notes"]:
        print(f"  {line}")
    print()


def run_walkthrough(start: int = 0) -> None:
    """Run the interactive walkthrough from the given step."""
    print()
    print(f"  {BOLD}{WHITE}{'=' * 74}{RESET}")
    print(f"  {BOLD}{WHITE}  METER API FOR HEADEND — ARCHITECTURE WALKTHROUGH{RESET}")
    print(f"  {BOLD}{WHITE}  {len(STEPS)} steps · Progressive component highlighting{RESET}")
    print(f"  {BOLD}{WHITE}{'=' * 74}{RESET}")
    print()
    print(f"  {DIM}Each step opens a diagram and displays narrator talking points.{RESET}")
    print(f"  {DIM}Press Enter to advance.  Type 'q' to quit.  Type a number to jump.{RESET}")
    print()

    i = start
    while i < len(STEPS):
        show_step(i)

        if i < len(STEPS) - 1:
            prompt = f"  {DIM}[Enter=next | q=quit | 1-{len(STEPS)}=jump]{RESET} "
            try:
                choice = input(prompt).strip().lower()
            except EOFError:
                break

            if choice == "q":
                break
            elif choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(STEPS):
                    i = num - 1
                    continue
            i += 1
        else:
            print(f"  {BOLD}{GREEN}Walkthrough complete!{RESET}")
            print()
            break


def main() -> None:
    args = sys.argv[1:]

    if "--render" in args:
        # Render first, then walkthrough
        import demo.render_diagrams as renderer
        renderer.render_all("online")
        run_walkthrough()
    elif args and args[0].isdigit():
        step = int(args[0]) - 1
        if 0 <= step < len(STEPS):
            show_step(step)
        else:
            print(f"  {RED}Invalid step. Use 1-{len(STEPS)}.{RESET}")
    else:
        run_walkthrough()


if __name__ == "__main__":
    main()
