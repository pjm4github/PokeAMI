"""CNI (Critical Network Infrastructure) client demo.

Simulates an application running on the utility's Critical Network
Infrastructure that makes periodic API requests using a known set
of meter mRIDs.  Displays a live dashboard with readings, voltage
compliance, and demand statistics.

This is used during the training video to show a realistic integration
client polling the Meter API on a schedule.

Usage:
    # Start the API server first
    python main.py

    # Then in another terminal
    python demo/cni_demo.py                    # default: 10-second poll cycle
    python demo/cni_demo.py --interval 5       # 5-second poll cycle
    python demo/cni_demo.py --meters 10        # monitor 10 meters
    python demo/cni_demo.py --cycles 3         # stop after 3 poll cycles
"""

import io
import json
import sys
import time
from datetime import datetime, timezone

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import httpx

# ── Config ──────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
API_KEY = "dev-api-key-change-me"
HEADERS = {"X-API-Key": API_KEY}

DEFAULT_POLL_INTERVAL = 10   # seconds between polls
DEFAULT_METER_COUNT = 8      # meters to monitor
DEFAULT_CYCLES = 0           # 0 = run until Ctrl+C

# ANSI
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[97m"
BLUE = "\033[34m"
RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J\033[H"


# ── Helpers ─────────────────────────────────────────────────────────

def get(path: str, params: dict | None = None) -> dict | list | None:
    """Make a GET request and return JSON, or None on error."""
    try:
        resp = httpx.get(f"{API}{path}", headers=HEADERS, params=params, timeout=10.0)
        if resp.status_code == 200:
            return resp.json()
        return None
    except httpx.ConnectError:
        return None


def post(path: str, body: dict) -> dict | None:
    """Make a POST request and return JSON, or None on error."""
    try:
        resp = httpx.post(
            f"{API}{path}", headers={**HEADERS, "Content-Type": "application/json"},
            json=body, timeout=10.0,
        )
        if resp.status_code in (200, 201):
            return resp.json()
        return None
    except httpx.ConnectError:
        return None


def bar(value: float, max_val: float, width: int = 20, color: str = GREEN) -> str:
    """Render a horizontal bar chart segment."""
    filled = int(value / max_val * width) if max_val > 0 else 0
    filled = min(filled, width)
    return f"{color}{'█' * filled}{DIM}{'░' * (width - filled)}{RESET}"


def voltage_status(avg_v: float, nominal: float) -> str:
    """Return colored voltage status based on ANSI C84.1 Range A."""
    low = nominal * 0.95
    high = nominal * 1.05
    if low <= avg_v <= high:
        return f"{GREEN}OK{RESET}"
    elif nominal * 0.90 <= avg_v <= nominal * 1.10:
        return f"{YELLOW}WARN{RESET}"
    else:
        return f"{RED}FAIL{RESET}"


# ── CNI Client ──────────────────────────────────────────────────────

class CNIClient:
    """Simulates a CNI application monitoring a known set of meters."""

    def __init__(self, meter_count: int = DEFAULT_METER_COUNT):
        self.meter_mrids: list[str] = []
        self.meter_info: dict[str, dict] = {}
        self.meter_count = meter_count
        self.poll_count = 0
        self.last_poll: str = ""

    def discover_meters(self) -> bool:
        """Fetch the known meter mRIDs from the API (initial setup)."""
        data = get("/meters", params={"limit": self.meter_count})
        if not data:
            return False

        for meter in data["items"]:
            mrid = meter["mrid"]
            self.meter_mrids.append(mrid)
            self.meter_info[mrid] = {
                "serial": meter["serial_number"],
                "type": meter["meter_type"],
                "status": meter["status"],
                "comm_type": meter["comm_module"]["comm_type"],
                "signal_dbm": meter["comm_module"]["signal_strength"],
                "nominal_v": 120.0 if meter["phase_code"] == "SinglePhaseN" else 240.0,
                # Populated on each poll cycle
                "latest_energy_wh": None,
                "latest_demand_w": None,
                "latest_voltage_v": None,
                "quality": None,
                "avg_voltage": None,
                "voltage_exceedances": None,
                "peak_demand_w": None,
                "load_factor": None,
            }
        return True

    def poll_readings(self) -> None:
        """Fetch latest readings for each monitored meter."""
        for mrid in self.meter_mrids:
            info = self.meter_info[mrid]

            # Fetch forward energy readings (latest interval)
            data = get(f"/meters/{mrid}/readings", params={
                "reading_type_mrid": "rt-forward-energy-wh",
                "validated_only": "true",
                "limit": 1,
            })
            if data and data["items"]:
                reading = data["items"][0]
                intervals = reading["interval_blocks"][0]["interval_readings"]
                if intervals:
                    latest = intervals[-1]
                    info["latest_energy_wh"] = latest["value"]
                    info["quality"] = latest["quality"][0]["quality_type"]

            # Fetch demand reading
            data = get(f"/meters/{mrid}/readings", params={
                "reading_type_mrid": "rt-demand-w",
                "validated_only": "true",
                "limit": 1,
            })
            if data and data["items"]:
                intervals = data["items"][0]["interval_blocks"][0]["interval_readings"]
                if intervals:
                    info["latest_demand_w"] = intervals[-1]["value"]

            # Fetch voltage reading
            data = get(f"/meters/{mrid}/readings", params={
                "reading_type_mrid": "rt-voltage-v",
                "validated_only": "true",
                "limit": 1,
            })
            if data and data["items"]:
                intervals = data["items"][0]["interval_blocks"][0]["interval_readings"]
                if intervals:
                    info["latest_voltage_v"] = intervals[-1]["value"]

    def poll_analytics(self) -> None:
        """Fetch analytics summaries for monitored meters."""
        # Voltage summary
        vdata = get("/analytics/voltage-summary")
        if vdata:
            for vs in vdata:
                if vs["meter_mrid"] in self.meter_info:
                    info = self.meter_info[vs["meter_mrid"]]
                    info["avg_voltage"] = vs["average_voltage_v"]
                    info["voltage_exceedances"] = vs["ansi_c84_1_exceedance_count"]

        # Demand summary
        ddata = get("/analytics/demand-summary")
        if ddata:
            for ds in ddata:
                if ds["meter_mrid"] in self.meter_info:
                    info = self.meter_info[ds["meter_mrid"]]
                    info["peak_demand_w"] = ds["peak_demand_w"]
                    info["load_factor"] = ds["load_factor"]

    def poll(self) -> None:
        """Execute one full poll cycle."""
        self.poll_count += 1
        self.last_poll = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.poll_readings()
        self.poll_analytics()

    def render_dashboard(self, interval: int, max_cycles: int) -> None:
        """Render the full dashboard to the terminal."""
        print(CLEAR_SCREEN, end="")
        now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        # Header
        print(f"  {BOLD}{WHITE}╔══════════════════════════════════════════════════════════════════════════════╗{RESET}")
        print(f"  {BOLD}{WHITE}║  CNI METER MONITORING DASHBOARD           {DIM}Critical Network Infrastructure{RESET}  {BOLD}{WHITE}║{RESET}")
        print(f"  {BOLD}{WHITE}╚══════════════════════════════════════════════════════════════════════════════╝{RESET}")
        print()

        cycle_info = f"  cycle {self.poll_count}" + (f"/{max_cycles}" if max_cycles > 0 else "")
        print(f"  {DIM}API:{RESET} {CYAN}{API}{RESET}    "
              f"{DIM}Poll interval:{RESET} {interval}s    "
              f"{DIM}Meters:{RESET} {len(self.meter_mrids)}    "
              f"{DIM}Time:{RESET} {now}   {DIM}[{cycle_info}]{RESET}")
        print()

        # ── Meter Status Table ──
        print(f"  {BOLD}{BLUE}┌─ METER STATUS ──────────────────────────────────────────────────────────────┐{RESET}")
        print(f"  {BOLD}  {'Serial':<16} {'Type':<10} {'Comm':<9} {'Signal':>7}  {'Status':<12} {'Quality':<10}{RESET}")
        print(f"  {DIM}  {'─'*16} {'─'*10} {'─'*9} {'─'*7}  {'─'*12} {'─'*10}{RESET}")
        for mrid in self.meter_mrids:
            info = self.meter_info[mrid]
            st_color = GREEN if info["status"] == "active" else RED
            q = info.get("quality") or "—"
            q_color = GREEN if q == "valid" else YELLOW if q == "estimated" else DIM
            sig = info["signal_dbm"]
            sig_color = GREEN if sig > -70 else YELLOW if sig > -85 else RED
            print(f"    {info['serial']:<16} {info['type']:<10} "
                  f"{info['comm_type']:<9} "
                  f"{sig_color}{sig:>6.1f}{RESET}  "
                  f"{st_color}{info['status']:<12}{RESET} "
                  f"{q_color}{q:<10}{RESET}")
        print(f"  {BOLD}{BLUE}└─────────────────────────────────────────────────────────────────────────────┘{RESET}")
        print()

        # ── Latest Readings ──
        print(f"  {BOLD}{GREEN}┌─ LATEST READINGS (validated) ────────────────────────────────────────────────┐{RESET}")
        print(f"  {BOLD}  {'Serial':<16} {'Energy (Wh)':>12} {'Demand (W)':>11} {'Voltage (V)':>12}  {'Bar':>20}{RESET}")
        print(f"  {DIM}  {'─'*16} {'─'*12} {'─'*11} {'─'*12}  {'─'*20}{RESET}")
        for mrid in self.meter_mrids:
            info = self.meter_info[mrid]
            e = info["latest_energy_wh"]
            d = info["latest_demand_w"]
            v = info["latest_voltage_v"]
            e_str = f"{e:>12,.1f}" if e is not None else f"{'—':>12}"
            d_str = f"{d:>11,.1f}" if d is not None else f"{'—':>11}"
            v_str = f"{v:>12.1f}" if v is not None else f"{'—':>12}"
            d_bar = bar(d or 0, 5000, 20, CYAN) if d else ""
            print(f"    {info['serial']:<16} {e_str} {d_str} {v_str}  {d_bar}")
        print(f"  {BOLD}{GREEN}└──────────────────────────────────────────────────────────────────────────────┘{RESET}")
        print()

        # ── Voltage Compliance ──
        print(f"  {BOLD}{YELLOW}┌─ VOLTAGE COMPLIANCE (ANSI C84.1 Range A) ───────────────────────────────────┐{RESET}")
        print(f"  {BOLD}  {'Serial':<16} {'Nominal':>8} {'Average':>9} {'Status':>8}  {'Exceedances':>12}{RESET}")
        print(f"  {DIM}  {'─'*16} {'─'*8} {'─'*9} {'─'*8}  {'─'*12}{RESET}")
        compliant = 0
        total_exc = 0
        for mrid in self.meter_mrids:
            info = self.meter_info[mrid]
            nominal = info["nominal_v"]
            avg = info.get("avg_voltage")
            exc = info.get("voltage_exceedances")
            if avg is not None:
                status = voltage_status(avg, nominal)
                avg_str = f"{avg:>9.1f}"
            else:
                status = f"{DIM}—{RESET}"
                avg_str = f"{'—':>9}"
            if exc is not None:
                exc_color = GREEN if exc == 0 else YELLOW if exc < 10 else RED
                exc_str = f"{exc_color}{exc:>12}{RESET}"
                total_exc += exc
                if exc == 0:
                    compliant += 1
            else:
                exc_str = f"{'—':>12}"
            print(f"    {info['serial']:<16} {nominal:>7.0f}V {avg_str} {status:>16}  {exc_str}")
        print(f"  {DIM}  {'─'*70}{RESET}")
        print(f"    Fleet: {GREEN}{compliant}/{len(self.meter_mrids)}{RESET} compliant    "
              f"Total exceedances: {total_exc}")
        print(f"  {BOLD}{YELLOW}└──────────────────────────────────────────────────────────────────────────────┘{RESET}")
        print()

        # ── Demand Summary ──
        print(f"  {BOLD}{MAGENTA}┌─ DEMAND ANALYTICS ───────────────────────────────────────────────────────────┐{RESET}")
        print(f"  {BOLD}  {'Serial':<16} {'Peak (kW)':>10} {'Load Factor':>12}  {'Profile':>20}{RESET}")
        print(f"  {DIM}  {'─'*16} {'─'*10} {'─'*12}  {'─'*20}{RESET}")
        for mrid in self.meter_mrids:
            info = self.meter_info[mrid]
            peak = info.get("peak_demand_w")
            lf = info.get("load_factor")
            if peak is not None and lf is not None:
                lf_color = GREEN if lf > 0.5 else YELLOW if lf > 0.3 else RED
                peak_str = f"{peak / 1000:>10.2f}"
                lf_str = f"{lf_color}{lf:>12.4f}{RESET}"
                lf_bar = bar(lf, 1.0, 20, MAGENTA)
            else:
                peak_str = f"{'—':>10}"
                lf_str = f"{'—':>12}"
                lf_bar = ""
            print(f"    {info['serial']:<16} {peak_str} {lf_str}  {lf_bar}")
        print(f"  {BOLD}{MAGENTA}└──────────────────────────────────────────────────────────────────────────────┘{RESET}")
        print()

        print(f"  {DIM}Polling {API} every {interval}s with {len(self.meter_mrids)} known mRIDs  |  Ctrl+C to stop{RESET}")


# ── Main ────────────────────────────────────────────────────────────

def parse_args() -> tuple[int, int, int]:
    """Parse command-line arguments."""
    interval = DEFAULT_POLL_INTERVAL
    meters = DEFAULT_METER_COUNT
    cycles = DEFAULT_CYCLES
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--interval" and i + 1 < len(args):
            interval = int(args[i + 1])
            i += 2
        elif args[i] == "--meters" and i + 1 < len(args):
            meters = int(args[i + 1])
            i += 2
        elif args[i] == "--cycles" and i + 1 < len(args):
            cycles = int(args[i + 1])
            i += 2
        else:
            i += 1
    return interval, meters, cycles


def main() -> None:
    interval, meter_count, max_cycles = parse_args()

    print()
    print(f"  {BOLD}{WHITE}CNI Meter Monitoring Client{RESET}")
    print(f"  {DIM}Connecting to {API}...{RESET}")
    print()

    # Check server health
    health = get("/health")
    if not health:
        print(f"  {RED}Cannot connect to API at {API}{RESET}")
        print(f"  {DIM}Start the server first: python main.py{RESET}")
        sys.exit(1)

    print(f"  {GREEN}Connected.{RESET} Server has {BOLD}{health['meter_count']}{RESET} meters.")
    print()

    # Initialize client with known meters
    client = CNIClient(meter_count=meter_count)
    if not client.discover_meters():
        print(f"  {RED}Failed to discover meters.{RESET}")
        sys.exit(1)

    print(f"  {GREEN}Registered {len(client.meter_mrids)} meter mRIDs for monitoring:{RESET}")
    for mrid in client.meter_mrids:
        info = client.meter_info[mrid]
        print(f"    {DIM}•{RESET} {info['serial']:<16} ({info['type']}, {info['comm_type']})")
    print()
    print(f"  {DIM}Starting poll cycle (every {interval}s)...{RESET}")
    time.sleep(2)

    # ── Delivery Promise demo ──
    print(f"  {BOLD}{CYAN}── DELIVERY PROMISE DEMO ──{RESET}")
    print(f"  {DIM}Creating async on-demand read request for {len(client.meter_mrids)} meters...{RESET}")
    promise = post("/delivery-promises", {
        "meter_mrids": client.meter_mrids[:4],
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-01-31T00:00:00Z",
    })
    if promise:
        pid = promise["promise_id"]
        print(f"  {GREEN}Promise created:{RESET} {pid}")
        print(f"  {DIM}Status: {promise['status']}  |  "
              f"Estimated delivery: {promise['estimated_delivery']}{RESET}")

        # Poll the promise a few times
        for i in range(6):
            time.sleep(5)
            resolved = get(f"/delivery-promises/{pid}")
            if resolved:
                st = resolved["status"]
                collected = resolved["meters_collected"]
                failed = resolved["meters_failed"]
                total = resolved["meters_total"]
                st_color = GREEN if st == "completed" else YELLOW if st in ("inProgress", "partial") else RED if st == "failed" else DIM
                print(f"  {DIM}[poll {i+1}]{RESET} Status: {st_color}{st}{RESET}  "
                      f"collected: {collected}/{total}  failed: {failed}/{total}")

                if st in ("completed", "partial", "failed"):
                    # Show per-meter results
                    for mr in resolved["meter_results"]:
                        mrid_short = mr["meter_mrid"][:12]
                        if mr["status"] == "collected":
                            n_readings = len(mr["readings"]) if mr["readings"] else 0
                            print(f"    {GREEN}[collected]{RESET} {mrid_short}  ({n_readings} reading groups)")
                        elif mr["status"] == "failed":
                            print(f"    {RED}[failed]{RESET}    {mrid_short}  {DIM}{mr['failure_reason']}{RESET}")
                        else:
                            print(f"    {DIM}[pending]{RESET}   {mrid_short}")
                    break
        print()
    else:
        print(f"  {RED}Failed to create delivery promise (API error){RESET}")
        print()

    # Poll loop
    try:
        while True:
            client.poll()
            client.render_dashboard(interval, max_cycles)

            if max_cycles > 0 and client.poll_count >= max_cycles:
                print()
                print(f"  {GREEN}Completed {max_cycles} poll cycles.{RESET}")
                break

            # Countdown between polls
            for remaining in range(interval, 0, -1):
                print(f"\r  {DIM}Next poll in {remaining}s...{RESET}  ", end="", flush=True)
                time.sleep(1)

    except KeyboardInterrupt:
        print()
        print()
        print(f"  {YELLOW}Monitoring stopped by operator.{RESET}")
        print(f"  {DIM}Completed {client.poll_count} poll cycles.{RESET}")
        print()


if __name__ == "__main__":
    main()
