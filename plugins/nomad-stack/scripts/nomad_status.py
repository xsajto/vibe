#!/usr/bin/env python3
"""Nomad cluster status reporter.

Connects to the Nomad HTTP API and reports server members, client nodes,
running jobs, and recent failed allocations.

Usage:
    python nomad_status.py http://localhost:4646
    python nomad_status.py http://localhost:4646 --token my-token --namespace default
    python nomad_status.py http://localhost:4646 --format json
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def api_get(base_url, path, token=None, params=None):
    """Make a GET request to the Nomad API."""
    url = base_url.rstrip("/") + path
    if params:
        query = "&".join(
            "{}={}".format(k, v) for k, v in params.items() if v is not None
        )
        if query:
            url += "?" + query

    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("X-Nomad-Token", token)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            print("Error: authentication failed (HTTP 403). Check your ACL token.", file=sys.stderr)
        elif exc.code == 401:
            print("Error: unauthorized (HTTP 401). An ACL token may be required.", file=sys.stderr)
        else:
            print("Error: HTTP {} from Nomad API: {}".format(exc.code, exc.reason), file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print("Error: could not connect to Nomad at {}: {}".format(base_url, exc.reason), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        sys.exit(1)


def print_table(title, headers, rows):
    """Print an aligned table with a title."""
    if not rows:
        print("\n=== {} ===".format(title))
        print("  (none)")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)

    print("\n=== {} ===".format(title))
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for row in rows:
        print(fmt.format(*row))


def get_server_members(base_url, token):
    """Fetch server members from /v1/agent/members."""
    data = api_get(base_url, "/v1/agent/members", token=token)
    members = data.get("Members", [])
    rows = []
    # Determine leader
    leader_info = None
    try:
        status = api_get(base_url, "/v1/status/leader", token=token)
        if isinstance(status, str):
            leader_info = status  # "ip:port"
    except Exception:
        pass

    for m in members:
        addr = m.get("Addr", "")
        port = str(m.get("Tags", {}).get("port", m.get("Port", "")))
        addr_port = "{}:{}".format(addr, port)
        is_leader = "*" if leader_info and addr_port == leader_info else ""
        rows.append((
            m.get("Name", ""),
            addr_port,
            m.get("Status", ""),
            is_leader,
            m.get("Tags", {}).get("build", ""),
        ))
    return rows


def get_client_nodes(base_url, token, namespace):
    """Fetch client nodes from /v1/nodes."""
    params = {}
    if namespace:
        params["namespace"] = namespace
    nodes = api_get(base_url, "/v1/nodes", token=token, params=params)
    rows = []
    for n in nodes:
        node_id = n.get("ID", "")[:8]
        rows.append((
            node_id,
            n.get("Name", ""),
            n.get("Status", ""),
            n.get("SchedulingEligibility", ""),
            n.get("Datacenter", ""),
            n.get("NodePool", ""),
            str(n.get("Drain", False)),
        ))
    return rows


def get_running_jobs(base_url, token, namespace):
    """Fetch running jobs from /v1/jobs."""
    params = {"filter": 'Status == "running"'}
    if namespace:
        params["namespace"] = namespace
    else:
        params["namespace"] = "*"
    jobs = api_get(base_url, "/v1/jobs", token=token, params=params)
    rows = []
    for j in jobs:
        tg_count = len(j.get("JobSummary", {}).get("Summary", {})) if j.get("JobSummary") else 0
        # Fallback: count TaskGroups if present
        if tg_count == 0:
            tg_count = len(j.get("TaskGroups", []))
        rows.append((
            j.get("ID", ""),
            j.get("Type", ""),
            j.get("Status", ""),
            j.get("Namespace", ""),
            str(tg_count),
        ))
    return rows


def get_failed_allocs(base_url, token, namespace, limit=20):
    """Fetch recent failed allocations from /v1/allocations."""
    params = {"filter": 'ClientStatus == "failed"'}
    if namespace:
        params["namespace"] = namespace
    else:
        params["namespace"] = "*"
    allocs = api_get(base_url, "/v1/allocations", token=token, params=params)

    # Sort by ModifyIndex descending, take most recent
    allocs.sort(key=lambda a: a.get("ModifyIndex", 0), reverse=True)
    allocs = allocs[:limit]

    rows = []
    for a in allocs:
        desc = a.get("TaskStates", {})
        status_desc = ""
        for _task_name, ts in desc.items():
            events = ts.get("Events", [])
            if events:
                last = events[-1]
                status_desc = last.get("DisplayMessage", last.get("Message", ""))
                break
        rows.append((
            a.get("ID", "")[:8],
            a.get("JobID", ""),
            a.get("TaskGroup", ""),
            a.get("NodeID", "")[:8],
            a.get("ClientStatus", ""),
            status_desc[:60],
        ))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Report Nomad cluster status")
    parser.add_argument("address", help="Nomad address (e.g., http://localhost:4646)")
    parser.add_argument("--token", default=None, help="ACL token")
    parser.add_argument("--namespace", default="", help="Filter by namespace (default: all)")
    parser.add_argument("--format", choices=["table", "json"], default="table", dest="fmt",
                        help="Output format (default: table)")
    args = parser.parse_args()

    base_url = args.address.rstrip("/")

    report = {}

    # Server members
    server_rows = get_server_members(base_url, args.token)
    report["server_members"] = [
        dict(zip(["name", "address", "status", "leader", "version"], r))
        for r in server_rows
    ]

    # Client nodes
    node_rows = get_client_nodes(base_url, args.token, args.namespace)
    report["client_nodes"] = [
        dict(zip(["id", "name", "status", "eligibility", "datacenter", "node_pool", "drain"], r))
        for r in node_rows
    ]

    # Running jobs
    job_rows = get_running_jobs(base_url, args.token, args.namespace)
    report["running_jobs"] = [
        dict(zip(["id", "type", "status", "namespace", "task_groups"], r))
        for r in job_rows
    ]

    # Failed allocations
    failed_rows = get_failed_allocs(base_url, args.token, args.namespace)
    report["failed_allocations"] = [
        dict(zip(["id", "job", "task_group", "node", "status", "description"], r))
        for r in failed_rows
    ]

    if args.fmt == "json":
        print(json.dumps(report, indent=2))
    else:
        print("Nomad Cluster Status: {}".format(base_url))
        print_table(
            "Server Members",
            ("NAME", "ADDRESS", "STATUS", "LEADER", "VERSION"),
            server_rows,
        )
        print_table(
            "Client Nodes",
            ("ID", "NAME", "STATUS", "ELIGIBILITY", "DATACENTER", "NODE POOL", "DRAIN"),
            node_rows,
        )
        print_table(
            "Running Jobs",
            ("ID", "TYPE", "STATUS", "NAMESPACE", "TASK GROUPS"),
            job_rows,
        )
        print_table(
            "Recent Failed Allocations",
            ("ID", "JOB", "TASK GROUP", "NODE", "STATUS", "DESCRIPTION"),
            failed_rows,
        )
        print()


if __name__ == "__main__":
    main()
