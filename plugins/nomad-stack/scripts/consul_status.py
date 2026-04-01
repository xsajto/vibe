#!/usr/bin/env python3
"""Consul cluster status reporter.

Connects to the Consul HTTP API and reports cluster members, registered
services, critical health checks, and leader info.

Usage:
    python consul_status.py http://localhost:8500
    python consul_status.py http://localhost:8500 --token my-token --datacenter dc1
    python consul_status.py http://localhost:8500 --format json
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def api_get(base_url, path, token=None, params=None):
    """Make a GET request to the Consul API."""
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
        req.add_header("X-Consul-Token", token)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            print("Error: authentication failed (HTTP 403). Check your ACL token.", file=sys.stderr)
        elif exc.code == 401:
            print("Error: unauthorized (HTTP 401). An ACL token may be required.", file=sys.stderr)
        else:
            print("Error: HTTP {} from Consul API: {}".format(exc.code, exc.reason), file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print("Error: could not connect to Consul at {}: {}".format(base_url, exc.reason), file=sys.stderr)
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


# Consul agent/members Status field is an integer:
# 0=None, 1=Alive, 2=Leaving, 3=Left, 4=Failed
_MEMBER_STATUS = {0: "none", 1: "alive", 2: "leaving", 3: "left", 4: "failed"}


def get_cluster_members(base_url, token, datacenter):
    """Fetch cluster members from /v1/agent/members."""
    params = {}
    if datacenter:
        params["dc"] = datacenter
    data = api_get(base_url, "/v1/agent/members", token=token, params=params)
    members = data if isinstance(data, list) else data.get("Members", [])
    rows = []
    for m in members:
        tags = m.get("Tags", {})
        role = "server" if tags.get("role") == "consul" or tags.get("role") == "consul" else tags.get("role", "client")
        # Servers have the "role" tag set; if "vs" or "expect" tags exist it is a server
        if tags.get("expect") or tags.get("vsn_max"):
            role = "server"
        status_int = m.get("Status", 0)
        status_str = _MEMBER_STATUS.get(status_int, str(status_int))
        rows.append((
            m.get("Name", ""),
            "{}:{}".format(m.get("Addr", ""), m.get("Port", "")),
            status_str,
            role,
            tags.get("dc", m.get("Tags", {}).get("datacenter", "")),
        ))
    return rows


def get_registered_services(base_url, token, datacenter):
    """Fetch registered services from /v1/catalog/services."""
    params = {}
    if datacenter:
        params["dc"] = datacenter
    services = api_get(base_url, "/v1/catalog/services", token=token, params=params)
    # services is a dict: {"service_name": ["tag1", "tag2"], ...}
    rows = []
    for name, tags in sorted(services.items()):
        # Get instance count via catalog
        params_svc = {"dc": datacenter} if datacenter else {}
        instances = api_get(base_url, "/v1/catalog/service/{}".format(name), token=token, params=params_svc)
        count = len(instances) if isinstance(instances, list) else 0
        tags_str = ", ".join(tags) if tags else ""
        if len(tags_str) > 50:
            tags_str = tags_str[:47] + "..."
        rows.append((name, str(count), tags_str))
    return rows


def get_critical_checks(base_url, token, datacenter):
    """Fetch critical health checks from /v1/health/state/critical."""
    params = {}
    if datacenter:
        params["dc"] = datacenter
    checks = api_get(base_url, "/v1/health/state/critical", token=token, params=params)
    rows = []
    for c in checks:
        output = c.get("Output", "")
        if len(output) > 60:
            output = output[:57] + "..."
        rows.append((
            c.get("Node", ""),
            c.get("CheckID", ""),
            c.get("ServiceName", ""),
            c.get("Status", ""),
            output,
        ))
    return rows


def get_leader(base_url, token, datacenter):
    """Fetch current leader from /v1/status/leader."""
    params = {}
    if datacenter:
        params["dc"] = datacenter
    leader = api_get(base_url, "/v1/status/leader", token=token, params=params)
    return leader if isinstance(leader, str) else str(leader)


def main():
    parser = argparse.ArgumentParser(description="Report Consul cluster status")
    parser.add_argument("address", help="Consul address (e.g., http://localhost:8500)")
    parser.add_argument("--token", default=None, help="ACL token")
    parser.add_argument("--datacenter", default=None, help="Target datacenter")
    parser.add_argument("--format", choices=["table", "json"], default="table", dest="fmt",
                        help="Output format (default: table)")
    args = parser.parse_args()

    base_url = args.address.rstrip("/")

    report = {}

    # Leader
    leader = get_leader(base_url, args.token, args.datacenter)
    report["leader"] = leader

    # Cluster members
    member_rows = get_cluster_members(base_url, args.token, args.datacenter)
    report["cluster_members"] = [
        dict(zip(["name", "address", "status", "type", "datacenter"], r))
        for r in member_rows
    ]

    # Registered services
    service_rows = get_registered_services(base_url, args.token, args.datacenter)
    report["registered_services"] = [
        dict(zip(["name", "instances", "tags"], r))
        for r in service_rows
    ]

    # Critical checks
    critical_rows = get_critical_checks(base_url, args.token, args.datacenter)
    report["critical_checks"] = [
        dict(zip(["node", "check_id", "service", "status", "output"], r))
        for r in critical_rows
    ]

    if args.fmt == "json":
        print(json.dumps(report, indent=2))
    else:
        print("Consul Cluster Status: {}".format(base_url))
        print("Leader: {}".format(leader))
        print_table(
            "Cluster Members",
            ("NAME", "ADDRESS", "STATUS", "TYPE", "DATACENTER"),
            member_rows,
        )
        print_table(
            "Registered Services",
            ("NAME", "INSTANCES", "TAGS"),
            service_rows,
        )
        print_table(
            "Critical Health Checks",
            ("NODE", "CHECK ID", "SERVICE", "STATUS", "OUTPUT"),
            critical_rows,
        )
        print()


if __name__ == "__main__":
    main()
