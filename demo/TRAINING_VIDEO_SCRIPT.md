# Meter API for Headend — Training Video Script

**Duration:** ~25–30 minutes
**Audience:** Utility integration engineers, IT architects, and AMI operations staff
**Prerequisites:** Familiarity with Landis+Gyr AMI infrastructure and REST APIs

---

## Setup Before Recording

### 1. Prepare PowerPoint Slides

Convert the walkthrough `.puml` files to a PowerPoint slide deck.
Source files are in `docs/diagrams/walkthrough/` (SVGs in `docs/diagrams/rendered/`).

| Slide | Source PUML | Title |
|-------|------------|-------|
| 1 | *(title card)* | Meter API for Headend |
| 2 | `architecture_step0_overview` | Full AMI Architecture Overview |
| 3 | `architecture_step1_meters` | Step 1: Landis+Gyr Meter Fleet |
| 4 | `architecture_step2_comms` | Step 2: Communication Pathways |
| 5 | `architecture_step3_hes` | Step 3: Gridstream HES (Head-End) |
| 6 | `architecture_step4_mdm` | Step 4: Core MDMS / VEE Pipeline |
| 7 | `architecture_step5_analytics` | Step 5: Gridstream Analytics |
| 8 | `architecture_step6_api` | Step 6: CIM REST API Layer |
| 9 | `architecture_step7_integration` | Step 7: Client Integration Points |
| 10 | `component_step1_simulator` | Software: Simulator Layer |
| 11 | `component_step2_api` | Software: API Layer & Routers |
| 12 | `sequence_get_readings` | Sequence: Get Meter Readings |
| 13 | `sequence_startup` | Sequence: Application Startup |

To render SVGs for import into PowerPoint:
```bash
.venv/Scripts/python demo/render_diagrams.py --svg --online
```

### 2. Test the Demo Scripts

```bash
# Test the API demo
.venv/Scripts/python demo/run_demo.py

# Test the CNI client (start server first, then in another terminal)
.venv/Scripts/python main.py
.venv/Scripts/python demo/cni_demo.py --cycles 2
```

### 3. Scripts to Run During Recording

| Script | What it does | When to use |
|--------|-------------|-------------|
| `python demo/run_demo.py` | Starts server, exercises every API endpoint | PART 2 (Live API Demo) |
| `python demo/cni_demo.py` | CNI client polling the API with known mRIDs | Scene 1.10 (CNI Demo) |

---

## PART 1: Architecture & Integration Context (10–12 min)

> Advance through the PowerPoint slide deck as you narrate each scene.

### Scene 1.1 — Title Card

> **NARRATOR:**
> "Welcome to the Meter API for Headend training. In this video, we'll walk
> through a CIM-compatible REST API interface that sits in front of your
> Landis+Gyr AMI infrastructure — your Head-End System, your Meter Data
> Management system, and your Analytics platform. We'll show you how to
> integrate it into your existing utility architecture, demonstrate a
> Critical Network Infrastructure client polling the API, and walk through
> every endpoint."

**[SLIDE 1: Title card]**

---

### Scene 1.2 — Full Architecture Overview

**[SLIDE 2: Full AMI Architecture Overview]**

> **NARRATOR:**
> "Let's start with the big picture. This is the complete AMI architecture —
> from field devices at the bottom through communication networks, back-office
> systems, the REST API layer, and client applications at the top.
>
> We'll walk through each layer one at a time."

---

### Scene 1.3 — Meter Fleet

**[SLIDE 3: Step 1 — Meter Fleet highlighted]**

> **NARRATOR:**
> "At the foundation, you have your meter fleet — the field devices that
> collect the data.
>
> In a typical L+G deployment, that's a mix of four meter families:
>
> - **E350** — your basic residential meter. Single-phase, 120V, Form 2S.
>   Communicates over RF Mesh or PLC. About 40% of a typical fleet.
>
> - **E360** — advanced residential with LTE connectivity. Same form factor,
>   but with cellular communication for areas where RF Mesh doesn't reach.
>   About 30% of the fleet.
>
> - **S4x/E650** — your commercial and industrial polyphase meters. Three-phase,
>   240V, CT-rated. These handle demand measurement for large customers.
>   About 20% of the fleet.
>
> - **E660/Revelo** — the newest platform. IoT grid-edge sensing with advanced
>   power quality measurement. About 10% of the fleet.
>
> Each meter collects 15-minute interval data: forward energy in watt-hours,
> demand in watts, and voltage in volts. About 20% of residential meters also
> report reverse energy for customers with solar generation."

