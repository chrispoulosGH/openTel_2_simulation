# OpenTelemetry Microservice Simulator

This workspace contains a Python microservice simulator that generates distributed traces for OpenTelemetry and Grafana Tempo.

The current implementation is scenario-driven:

- `ABPT` is the only entry service.
- Each request selects one predefined route via `chain_id`.
- `chain_id` and `E2EUX` are propagated through OpenTelemetry baggage.
- Both values are copied onto spans so they are queryable in Grafana Tempo.
- `run_all.py` starts all services and executes repeated scenario runs.

## Current Services

There are 15 services in the current simulator:

| Service | Port | Endpoint | Port Override Env Var |
|---|---:|---|---|
| T.Data | 8001 | `/a` | `SERVICE_A_PORT` |
| IDP-IDM | 8002 | `/b` | `SERVICE_B_PORT` |
| (FED) - TDICE | 8003 | `/c` | `SERVICE_C_PORT` |
| ABPT | 8004 | `/d` | `SERVICE_D_PORT` |
| Amp-MM - Invenio | 8015 | `/e` | `SERVICE_E_PORT` |
| ECO Suite | 8006 | `/f` | `SERVICE_F_PORT` |
| GRP-ICAP | 8007 | `/g` | `SERVICE_G_PORT` |
| IDP-Commerce-ES | 8008 | `/h` | `SERVICE_H_PORT` |
| IDP-Order Graph Cloud | 8009 | `/i` | `SERVICE_I_PORT` |
| IDP_Platform | 8010 | `/j` | `SERVICE_J_PORT` |
| SHM | 8011 | `/shm` | `SHM_PORT` |
| TDICE | 8012 | `/tdice` | `TDICE_PORT` |
| TRiP | 8013 | `/trip` | `TRIP_PORT` |
| ISBUS | 8014 | `/isbus` | `ISBUS_PORT` |
| Nimbus | 8016 | `/nimbus` | `NIMBUS_PORT` |

## Call Chain

The simulator does not use one static tree anymore. The effective call chain depends on the selected scenario.

Entry point:

```text
ABPT (/d)
```

Configured scenario routes:

