# Nomad HTTP API Reference

Complete reference for the Nomad HTTP API. Default base URL: `http://127.0.0.1:4646/v1`.

All requests support these common query parameters:

| Parameter | Description |
|-----------|-------------|
| `region` | Target region |
| `namespace` | Target namespace |
| `index` | Blocking query index (long poll) |
| `wait` | Blocking query timeout (e.g., `5m`) |
| `stale` | Allow stale reads (any server) |
| `prefix` | Filter by ID prefix |

Authentication: pass ACL token via `X-Nomad-Token` header or `token` query parameter.

---

## Jobs API

### List Jobs

```
GET /v1/jobs
```

| Parameter | Description |
|-----------|-------------|
| `prefix` | Filter by job ID prefix |
| `meta` | Include job meta in response |

```bash
curl http://localhost:4646/v1/jobs
curl http://localhost:4646/v1/jobs?prefix=web&namespace=production
```

### Read Job

```
GET /v1/job/:job_id
```

```json
{
  "ID": "webapp",
  "Name": "webapp",
  "Type": "service",
  "Status": "running",
  "TaskGroups": [...]
}
```

### Create/Update Job

```
POST /v1/jobs
```

Request body:

```json
{
  "Job": {
    "ID": "webapp",
    "Name": "webapp",
    "Type": "service",
    "Datacenters": ["dc1"],
    "TaskGroups": [{
      "Name": "web",
      "Count": 3,
      "Tasks": [{
        "Name": "server",
        "Driver": "docker",
        "Config": {
          "image": "nginx:1.25",
          "ports": ["http"]
        },
        "Resources": {
          "CPU": 500,
          "MemoryMB": 256
        }
      }],
      "Networks": [{
        "Mode": "bridge",
        "DynamicPorts": [{"Label": "http", "To": 8080}]
      }]
    }]
  }
}
```

Response:

```json
{
  "EvalID": "d092fdc0-...",
  "EvalCreateIndex": 35,
  "JobModifyIndex": 34
}
```

### Plan Job (Dry Run)

```
POST /v1/job/:job_id/plan
```

Request body:

```json
{
  "Job": { ... },
  "Diff": true,
  "PolicyOverride": false
}
```

### Delete Job

```
DELETE /v1/job/:job_id
```

| Parameter | Description |
|-----------|-------------|
| `purge` | Fully purge the job (default false) |
| `global` | Stop in all regions |

```bash
curl -X DELETE http://localhost:4646/v1/job/webapp?purge=true
```

### Job Versions

```
GET /v1/job/:job_id/versions
```

| Parameter | Description |
|-----------|-------------|
| `diffs` | Include diffs between versions |

### Job Summary

```
GET /v1/job/:job_id/summary
```

```json
{
  "JobID": "webapp",
  "Summary": {
    "web": {
      "Queued": 0,
      "Complete": 5,
      "Failed": 0,
      "Running": 3,
      "Starting": 0,
      "Lost": 0
    }
  }
}
```

### Job Evaluations

```
GET /v1/job/:job_id/evaluations
```

### Job Deployments

```
GET /v1/job/:job_id/deployments
```

### Job Latest Deployment

```
GET /v1/job/:job_id/deployment
```

### Dispatch Parameterized Job

```
POST /v1/job/:job_id/dispatch
```

```json
{
  "Payload": "base64_encoded_payload",
  "Meta": {
    "report_type": "quarterly"
  }
}
```

### Force Periodic Job

```
POST /v1/job/:job_id/periodic/force
```

### Revert Job

```
POST /v1/job/:job_id/revert
```

```json
{
  "JobID": "webapp",
  "JobVersion": 3,
  "EnforcePriorVersion": 5
}
```

### Job Scale (Read)

```
GET /v1/job/:job_id/scale
```

### Job Scale (Write)

```
POST /v1/job/:job_id/scale
```

```json
{
  "Count": 5,
  "Target": {
    "Group": "web"
  },
  "Message": "scaling up for traffic"
}
```

---

## Allocations API

### List Allocations

```
GET /v1/allocations
```

| Parameter | Description |
|-----------|-------------|
| `prefix` | Filter by alloc ID prefix |
| `resources` | Include resource usage |
| `task_states` | Include task state info |

### Read Allocation

```
GET /v1/allocation/:alloc_id
```

### Restart Allocation

```
POST /v1/allocation/:alloc_id/restart
```

```json
{
  "TaskName": "web",
  "AllTasks": false,
  "NoShutdownDelay": false
}
```

### Stop Allocation

```
POST /v1/allocation/:alloc_id/stop
```

| Parameter | Description |
|-----------|-------------|
| `no_shutdown_delay` | Skip shutdown delay |

### Signal Allocation