---

### Scene 1.4 — Communication Pathways

**[SLIDE 4: Step 2 — Communication Network highlighted]**

> **NARRATOR:**
> "The data gets from the meters to headquarters over three communication
> pathways.
>
> **RF Mesh** — Gridstream's 900 MHz mesh network. Self-healing, multi-hop.
> Your E350s and some E360s use this. Great for dense residential areas.
>
> **PLC** — Power Line Carrier. Uses the existing power lines themselves.
> Another option for E350s, especially where RF coverage is challenging.
>
> **Cellular LTE** — Direct 4G/LTE to carrier network. Used by E360s, S4x,
> and E660 meters. Best for wide-area or rural deployments.
>
> The choice between these depends on geography, meter density, and cost.
> Landis+Gyr's AMI Communication Pathway Selection Guide covers the
> trade-offs in detail."

---

### Scene 1.5 — Gridstream HES

**[SLIDE 5: Step 3 — HES highlighted]**

> **NARRATOR:**
> "All three communication pathways converge at the Gridstream Head-End
> System — the HES. This is your central data collection point.
>
> The HES does two things:
>
> **Data Collection** — It collects 15-minute interval readings from every
> meter in the fleet. It handles on-demand reads, processes events and alarms,
> and manages the communication schedule.
>
> **Meter Inventory** — It maintains the complete device registry. Every
> meter's serial number, firmware version, communication module, signal
> strength, and last successful communication.
>
> At this point, the data is RAW. It hasn't been through validation or
> estimation. Quality flags come from the meter and comm layer — valid,
> estimated, suspect, or missing.
>
> In the API, when you call GET /meters/{id}/readings without the
> validated_only flag, you're getting this raw HES data."

---

### Scene 1.6 — Core MDMS / VEE Pipeline

**[SLIDE 6: Step 4 — MDM/VEE highlighted]**

> **NARRATOR:**
> "Raw readings from the HES flow into the Meter Data Management system —
> Landis+Gyr calls it Core MDMS. The critical function here is the VEE
> pipeline: Validation, Estimation, and Editing.
>
> **Step 1: Validation** — Range checks ask: is this value physically
> possible? Spike detection flags readings that are more than 5 times the
> rolling average. Null detection catches missing data.
>
> **Step 2: Estimation** — For MISSING gaps, the MDM uses linear
> interpolation between the nearest valid neighbors. The quality flag
> changes from 'missing' to 'estimated' with a source of 'MDM-VEE'.
>
> **Step 3: Editing** — Quality flag management. The is_validated flag
> is set to true. At this point, you have billing-quality data.
>
> In the API, when you add validated_only=true, the request routes through
> the MDM. In the demo, you'll see MISSING readings drop to zero after
> VEE processing."

---

### Scene 1.7 — Gridstream Analytics

**[SLIDE 7: Step 5 — Analytics highlighted]**

> **NARRATOR:**
> "The analytics platform sits on top, consuming both raw and validated data.
>
> **Demand Analysis** — Peak, average, and minimum demand per meter. Load
> factor tells you how spiky the load profile is — closer to 1.0 means
> steady consumption.
>
> **Voltage Monitoring** — This is where ANSI C84.1 compliance comes in.
> Range A says voltage should stay within plus or minus 5% of nominal. For
> 120V, that's 114 to 126 volts. The analytics count how many intervals
> exceed that range.
>
> **Revenue Protection** — Flags anomalies that might indicate theft or
> meter tampering. Reverse energy flow on a meter that doesn't have solar.
> Sudden drops in consumption. Tamper detection events."

---