```text
chain_01 (length 7): ABPT -> T.Data -> IDP-IDM -> (FED) - TDICE -> Amp-MM - Invenio -> ECO Suite -> TDICE
chain_02 (length 7): ABPT -> GRP-ICAP -> IDP-Commerce-ES -> IDP-Order Graph Cloud -> SHM -> TRiP -> TDICE
chain_03 (length 7): ABPT -> Nimbus -> ISBUS -> IDP_Platform -> IDP-IDM -> ECO Suite -> TDICE
chain_04 (length 8): ABPT -> T.Data -> GRP-ICAP -> Amp-MM - Invenio -> IDP-Commerce-ES -> SHM -> TRiP -> TDICE
chain_05 (length 8): ABPT -> (FED) - TDICE -> IDP_Platform -> Nimbus -> ISBUS -> IDP-Order Graph Cloud -> ECO Suite -> TDICE
chain_06 (length 8): ABPT -> IDP-IDM -> SHM -> IDP-Commerce-ES -> TRiP -> GRP-ICAP -> Nimbus -> TDICE
chain_07 (length 9): ABPT -> ECO Suite -> Amp-MM - Invenio -> IDP-Order Graph Cloud -> T.Data -> ISBUS -> IDP_Platform -> GRP-ICAP -> TDICE
chain_08 (length 9): ABPT -> Nimbus -> IDP-Commerce-ES -> (FED) - TDICE -> SHM -> IDP-IDM -> TRiP -> Amp-MM - Invenio -> TDICE
chain_09 (length 9): ABPT -> ISBUS -> IDP_Platform -> ECO Suite -> T.Data -> GRP-ICAP -> IDP-Order Graph Cloud -> Nimbus -> TDICE
chain_10 (branched): ABPT -> T.Data -> [branch_1: IDP-IDM -> Amp-MM - Invenio] + [branch_2: GRP-ICAP] -> IDP-Commerce-ES -> SHM -> IDP-Order Graph Cloud -> TRiP -> Nimbus -> TDICE
chain_11 (length 10): ABPT -> (FED) - TDICE -> ECO Suite -> Nimbus -> ISBUS -> IDP_Platform -> T.Data -> IDP-IDM -> GRP-ICAP -> TDICE
chain_12 (length 10): ABPT -> IDP-Order Graph Cloud -> SHM -> Amp-MM - Invenio -> TRiP -> IDP-Commerce-ES -> Nimbus -> ECO Suite -> IDP_Platform -> TDICE
chain_13 (length 11): ABPT -> GRP-ICAP -> T.Data -> IDP-Commerce-ES -> Nimbus -> Amp-MM - Invenio -> ISBUS -> IDP-IDM -> ECO Suite -> IDP-Order Graph Cloud -> TDICE
chain_14 (length 11): ABPT -> SHM -> IDP_Platform -> (FED) - TDICE -> TRiP -> IDP-IDM -> GRP-ICAP -> Amp-MM - Invenio -> Nimbus -> ECO Suite -> TDICE
chain_15 (length 11): ABPT -> Nimbus -> ISBUS -> Amp-MM - Invenio -> ECO Suite -> T.Data -> IDP-Order Graph Cloud -> IDP-Commerce-ES -> SHM -> GRP-ICAP -> TDICE
chain_16 (length 12): ABPT -> T.Data -> GRP-ICAP -> IDP-IDM -> Amp-MM - Invenio -> IDP-Commerce-ES -> SHM -> IDP-Order Graph Cloud -> ECO Suite -> TRiP -> Nimbus -> TDICE
chain_17 (length 12): ABPT -> (FED) - TDICE -> IDP_Platform -> ISBUS -> IDP-Commerce-ES -> T.Data -> Nimbus -> IDP-IDM -> GRP-ICAP -> TRiP -> ECO Suite -> TDICE
chain_18 (length 12): ABPT -> IDP-Order Graph Cloud -> SHM -> Amp-MM - Invenio -> Nimbus -> IDP-IDM -> ECO Suite -> TRiP -> IDP_Platform -> GRP-ICAP -> ISBUS -> TDICE
chain_19 (length 12): ABPT -> IDP-Commerce-ES -> T.Data -> GRP-ICAP -> IDP-Order Graph Cloud -> Amp-MM - Invenio -> SHM -> Nimbus -> TRiP -> ECO Suite -> IDP-IDM -> TDICE
chain_20 (fork-join): ABPT -> [branch_1: Nimbus -> ECO Suite -> IDP_Platform -> T.Data] + [branch_2: IDP-Commerce-ES -> Amp-MM - Invenio -> ISBUS -> TRiP -> GRP-ICAP -> IDP-IDM] -> TDICE
```

`chain_19` is the designated longest linear scenario.

## Scenario Model

Accepted `chain_id` values:

- `chain_01` through `chain_20`

Scenario definitions (all chains start with ABPT and end with TDICE; `chain_20` is fork-join):