```
POST /v1/allocation/:alloc_id/signal
```

```json
{
  "Signal": "SIGHUP",
  "Task": "web"
}
```

### Allocation Logs

```
GET /v1/client/allocation/:alloc_id/logs
```

| Parameter | Description |
|-----------|-------------|
| `task` | Task name (required) |
| `type` | `stdout` or `stderr` |
| `follow` | Stream logs (boolean) |
| `offset` | Byte offset |
| `origin` | `start` or `end` |
| `plain` | Plain text output |

```bash
curl "http://localhost:4646/v1/client/allocation/abc123/logs?task=web&type=stdout&follow=true&plain=true"
```

### Allocation Exec

```
WebSocket: /v1/client/allocation/:alloc_id/exec
```

| Parameter | Description |
|-----------|-------------|
| `task` | Task name |
| `command` | JSON-encoded command array |
| `tty` | Allocate TTY |

### Allocation Filesystem

```
GET /v1/client/allocation/:alloc_id/fs/ls/:path
GET /v1/client/allocation/:alloc_id/fs/stat/:path
GET /v1/client/allocation/:alloc_id/fs/cat/:path
GET /v1/client/allocation/:alloc_id/fs/readat/:path
GET /v1/client/allocation/:alloc_id/fs/stream/:path
```

---

## Nodes API

### List Nodes

```
GET /v1/nodes
```

| Parameter | Description |
|-----------|-------------|
| `prefix` | Filter by node ID prefix |
| `os` | Filter by OS |

```json
[{
  "ID": "abc123",
  "Name": "client-1",
  "Status": "ready",
  "Datacenter": "dc1",
  "NodeClass": "high-memory",
  "Drain": false,
  "SchedulingEligibility": "eligible"
}]
```

### Read Node

```
GET /v1/node/:node_id
```

### Drain Node

```
POST /v1/node/:node_id/drain
```

```json
{
  "DrainSpec": {
    "Deadline": 3600000000000,
    "IgnoreSystemJobs": false
  },
  "MarkEligible": false
}
```

To disable drain:

```json
{
  "DrainSpec": null,
  "MarkEligible": true
}
```

### Node Eligibility

```
POST /v1/node/:node_id/eligibility
```

```json
{
  "Eligibility": "ineligible"
}
```

### Purge Node

```
POST /v1/node/:node_id/purge
```

### Node Allocations

```
GET /v1/node/:node_id/allocations
```

---

## Deployments API

### List Deployments

```
GET /v1/deployments
```

### Read Deployment

```
GET /v1/deployment/:deployment_id
```

```json
{
  "ID": "abc123",
  "JobID": "webapp",
  "Status": "running",
  "StatusDescription": "Deployment is running",
  "TaskGroups": {
    "web": {
      "DesiredCanaries": 1,
      "DesiredTotal": 3,
      "HealthyAllocs": 1,
      "UnhealthyAllocs": 0,
      "PlacedAllocs": 1,
      "Promoted": false
    }
  }
}
```

### Pause Deployment

```
POST /v1/deployment/pause/:deployment_id
```

```json
{ "Pause": true }
```

### Promote Deployment

```
POST /v1/deployment/promote/:deployment_id
```

```json
{
  "All": true
}
```

Or promote specific groups:

```json
{
  "Groups": ["web"]
}
```

### Fail Deployment

```
POST /v1/deployment/fail/:deployment_id
```

### Set Allocation Health

```
POST /v1/deployment/allocation-health/:deployment_id
```

```json
{
  "HealthyAllocationIDs": ["alloc-1"],
  "UnhealthyAllocationIDs": ["alloc-2"]
}
```

---

## Evaluations API

### List Evaluations

```
GET /v1/evaluations
```

| Parameter | Description |
|-----------|-------------|
| `prefix` | Filter by eval ID prefix |
| `job` | Filter by job ID |
| `status` | Filter by status |

### Read Evaluation

```
GET /v1/evaluation/:eval_id
```

### Evaluation Allocations

```
GET /v1/evaluation/:eval_id/allocations
```

---

## Namespaces API

### List Namespaces

```
GET /v1/namespaces
```

### Read Namespace

```
GET /v1/namespace/:name
```

### Create/Update Namespace

```
POST /v1/namespace/:name
```

```json
{
  "Name": "production",
  "Description": "Production workloads",
  "Quota": "prod-quota",
  "Meta": {
    "team": "platform"
  }
}
```

### Delete Namespace

```
DELETE /v1/namespace/:name
```

---

## Variables API

### List Variables

```
GET /v1/vars
```

| Parameter | Description |
|-----------|-------------|
| `prefix` | Filter by path prefix |

### Read Variable

```
GET /v1/var/:path
```