### Scene 1.8 — The REST API Layer

**[SLIDE 8: Step 6 — API Layer highlighted]**

> **NARRATOR:**
> "This is what we're adding. A CIM-compatible REST API that sits in front
> of all three L+G systems.
>
> Four main endpoint groups:
> - /meters for device inventory
> - /readings for interval data (raw or validated)
> - /usage-points for service locations
> - /analytics for demand, voltage, and revenue protection
>
> Key design choices: IEC 61968-9 CIM data models for industry
> compatibility. OpenAPI 3.1 with auto-generated Swagger documentation.
> Simple API key authentication. Pagination on every list endpoint.
> And critically — this is read-only. It queries your existing systems
> without modifying anything."

---

### Scene 1.9 — Client Integration

**[SLIDE 9: Step 7 — Client Integration with all actors]**

> **NARRATOR:**
> "Now let's talk about who connects to this API.
>
> Your **Billing System** pulls VEE-validated interval data with
> validated_only=true. Your **Grid Operations** team queries voltage
> analytics for ANSI C84.1 compliance. Your **Customer Portal** shows
> usage history via usage-points and readings. And your **DERMS** uses
> demand summaries for DER integration and capacity planning.
>
> All clients use the same simple pattern: HTTP GET with an API key.
> The OpenAPI spec at /openapi.json lets you auto-generate client
> libraries in Java, C#, Python, TypeScript — whatever your systems use.
>
> Let me show you what this looks like in practice. We have a monitoring
> application running on the Critical Network Infrastructure — the CNI —
> that polls this API on a schedule with a known set of meter mRIDs."

---

### Scene 1.10 — CNI Live Demo

> **Before this scene:** Start the API server in one terminal and the CNI
> client in another:
>
> ```bash
> # Terminal 1 — API server
> .venv/Scripts/python main.py
>
> # Terminal 2 — CNI monitoring client
> .venv/Scripts/python demo/cni_demo.py --interval 10 --meters 8
> ```

**[SWITCH TO TERMINAL: CNI dashboard running]**

> **NARRATOR:**
> "Here's a CNI monitoring application running in real time. It has
> a preconfigured set of 8 meter mRIDs — just like a real utility
> operations center would maintain a watch list of critical meters.
>
> Every 10 seconds, it polls the API and updates four panels:
>
> **Meter Status** — shows each meter's serial number, type, communication
> method, and signal strength. You can see the mix of E350s, E360s,
> S4x meters, and E660s, communicating over RF Mesh, PLC, and Cellular.
>
> **Latest Readings** — the most recent validated interval for each meter.
> Forward energy in watt-hours, demand in watts, and voltage. The bar
> chart shows demand relative to capacity.
>
> **Voltage Compliance** — ANSI C84.1 Range A check for every meter.
> The nominal voltage, average measured voltage, pass/fail status, and
> exceedance count. At the bottom, the fleet compliance summary.
>
> **Demand Analytics** — peak demand and load factor for each meter.
> A load factor close to 1.0 means steady usage; closer to 0 means
> peaky, intermittent loads.
>
> Notice the poll counter incrementing in the header — this client is
> using the exact same API endpoints you'll see in the live demo.
> It authenticates with the same X-API-Key header, queries validated
> readings, and pulls analytics — all over standard HTTP.
>
> This is a simple example, but in production you could feed these
> readings into your SCADA historian, your outage management system,
> or a real-time voltage monitoring dashboard on the CNI."

**[Let the dashboard cycle through 2–3 polls, then Ctrl+C to stop]**

---

### Scene 1.11 — Software Architecture

**[SLIDE 10: Simulator Layer]**
**[SLIDE 11: API Layer & Routers]**

> **NARRATOR:**
> "Under the hood, the simulator layer models the three L+G systems in
> Python. MeterPark generates the fleet, DataGenerator produces realistic
> time-series, and the Headend, MDM, and Analytics Engine simulate the
> real systems.
>
> In production, you'd replace the simulator with actual connections to
> your HES database, MDM API, and analytics platform. The API layer and
> CIM models stay exactly the same.
>
> The API layer has six routers — one per resource — plus an auth
> middleware that validates the API key on every request except /health."