| `chain_id` | Length | Route |
|---|---:|---|
| `chain_01` | 7 | ABPT -> T.Data -> IDP-IDM -> (FED) - TDICE -> Amp-MM - Invenio -> ECO Suite -> TDICE |
| `chain_02` | 7 | ABPT -> GRP-ICAP -> IDP-Commerce-ES -> IDP-Order Graph Cloud -> SHM -> TRiP -> TDICE |
| `chain_03` | 7 | ABPT -> Nimbus -> ISBUS -> IDP_Platform -> IDP-IDM -> ECO Suite -> TDICE |
| `chain_04` | 8 | ABPT -> T.Data -> GRP-ICAP -> Amp-MM - Invenio -> IDP-Commerce-ES -> SHM -> TRiP -> TDICE |
| `chain_05` | 8 | ABPT -> (FED) - TDICE -> IDP_Platform -> Nimbus -> ISBUS -> IDP-Order Graph Cloud -> ECO Suite -> TDICE |
| `chain_06` | 8 | ABPT -> IDP-IDM -> SHM -> IDP-Commerce-ES -> TRiP -> GRP-ICAP -> Nimbus -> TDICE |
| `chain_07` | 9 | ABPT -> ECO Suite -> Amp-MM - Invenio -> IDP-Order Graph Cloud -> T.Data -> ISBUS -> IDP_Platform -> GRP-ICAP -> TDICE |
| `chain_08` | 9 | ABPT -> Nimbus -> IDP-Commerce-ES -> (FED) - TDICE -> SHM -> IDP-IDM -> TRiP -> Amp-MM - Invenio -> TDICE |
| `chain_09` | 9 | ABPT -> ISBUS -> IDP_Platform -> ECO Suite -> T.Data -> GRP-ICAP -> IDP-Order Graph Cloud -> Nimbus -> TDICE |
| `chain_10` | branched | ABPT -> T.Data -> [branch_1: IDP-IDM -> Amp-MM - Invenio] + [branch_2: GRP-ICAP] -> IDP-Commerce-ES -> SHM -> IDP-Order Graph Cloud -> TRiP -> Nimbus -> TDICE |
| `chain_11` | 10 | ABPT -> (FED) - TDICE -> ECO Suite -> Nimbus -> ISBUS -> IDP_Platform -> T.Data -> IDP-IDM -> GRP-ICAP -> TDICE |
| `chain_12` | 10 | ABPT -> IDP-Order Graph Cloud -> SHM -> Amp-MM - Invenio -> TRiP -> IDP-Commerce-ES -> Nimbus -> ECO Suite -> IDP_Platform -> TDICE |
| `chain_13` | 11 | ABPT -> GRP-ICAP -> T.Data -> IDP-Commerce-ES -> Nimbus -> Amp-MM - Invenio -> ISBUS -> IDP-IDM -> ECO Suite -> IDP-Order Graph Cloud -> TDICE |
| `chain_14` | 11 | ABPT -> SHM -> IDP_Platform -> (FED) - TDICE -> TRiP -> IDP-IDM -> GRP-ICAP -> Amp-MM - Invenio -> Nimbus -> ECO Suite -> TDICE |
| `chain_15` | 11 | ABPT -> Nimbus -> ISBUS -> Amp-MM - Invenio -> ECO Suite -> T.Data -> IDP-Order Graph Cloud -> IDP-Commerce-ES -> SHM -> GRP-ICAP -> TDICE |
| `chain_16` | 12 | ABPT -> T.Data -> GRP-ICAP -> IDP-IDM -> Amp-MM - Invenio -> IDP-Commerce-ES -> SHM -> IDP-Order Graph Cloud -> ECO Suite -> TRiP -> Nimbus -> TDICE |
| `chain_17` | 12 | ABPT -> (FED) - TDICE -> IDP_Platform -> ISBUS -> IDP-Commerce-ES -> T.Data -> Nimbus -> IDP-IDM -> GRP-ICAP -> TRiP -> ECO Suite -> TDICE |
| `chain_18` | 12 | ABPT -> IDP-Order Graph Cloud -> SHM -> Amp-MM - Invenio -> Nimbus -> IDP-IDM -> ECO Suite -> TRiP -> IDP_Platform -> GRP-ICAP -> ISBUS -> TDICE |
| `chain_19` | 12 | ABPT -> IDP-Commerce-ES -> T.Data -> GRP-ICAP -> IDP-Order Graph Cloud -> Amp-MM - Invenio -> SHM -> Nimbus -> TRiP -> ECO Suite -> IDP-IDM -> TDICE |
| `chain_20` | fork-join | ABPT -> [branch_1: Nimbus -> ECO Suite -> IDP_Platform -> T.Data] + [branch_2: IDP-Commerce-ES -> Amp-MM - Invenio -> ISBUS -> TRiP -> GRP-ICAP -> IDP-IDM] -> TDICE |

## Propagated Context

Two important values are propagated through the request path:

- `chain_id`
    - selects the scenario route
    - is stored in baggage
    - is copied onto spans for Tempo queries
- `E2EUX`
    - identifies the business context for the trace
    - is stored in baggage
    - is copied onto spans for Tempo queries

