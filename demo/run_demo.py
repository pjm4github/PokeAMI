"""Interactive API demo script for training video.

Starts the server, walks through every endpoint with formatted output,
and pauses between sections for narration.

Usage:
    python demo/run_demo.py
"""

import atexit
import io
import json
import signal
import subprocess
import sys
import time

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

import httpx

# ── Config ──────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
API_KEY = "dev-api-key-change-me"
HEADERS = {"X-API-Key": API_KEY}

# ANSI
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[97m"
RESET = "\033[0m"

server_proc: subprocess.Popen | None = None


# ── Helpers ─────────────────────────────────────────────────────────

def hr() -> None:
    print(f"{DIM}{'─' * 78}{RESET}")


def section(num: str, title: str) -> None:
    print()
    print()
    hr()
    print(f"  {BOLD}{WHITE}SECTION {num}: {title}{RESET}")
    hr()
    print()


def show_request(method: str, url: str, auth: bool = True) -> None:
    """Display the curl command being executed."""
    display_url = url.replace(BASE_URL, "")
    key_part = f' -H "X-API-Key: {API_KEY}"' if auth else ""
    print(f"  {DIM}${RESET} curl{key_part} {BOLD}{method}{RESET} {CYAN}{display_url}{RESET}")
    print()


def pretty(data: dict | list, max_lines: int = 40) -> None:
    """Pretty-print JSON response, truncated for readability."""
    text = json.dumps(data, indent=2, default=str)
    lines = text.split("\n")
    for line in lines[:max_lines]:
        print(f"  {line}")
    if len(lines) > max_lines:
        print(f"  {DIM}... ({len(lines) - max_lines} more lines){RESET}")
    print()


def get(path: str, headers: dict | None = None, params: dict | None = None) -> dict | list:
    """Make a GET request and return JSON."""
    h = headers if headers is not None else HEADERS
    resp = httpx.get(f"{API}{path}", headers=h, params=params, timeout=30.0)
    return resp.json(), resp.status_code


def wait_for_enter(msg: str = "Press Enter to continue...") -> None:
    input(f"  {DIM}[{msg}]{RESET}")
    print()


def status_badge(code: int) -> str:
    if 200 <= code < 300:
        return f"{GREEN}{BOLD}{code}{RESET}"
    elif code == 401:
        return f"{RED}{BOLD}{code} UNAUTHORIZED{RESET}"
    elif code == 404:
        return f"{YELLOW}{BOLD}{code} NOT FOUND{RESET}"
    else:
        return f"{RED}{BOLD}{code}{RESET}"


# ── Server Management ──────────────────────────────────────────────

def start_server() -> None:
    global server_proc
    print(f"  {YELLOW}Starting Meter API server...{RESET}")
    print(f"  {DIM}(Generating 50 meters × 30 days of 15-min interval data){RESET}")
    print()

    server_proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for server to be ready
    for i in range(60):
        try:
            resp = httpx.get(f"{API}/health", timeout=2.0)
            if resp.status_code == 200:
                break
        except httpx.ConnectError:
            pass
        time.sleep(1)
    else:
        print(f"  {RED}Server failed to start!{RESET}")
        sys.exit(1)

    print(f"  {GREEN}{BOLD}Server is running!{RESET}")
    print(f"  Swagger UI:   {CYAN}{BOLD}{BASE_URL}/docs{RESET}")
    print(f"  ReDoc:        {CYAN}{BASE_URL}/redoc{RESET}")
    print()


def stop_server() -> None:
    global server_proc
    if server_proc:
        server_proc.terminate()
        server_proc.wait(timeout=5)
        server_proc = None


atexit.register(stop_server)
signal.signal(signal.SIGINT, lambda *_: (stop_server(), sys.exit(0)))


# ── Demo Sections ──────────────────────────────────────────────────

def demo_health() -> None:
    section("1", "HEALTH CHECK (no authentication)")

    print(f"  The {BOLD}/health{RESET} endpoint requires no API key.")
    print(f"  Use it for monitoring, load balancer checks, or uptime probes.")
    print()

    show_request("GET", f"{API}/health", auth=False)
    data, code = get("/health", headers={})
    print(f"  Response: {status_badge(code)}")
    pretty(data)

    print(f"  {GREEN}✓{RESET} Server is healthy with {BOLD}{data['meter_count']}{RESET} simulated meters")
    print()


def demo_auth() -> None:
    section("2", "AUTHENTICATION")

    # No key
    print(f"  {BOLD}Test 1:{RESET} Request without API key")
    show_request("GET", f"{API}/meters", auth=False)
    data, code = get("/meters", headers={})
    print(f"  Response: {status_badge(code)}")
    pretty(data)

    # Wrong key
    print(f"  {BOLD}Test 2:{RESET} Request with wrong API key")
    print(f'  {DIM}$ curl -H "X-API-Key: wrong-key" GET /api/v1/meters{RESET}')
    print()
    data, code = get("/meters", headers={"X-API-Key": "wrong-key"})
    print(f"  Response: {status_badge(code)}")
    pretty(data)

    # Correct key
    print(f"  {BOLD}Test 3:{RESET} Request with valid API key")
    show_request("GET", f"{API}/meters?limit=1")
    data, code = get("/meters", params={"limit": 1})
    print(f"  Response: {status_badge(code)}")
    print(f"  {GREEN}✓{RESET} Returned {data['total']} meters (showing 1)")
    print()


def demo_meters() -> None:
    section("3", "METER FLEET — LIST, FILTER, AND INSPECT")

    # List all
    show_request("GET", f"{API}/meters?limit=5")
    data, code = get("/meters", params={"limit": 5})
    print(f"  Response: {status_badge(code)}")
    print(f"  Total meters: {BOLD}{data['total']}{RESET}")
    print()
    print(f"  {'Serial':<18} {'Type':<12} {'Status':<14} {'Comm':<15} {'Signal':>8}")
    print(f"  {'─'*18} {'─'*12} {'─'*14} {'─'*15} {'─'*8}")
    for m in data["items"]:
        status_color = GREEN if m["status"] == "active" else RED
        print(f"  {m['serial_number']:<18} {m['meter_type']:<12} "
              f"{status_color}{m['status']:<14}{RESET} "
              f"{m['comm_module']['comm_type']:<15} "
              f"{m['comm_module']['signal_strength']:>6.1f} dBm")
    print()

    # Filter by type
    print(f"  {BOLD}Filter by type:{RESET} meter_type=E350")
    data_e350, _ = get("/meters", params={"meter_type": "E350"})
    print(f"  → {data_e350['total']} E350 residential meters")

    data_ci, _ = get("/meters", params={"meter_type": "S4x/E650"})
    print(f"  → {data_ci['total']} S4x/E650 C&I meters")
    print()

    # Filter by status
    print(f"  {BOLD}Filter by status:{RESET} status=commFailure")
    data_fail, _ = get("/meters", params={"status": "commFailure"})
    print(f"  → {data_fail['total']} meters with communication failures")
    print()

    # Get single meter
    meter_id = data["items"][0]["mrid"]
    print(f"  {BOLD}Get specific meter:{RESET}")
    show_request("GET", f"{API}/meters/{meter_id[:8]}...")
    detail, code = get(f"/meters/{meter_id}")
    print(f"  Response: {status_badge(code)}")
    print(f"  Serial:     {BOLD}{detail['serial_number']}{RESET}")
    print(f"  Type:       {detail['meter_type']}")
    print(f"  Firmware:   {detail['firmware_version']}")
    print(f"  Phase:      {detail['phase_code']}")
    print(f"  Rated:      {detail['rated_power_w']:,.0f} W")
    print(f"  Form:       {detail['form_number']}")
    print(f"  Comm:       {detail['comm_module']['comm_type']} "
          f"(fw {detail['comm_module']['firmware_version']})")
    print(f"  MAC:        {detail['comm_module']['mac_address']}")
    print(f"  Last comm:  {detail['comm_module']['last_communication']}")
    print()

    # 404
    print(f"  {BOLD}Error handling:{RESET} request nonexistent meter")
    show_request("GET", f"{API}/meters/does-not-exist")
    err, code = get("/meters/does-not-exist")
    print(f"  Response: {status_badge(code)}")
    pretty(err)

    return meter_id


def demo_reading_types() -> None:
    section("4", "READING TYPES — WHAT CAN WE MEASURE?")

    show_request("GET", f"{API}/reading-types")
    data, code = get("/reading-types")
    print(f"  Response: {status_badge(code)}")
    print(f"  {data['total']} reading types available:")
    print()
    print(f"  {'mRID':<24} {'Name':<28} {'Unit':>5}  {'Direction':<10} {'Kind':<10}")
    print(f"  {'─'*24} {'─'*28} {'─'*5}  {'─'*10} {'─'*10}")
    for rt in data["items"]:
        print(f"  {rt['mrid']:<24} {rt['name']:<28} {rt['unit']:>5}  "
              f"{rt['flow_direction']:<10} {rt['measurement_kind']:<10}")
    print()
    print(f"  {DIM}These follow the IEC 61968-9 ReadingType 18-attribute coded structure.{RESET}")
    print(f"  {DIM}Each reading type fully describes the measurement: what, how, and in what unit.{RESET}")
    print()


def demo_readings(meter_id: str) -> None:
    section("5", "METER READINGS — RAW vs. VALIDATED")

    # Raw readings
    print(f"  {BOLD}5a: Raw readings from HES{RESET}")
    show_request("GET", f"{API}/meters/{{id}}/readings?reading_type_mrid=rt-forward-energy-wh&limit=1")
    data, code = get(f"/meters/{meter_id}/readings",
                     params={"reading_type_mrid": "rt-forward-energy-wh", "limit": 1})
    print(f"  Response: {status_badge(code)}")
    reading = data["items"][0]
    block = reading["interval_blocks"][0]
    intervals = block["interval_readings"]
    print(f"  Reading type: {reading['reading_type_mrid']}")
    print(f"  Validated:    {RED}{reading['is_validated']}{RESET}")
    print(f"  Intervals:    {BOLD}{len(intervals)}{RESET} "
          f"({len(intervals) // 96} days × 96 intervals/day)")
    print()
    print(f"  {'Timestamp':<26} {'Value (Wh)':>12}  {'Quality':<12}")
    print(f"  {'─'*26} {'─'*12}  {'─'*12}")
    for ir in intervals[:8]:
        qt = ir["quality"][0]["quality_type"]
        qt_color = GREEN if qt == "valid" else YELLOW if qt == "estimated" else RED
        print(f"  {ir['timestamp']:<26} {ir['value']:>12.2f}  {qt_color}{qt}{RESET}")
    print(f"  {DIM}... ({len(intervals) - 8} more intervals){RESET}")
    print()

    # Count quality types
    quality_counts: dict[str, int] = {}
    for ir in intervals:
        qt = ir["quality"][0]["quality_type"]
        quality_counts[qt] = quality_counts.get(qt, 0) + 1
    print(f"  {BOLD}Quality distribution (raw):{RESET}")
    for qt, count in sorted(quality_counts.items(), key=lambda x: -x[1]):
        pct = count / len(intervals) * 100
        bar = "█" * int(pct / 2)
        qt_color = GREEN if qt == "valid" else YELLOW if qt == "estimated" else RED
        print(f"    {qt_color}{qt:<12}{RESET} {count:>5} ({pct:>5.1f}%)  {qt_color}{bar}{RESET}")
    print()

    # Validated readings
    print(f"  {BOLD}5b: VEE-validated readings from MDM{RESET}")
    show_request("GET", f"{API}/meters/{{id}}/readings?reading_type_mrid=rt-forward-energy-wh&validated_only=true&limit=1")
    vdata, code = get(f"/meters/{meter_id}/readings",
                      params={"reading_type_mrid": "rt-forward-energy-wh",
                              "validated_only": "true", "limit": 1})
    print(f"  Response: {status_badge(code)}")
    vreading = vdata["items"][0]
    vblock = vreading["interval_blocks"][0]
    vintervals = vblock["interval_readings"]
    print(f"  Validated:    {GREEN}{BOLD}{vreading['is_validated']}{RESET}")
    print()

    v_quality_counts: dict[str, int] = {}
    for ir in vintervals:
        qt = ir["quality"][0]["quality_type"]
        v_quality_counts[qt] = v_quality_counts.get(qt, 0) + 1
    print(f"  {BOLD}Quality distribution (after VEE):{RESET}")
    for qt, count in sorted(v_quality_counts.items(), key=lambda x: -x[1]):
        pct = count / len(vintervals) * 100
        bar = "█" * int(pct / 2)
        qt_color = GREEN if qt == "valid" else YELLOW if qt == "estimated" else RED
        print(f"    {qt_color}{qt:<12}{RESET} {count:>5} ({pct:>5.1f}%)  {qt_color}{bar}{RESET}")

    missing_before = quality_counts.get("missing", 0)
    missing_after = v_quality_counts.get("missing", 0)
    print()
    print(f"  {GREEN}✓{RESET} VEE pipeline: MISSING readings {RED}{missing_before}{RESET} → {GREEN}{missing_after}{RESET} "
          f"(estimated via linear interpolation)")
    print()


def demo_usage_points() -> None:
    section("6", "USAGE POINTS — SERVICE LOCATIONS")

    show_request("GET", f"{API}/usage-points?limit=5")
    data, code = get("/usage-points", params={"limit": 5})
    print(f"  Response: {status_badge(code)}")
    print(f"  Total usage points: {BOLD}{data['total']}{RESET}")
    print()
    print(f"  {'Name':<20} {'Category':<14} {'Voltage':>8}  {'Address':<28} {'State'}")
    print(f"  {'─'*20} {'─'*14} {'─'*8}  {'─'*28} {'─'*12}")
    for up in data["items"]:
        print(f"  {up['name']:<20} {up['service_category']:<14} "
              f"{up['rated_voltage_v']:>6.0f} V  "
              f"{up['service_location_address']:<28} {up['connection_state']}")
    print()

    # Get readings for usage point
    up_id = data["items"][0]["mrid"]
    print(f"  {BOLD}Get readings for usage point:{RESET}")
    show_request("GET", f"{API}/usage-points/{{id}}/meter-readings?limit=5")
    rdata, code = get(f"/usage-points/{up_id}/meter-readings", params={"limit": 5})
    print(f"  Response: {status_badge(code)}")
    print(f"  {rdata['total']} reading sets for this usage point")
    for r in rdata["items"]:
        print(f"    • {r['reading_type_mrid']} ({len(r['interval_blocks'][0]['interval_readings'])} intervals)")
    print()


def demo_interval_blocks() -> None:
    section("7", "INTERVAL BLOCKS — CROSS-METER QUERIES")

    show_request("GET", f"{API}/interval-blocks?reading_type_mrid=rt-voltage-v&limit=3")
    data, code = get("/interval-blocks",
                     params={"reading_type_mrid": "rt-voltage-v", "limit": 3})
    print(f"  Response: {status_badge(code)}")
    print(f"  Total blocks: {BOLD}{data['total']}{RESET} (one per meter for voltage)")
    print()
    for block in data["items"]:
        intervals = block["interval_readings"]
        values = [ir["value"] for ir in intervals if ir["value"] > 0]
        avg_v = sum(values) / len(values) if values else 0
        print(f"  Block {block['mrid'][:8]}...")
        print(f"    Period:   {block['time_period']['start']} → {block['time_period']['end']}")
        print(f"    Readings: {len(intervals)} intervals")
        print(f"    Avg:      {avg_v:.1f} V")
        print()


def demo_analytics() -> None:
    section("8", "ANALYTICS — DEMAND, VOLTAGE & REVENUE PROTECTION")

    # Demand
    print(f"  {BOLD}8a: Demand Summary{RESET}")
    show_request("GET", f"{API}/analytics/demand-summary")
    data, code = get("/analytics/demand-summary")
    print(f"  Response: {status_badge(code)}")
    print(f"  {len(data)} meter summaries returned")
    print()
    print(f"  {'Meter':<16} {'Peak (kW)':>10} {'Avg (kW)':>10} {'Min (kW)':>10} {'Load Factor':>12}")
    print(f"  {'─'*16} {'─'*10} {'─'*10} {'─'*10} {'─'*12}")
    for s in data[:8]:
        meter_short = s["meter_mrid"][:14] + ".."
        lf_color = GREEN if s["load_factor"] > 0.5 else YELLOW if s["load_factor"] > 0.3 else RED
        print(f"  {meter_short:<16} {s['peak_demand_w']/1000:>10.1f} "
              f"{s['average_demand_w']/1000:>10.1f} "
              f"{s['min_demand_w']/1000:>10.1f} "
              f"{lf_color}{s['load_factor']:>12.4f}{RESET}")
    if len(data) > 8:
        print(f"  {DIM}... ({len(data) - 8} more meters){RESET}")
    print()

    # Voltage
    print(f"  {BOLD}8b: Voltage Summary (ANSI C84.1 Compliance){RESET}")
    print(f"  {DIM}Range A for 120V: 114V–126V (±5%){RESET}")
    print(f"  {DIM}Range A for 240V: 228V–252V (±5%){RESET}")
    print()
    show_request("GET", f"{API}/analytics/voltage-summary")
    vdata, code = get("/analytics/voltage-summary")
    print(f"  Response: {status_badge(code)}")
    print()
    print(f"  {'Meter':<16} {'Avg (V)':>8} {'Min (V)':>8} {'Max (V)':>8} {'StdDev':>8} {'Exceedances':>12}")
    print(f"  {'─'*16} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*12}")
    for s in vdata[:8]:
        meter_short = s["meter_mrid"][:14] + ".."
        exc = s["ansi_c84_1_exceedance_count"]
        exc_color = GREEN if exc == 0 else YELLOW if exc < 10 else RED
        print(f"  {meter_short:<16} {s['average_voltage_v']:>8.1f} "
              f"{s['min_voltage_v']:>8.1f} {s['max_voltage_v']:>8.1f} "
              f"{s['std_dev_voltage_v']:>8.3f} "
              f"{exc_color}{exc:>12}{RESET}")
    if len(vdata) > 8:
        print(f"  {DIM}... ({len(vdata) - 8} more meters){RESET}")
    print()

    total_exceedances = sum(s["ansi_c84_1_exceedance_count"] for s in vdata)
    compliant = sum(1 for s in vdata if s["ansi_c84_1_exceedance_count"] == 0)
    print(f"  {BOLD}ANSI C84.1 Fleet Summary:{RESET}")
    print(f"    Meters in compliance: {GREEN}{compliant}/{len(vdata)}{RESET}")
    print(f"    Total exceedances:    {total_exceedances}")
    print()

    # Revenue protection
    print(f"  {BOLD}8c: Revenue Protection Alerts{RESET}")
    show_request("GET", f"{API}/analytics/revenue-protection-alerts")
    alerts, code = get("/analytics/revenue-protection-alerts")
    print(f"  Response: {status_badge(code)}")
    if alerts:
        print(f"  {RED}{BOLD}{len(alerts)} alerts found:{RESET}")
        for a in alerts[:5]:
            sev_color = RED if a["severity"] in ("high", "critical") else YELLOW
            print(f"    {sev_color}[{a['severity'].upper()}]{RESET} {a['alert_type']}: "
                  f"{a['description'][:60]}")
    else:
        print(f"  {GREEN}No alerts — fleet is operating normally{RESET}")
    print()


def demo_swagger() -> None:
    section("9", "INTERACTIVE DOCUMENTATION")

    print(f"  The API auto-generates interactive documentation:")
    print()
    print(f"    {CYAN}{BOLD}{BASE_URL}/docs{RESET}    ← Swagger UI (try endpoints live)")
    print(f"    {CYAN}{BASE_URL}/redoc{RESET}   ← ReDoc (clean reference docs)")
    print(f"    {CYAN}{BASE_URL}/openapi.json{RESET} ← OpenAPI 3.1 spec (for code generation)")
    print()
    print(f"  {BOLD}Swagger UI features:{RESET}")
    print(f"    • Try any endpoint directly in the browser")
    print(f"    • Click 'Authorize' and enter the API key")
    print(f"    • Full request/response schemas with examples")
    print(f"    • Download the OpenAPI spec for client generation")
    print()
    print(f"  {BOLD}Generating client libraries:{RESET}")
    print(f"    Use the OpenAPI spec with any code generator:")
    print(f"    • openapi-generator for Java, C#, Go, TypeScript...")
    print(f"    • Postman import for API testing")
    print(f"    • Azure API Management import")
    print()


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    print()
    print(f"  {BOLD}{WHITE}{'=' * 58}{RESET}")
    print(f"  {BOLD}{WHITE}   METER API FOR HEADEND — INTERACTIVE DEMO{RESET}")
    print(f"  {BOLD}{WHITE}   CIM-Compatible REST API for Landis+Gyr AMI{RESET}")
    print(f"  {BOLD}{WHITE}{'=' * 58}{RESET}")
    print()

    start_server()
    wait_for_enter("Server ready. Press Enter to begin demo...")

    demo_health()
    wait_for_enter()

    demo_auth()
    wait_for_enter()

    meter_id = demo_meters()
    wait_for_enter()

    demo_reading_types()
    wait_for_enter()

    demo_readings(meter_id)
    wait_for_enter()

    demo_usage_points()
    wait_for_enter()

    demo_interval_blocks()
    wait_for_enter()

    demo_analytics()
    wait_for_enter()

    demo_swagger()

    print()
    hr()
    print(f"  {BOLD}{WHITE}DEMO COMPLETE{RESET}")
    hr()
    print()
    print(f"  The server is still running at {CYAN}{BASE_URL}{RESET}")
    print(f"  Open {CYAN}{BOLD}{BASE_URL}/docs{RESET} in your browser to explore interactively.")
    print()
    print(f"  {BOLD}Resources:{RESET}")
    print(f"    README.md        — Full documentation")
    print(f"    BIBLIOGRAPHY.md  — Standards references")
    print(f"    docs/diagrams/   — PlantUML architecture diagrams")
    print(f"    tests/           — Automated test suite (pytest tests/ -v)")
    print()

    wait_for_enter("Press Enter to stop the server and exit...")
    stop_server()
    print(f"  {GREEN}Server stopped. Goodbye!{RESET}")
    print()


if __name__ == "__main__":
    main()