---

### Scene 1.12 — Request Flow

**[SLIDE 12: Sequence — Get Meter Readings]**
**[SLIDE 13: Sequence — Application Startup]**

> **NARRATOR:**
> "Here's how a request flows through the system. A client asks for
> validated meter readings. The router validates the API key, calls the
> SimulatorEngine, which routes to the MDM. The MDM pulls raw data from
> the HES, runs VEE, and sends validated readings back.
>
> At startup, the lifespan event creates the SimulatorEngine, generates
> the fleet of 50 meters with 30 days of 15-minute data, and stores
> everything in memory. That's about 144,000 readings per reading type."

---

## PART 2: Live API Demo (10–12 min)

> Run `python demo/run_demo.py`.
> The script starts the server and walks through every endpoint.
> Press Enter to advance between sections.

### Scene 2.1 — Starting the Server

> "Let's fire up the API. The demo script starts the server and generates
> the simulated meter data."

**[demo/run_demo.py starts — shows server banner with URLs]**

---

### Scene 2.2 — Health Check (Section 1)

> "The health check at /api/v1/health needs no API key. It returns the
> system status and meter count. Use this for your monitoring and load
> balancer health probes."

---

### Scene 2.3 — Authentication (Section 2)

> "Every other endpoint requires an X-API-Key header. Without it — 401.
> Wrong key — 401. Valid key — 200. Simple and effective for
> service-to-service calls."

---

### Scene 2.4 — Meter Fleet (Section 3)

> "Here's the fleet. 50 meters with the realistic distribution we
> discussed. Notice the filtering — by type, by status, by communication
> technology. And pagination on every response."

---

### Scene 2.5 — Reading Types (Section 4)

> "The reading-types endpoint returns the CIM catalog. Four types:
> forward energy, reverse energy, demand, and voltage. Each with the
> CIM-standard coded attributes."

---

### Scene 2.6 — Meter Readings: Raw vs. Validated (Section 5)

> "This is the core use case. First, raw readings from the HES — notice
> the quality distribution. About 97% valid, 2% estimated, small amounts
> of suspect and missing.
>
> Now the same data with validated_only=true. The VEE pipeline runs and
> every MISSING reading gets estimated. That quality bar chart tells the
> whole story."

---

### Scene 2.7 — Usage Points (Section 6)

> "Usage points are your service locations. Each one has a customer
> account, service address, and associated meters. You can pull readings
> for a usage point to get all meters at that location."

---

### Scene 2.8 — Interval Blocks (Section 7)

> "Interval blocks let you query across multiple meters at once. Useful
> for bulk data extraction."

---

### Scene 2.9 — Analytics (Section 8)

> "Finally, analytics. Demand summaries with load factor. Voltage
> summaries with ANSI C84.1 exceedance counts. And revenue protection
> alerts for anomaly detection.
>
> Notice the fleet summary — how many meters are in voltage compliance,
> total exceedance count across the fleet."

---

### Scene 2.10 — Swagger UI (Section 9)

> "Switch to the browser and open localhost:8000/docs. This is the
> auto-generated Swagger UI. Click Authorize, enter the API key, and
> you can try any endpoint right here. Download the OpenAPI spec for
> client generation."

**[Switch to browser, show Swagger UI]**

---

## PART 3: Wrap-Up (2–3 min)

> **NARRATOR:**
> "Let's recap what we covered:
>
> - The existing L+G AMI architecture: meters, comms, HES, MDM, analytics
> - Where the REST API fits as a read-only integration layer
> - IEC 61968-9 CIM data models for industry compatibility
> - A CNI monitoring client polling the API with known meter mRIDs
> - Every API endpoint with real data
> - Raw vs. VEE-validated readings
> - ANSI C84.1 voltage compliance analytics
>
> To get started, clone the repo, install dependencies, and run
> python main.py. Open the Swagger UI and explore. Check BIBLIOGRAPHY.md
> for every standards reference.
>
> Thank you for watching."

**[Final title card]**