```json
{
  "Namespace": "default",
  "Path": "nomad/jobs/webapp",
  "Items": {
    "db_host": "10.0.0.5",
    "db_port": "5432"
  },
  "ModifyIndex": 42
}
```

### Create/Update Variable

```
PUT /v1/var/:path
```

```json
{
  "Namespace": "default",
  "Path": "nomad/jobs/webapp",
  "Items": {
    "db_host": "10.0.0.5",
    "db_port": "5432",
    "db_pass": "secret"
  }
}
```

| Parameter | Description |
|-----------|-------------|
| `cas` | Check-and-set index (optimistic locking) |

### Delete Variable

```
DELETE /v1/var/:path
```

---

## ACL API

### Bootstrap ACL

```
POST /v1/acl/bootstrap
```

Response:

```json
{
  "AccessorID": "abc-123",
  "SecretID": "xyz-789",
  "Name": "Bootstrap Token",
  "Type": "management",
  "Global": true
}
```

### List ACL Tokens

```
GET /v1/acl/tokens
```

### Create ACL Token

```
POST /v1/acl/token
```

```json
{
  "Name": "deploy-token",
  "Type": "client",
  "Policies": ["deploy-policy"],
  "Global": false,
  "TTL": "8h"
}
```

### Read ACL Token

```
GET /v1/acl/token/:accessor_id
```

### Delete ACL Token

```
DELETE /v1/acl/token/:accessor_id
```

### Read Self Token

```
GET /v1/acl/token/self
```

### List ACL Policies

```
GET /v1/acl/policies
```

### Create/Update ACL Policy

```
POST /v1/acl/policy/:name
```

```json
{
  "Name": "deploy-policy",
  "Description": "Deployment access",
  "Rules": "namespace \"production\" {\n  policy = \"write\"\n}\nnode {\n  policy = \"read\"\n}"
}
```

### Read ACL Policy

```
GET /v1/acl/policy/:name
```

### Delete ACL Policy

```
DELETE /v1/acl/policy/:name
```

### List ACL Roles

```
GET /v1/acl/roles
```

### Create ACL Role

```
POST /v1/acl/role
```

```json
{
  "Name": "deployer",
  "Description": "Deployment role",
  "Policies": [
    {"Name": "deploy-policy"}
  ]
}
```

### Delete ACL Role

```
DELETE /v1/acl/role/:role_id
```

---

## Agent API

### Agent Self

```
GET /v1/agent/self
```

Returns agent configuration, stats, and member info.

### Agent Members

```
GET /v1/agent/members
```

### Agent Health

```
GET /v1/agent/health
```

```json
{
  "client": { "ok": true, "message": "ok" },
  "server": { "ok": true, "message": "ok" }
}
```

### Agent Join

```
POST /v1/agent/join
```

```json
{
  "Addresses": ["10.0.0.5:4648"]
}
```

### Agent Force Leave

```
POST /v1/agent/force-leave
```

---

## Operator API

### Raft Configuration

```
GET /v1/operator/raft/configuration
```

### Remove Raft Peer

```
DELETE /v1/operator/raft/peer
```

| Parameter | Description |
|-----------|-------------|
| `address` | Peer address to remove |
| `id` | Peer ID to remove |

### Autopilot Configuration

```
GET /v1/operator/autopilot/configuration
PUT /v1/operator/autopilot/configuration
```

### Autopilot Health

```
GET /v1/operator/autopilot/health
```

### Snapshot Save

```
GET /v1/operator/snapshot
```

Returns raw snapshot data. Save to file.

```bash
curl -o backup.snap http://localhost:4646/v1/operator/snapshot
```

### Snapshot Restore

```
PUT /v1/operator/snapshot
```

Upload raw snapshot data.

```bash
curl -X PUT --data-binary @backup.snap http://localhost:4646/v1/operator/snapshot
```

---

## Status API

### Leader

```
GET /v1/status/leader
```

```json
"10.0.0.1:4647"
```

### Peers

```
GET /v1/status/peers
```

```json
["10.0.0.1:4647", "10.0.0.2:4647", "10.0.0.3:4647"]
```

---

## Search API

### Search

```
POST /v1/search
```

```json
{
  "Prefix": "web",
  "Context": "jobs"
}
```

Valid contexts: `jobs`, `evals`, `allocs`, `nodes`, `deployment`, `plugins`, `volumes`, `namespaces`, `variables`.

Response:

```json
{
  "Matches": {
    "jobs": ["webapp", "web-api"]
  },
  "Truncations": {
    "jobs": false
  }
}
```

### Fuzzy Search

```
POST /v1/search/fuzzy
```

```json
{
  "Text": "webapp",
  "Context": "all"
}
```