`trace_id` is different from both of these. It is generated by OpenTelemetry for each request execution and is not the same thing as `chain_id`.

## Prerequisites

- Python 3.10+
- An OpenTelemetry collector listening on gRPC port 4317
    - for example Grafana Alloy, OpenTelemetry Collector, or Tempo with OTLP receiver enabled

## Install Dependencies

```powershell
pip install -r requirements.txt
```

## Start The Simulator

```powershell
python run_all.py
```

What `run_all.py` does:

1. Kills any existing listeners on the configured service ports.
2. Starts all simulator services as subprocesses.
3. Prints the configured scenarios.
4. Executes `RUN_COUNT` scenario runs through `ABPT`.
5. Prints per-run status and a final completed/failed summary.

By default it also clears and repopulates a local trace export folder at `local_traces\spans`, so you can analyze runs without exporting traces from Tempo.

Stop the simulator with `Ctrl+C` in the terminal where `run_all.py` is running.

## Manual Invocation

You can also trigger the entry service yourself after the services are running.

Examples:

```powershell
curl "http://localhost:8004/d?chain_id=chain_01"
curl "http://localhost:8004/d?chain_id=chain_10"
curl "http://localhost:8004/d?chain_id=chain_20"
```

Each request produces one distributed trace for the selected scenario.

## Additional Endpoints

Each service also exposes:

- `GET /health`
    - returns a simple status payload
- `GET /info`
    - returns service name, port, and all possible downstream URLs for that service across configured scenarios

## Configuration

Set environment variables before running to override defaults:

| Variable | Default | Description |
|---|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `localhost:4317` | OTLP gRPC collector endpoint |
| `E2EUX` | `Troubleshoot Broadband (Care)` | Business context attached at the ABPT entry point |
| `RUN_COUNT` | `20` | Total number of scenario executions performed by `run_all.py` |
| `GRP_ICAP_TIMEOUT_RATE` | `0.0` | Probability that GRP-ICAP simulates a timeout |
| `GRP_ICAP_TIMEOUT_SECONDS` | `6.0` | Sleep duration used by GRP-ICAP to exceed the caller timeout |
| `ENABLE_LOCAL_TRACE_EXPORT` | `1` | Write local JSONL span exports alongside OTLP export |
| `LOCAL_TRACE_EXPORT_DIR` | `local_traces` | Folder used for local trace exports |
| `RESET_LOCAL_TRACE_EXPORTS` | `1` | Clear previous local trace exports when `run_all.py` starts |
| `SERVICE_A_PORT` | `8001` | Override T.Data port |
| `SERVICE_B_PORT` | `8002` | Override IDP-IDM port |
| `SERVICE_C_PORT` | `8003` | Override (FED) - TDICE port |
| `SERVICE_D_PORT` | `8004` | Override ABPT port |
| `SERVICE_E_PORT` | `8015` | Override Amp-MM - Invenio port |
| `SERVICE_F_PORT` | `8006` | Override ECO Suite port |
| `SERVICE_G_PORT` | `8007` | Override GRP-ICAP port |
| `SERVICE_H_PORT` | `8008` | Override IDP-Commerce-ES port |
| `SERVICE_I_PORT` | `8009` | Override IDP-Order Graph Cloud port |
| `SERVICE_J_PORT` | `8010` | Override IDP_Platform port |
| `SHM_PORT` | `8011` | Override SHM port |
| `TDICE_PORT` | `8012` | Override TDICE port |
| `TRIP_PORT` | `8013` | Override TRiP port |
| `ISBUS_PORT` | `8014` | Override ISBUS port |
| `NIMBUS_PORT` | `8016` | Override Nimbus port |

Example:

```powershell
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "my-collector:4317"
$env:E2EUX = "Troubleshoot Broadband (Care)"
$env:RUN_COUNT = "20"
python run_all.py
```

## Logging

Runtime logging is intentionally minimal.

Each service emits one concise line when it is invoked, including:

- service name
- `trace_id`
- HTTP method and path
- `E2EUX`
- source of the propagated value

Logs are written to `services.log` and also printed to stderr.

Example:

```text
2026-03-25 12:10:15,123 [otel-sim] INFO: service=ABPT trace_id=4a5f2c8f9f864f8d9f07dc4d8d8ff123 method=GET path=/d E2EUX=Troubleshoot Broadband (Care) source=baggage
2026-03-25 12:10:15,245 [otel-sim] INFO: service=IDP-IDM trace_id=4a5f2c8f9f864f8d9f07dc4d8d8ff123 method=GET path=/b E2EUX=Troubleshoot Broadband (Care) source=baggage
```

## Grafana Tempo

Both `E2EUX` and `chain_id` are available in Tempo because they are copied from baggage onto spans.

Typical Tempo / TraceQL examples:

```text
{ span.E2EUX = "Troubleshoot Broadband (Care)" }
```

```text
{ span.chain_id = "ts_scernario_05" }
```

```text
{ span.E2EUX = "Troubleshoot Broadband (Care)" && span.chain_id = "ts_scernario_10" }
```

Filter by service:

```text
{ resource.service.name = "GRP-ICAP" }
```

Filter by service and scenario:

```text
{ resource.service.name = "GRP-ICAP" && span.chain_id = "ts_scernario_05" }
```

Find failed scenario runs at the entry service:

```text
{ resource.service.name = "ABPT" && span.chain_id != "" && status = error }
```

Find failed runs for one specific scenario:

```text
{ resource.service.name = "ABPT" && span.chain_id = "ts_scernario_05" && status = error }
```

## Failure Simulation

`GRP-ICAP` is configured to simulate a timeout 50% of the time by default.

Mechanism:

- the service sleeps for 6 seconds
- downstream callers use a 5 second HTTP timeout
- affected calls raise an error
- downstream errors are propagated instead of being converted into a successful JSON payload

Result:

- scenarios containing `GRP-ICAP` can fail to complete
- scenarios without `GRP-ICAP` are unaffected by that simulation path

## PM4PY Export

There are now two input paths for PM4PY-ready export.

From a Tempo-exported trace JSON:

```powershell
python export_pm4py_csv.py "C:\Users\cp1853\Downloads\Trace-246165-2026-03-25 15_03_21.json.json" pm4py_trace.csv
```

From the simulator's local trace export folder, without any Tempo export step:

```powershell
python export_pm4py_csv.py local_traces pm4py_trace.csv
```

By default, the script keeps only `process-request` spans so each service step becomes one PM4PY event row.

Output columns:

- `case:concept:name` = trace ID
- `concept:name` = `service.name:span.name`
- `time:timestamp` = span start time in UTC
- `E2EUX` = span attribute copied from baggage
- `chain_id` = propagated scenario identifier
- `service.name` = service that emitted the span
- `status` = `UNSET`, `OK`, or `ERROR`
- `status_code` = raw OpenTelemetry status code

To export all spans instead of only `process-request` spans:

```powershell
python export_pm4py_csv.py trace.json pm4py_trace.csv --all-spans
```

If you want a local scenario completion summary from that CSV without querying Tempo again, run:

```powershell
python analyze_pm4py_csv.py pm4py_trace.csv
```

That summary script reads the PM4PY-ready CSV directly and does not require the `pm4py` or `pandas` packages.

If you want one command that does both the JSON-to-CSV export and the PM4PY analysis, run:

```powershell
python run_pm4py_analysis.py "C:\path\to\trace.json"
```

If you want one command that uses the simulator's local exports instead of Tempo, run:

```powershell
python run_pm4py_analysis.py local_traces
```

You can also provide an explicit CSV output path:

```powershell
python run_pm4py_analysis.py "C:\path\to\trace.json" pm4py_trace.csv
```

Or with local trace exports:

```powershell
python run_pm4py_analysis.py local_traces pm4py_trace.csv
```

The analysis script uses PM4PY-compatible data and prints:

- one row per scenario with `runs`, `completed`, `failed`, and `failure_rate`
- one row per trace with `chain_id`, `E2EUX`, outcome, and timestamps
