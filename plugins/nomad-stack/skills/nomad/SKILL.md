---
name: nomad
description: >
  Manage HashiCorp Nomad workload orchestration. Use when deploying jobs
  (service, batch, system, sysbatch), writing HCL job specifications,
  inspecting allocations, managing cluster nodes, planning deployments,
  configuring update/migrate strategies, or troubleshooting scheduling.
  Covers HCL job specs, CLI, HTTP API, and Consul integration.
---

# Nomad

HashiCorp Nomad — distributed workload scheduler for containers, VMs, and standalone applications.

## Quick Reference

### Essential CLI Commands

| Command | Description |
|---------|-------------|
| `nomad job run <file.hcl>` | Register and run a job |
| `nomad job plan <file.hcl>` | Dry-run — show what would change |
| `nomad job status <job-id>` | Show job status and allocations |
| `nomad job stop <job-id>` | Stop a job (deregister) |
| `nomad job inspect <job-id>` | View full job specification |
| `nomad job history <job-id>` | Show job version history |
| `nomad job dispatch <parameterized-job> -meta key=val` | Dispatch parameterized batch job |
| `nomad alloc status <alloc-id>` | Show allocation detail |
| `nomad alloc logs <alloc-id> <task>` | Stream task stdout (`-stderr` for stderr) |
| `nomad alloc exec <alloc-id> <task> <cmd>` | Exec into running task |
| `nomad alloc restart <alloc-id>` | Restart allocation tasks |
| `nomad node status` | List client nodes |
| `nomad node drain -enable <node-id>` | Drain node for maintenance |
| `nomad node eligibility -disable <node-id>` | Mark node ineligible |
| `nomad server members` | List server cluster members |
| `nomad namespace list` | List namespaces |
| `nomad var put <path> key=val` | Store a variable |
| `nomad var get <path>` | Read a variable |
| `nomad system gc` | Trigger garbage collection |

Common flags: `-address=<url>`, `-region=<r>`, `-namespace=<ns>`, `-token=<acl>`, `-json`

## Job Specification (HCL)

### Minimal Service Job

```hcl
job "web" {
  datacenters = ["dc1"]
  type        = "service"

  group "app" {
    count = 3

    network {
      port "http" { to = 8080 }
    }

    service {
      name = "web"
      port = "http"
      provider = "consul"

      check {
        type     = "http"
        path     = "/health"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "server" {
      driver = "docker"

      config {
        image = "myapp:latest"
        ports = ["http"]
      }

      resources {
        cpu    = 500   # MHz
        memory = 256   # MB
      }

      env {
        PORT = "${NOMAD_PORT_http}"
      }
    }
  }
}
```

### Minimal Batch Job

```hcl
job "etl" {
  datacenters = ["dc1"]
  type        = "batch"

  group "transform" {
    task "run" {
      driver = "docker"

      config {
        image   = "etl-runner:latest"
        command = "/bin/run"
        args    = ["--date", "${NOMAD_META_date}"]
      }

      resources {
        cpu    = 1000
        memory = 512
      }
    }
  }
}
```

### Key Stanzas Reference

| Stanza | Location | Purpose |
|--------|----------|---------|
| `job` | Top-level | Job name, type, datacenters, priority, namespace |
| `group` | job > group | Task group with count, networking, services |
| `task` | group > task | Individual workload with driver, config, resources |
| `network` | group > network | Port mappings, mode (bridge/host) |
| `service` | group/task > service | Consul service registration + health checks |
| `update` | job/group > update | Rolling deploy strategy |
| `migrate` | group > migrate | Client drain migration strategy |
| `reschedule` | job/group > reschedule | Failed allocation rescheduling policy |
| `restart` | group/task > restart | Local task restart policy |
| `constraint` | job/group/task > constraint | Hard placement requirements |
| `affinity` | job/group/task > affinity | Soft placement preferences (weighted) |
| `spread` | job/group > spread | Distribute allocs across attribute values |
| `volume` | group > volume | Host or CSI volume declaration |
| `volume_mount` | task > volume_mount | Mount a declared volume into task |
| `artifact` | task > artifact | Download file before task starts |
| `template` | task > template | Render Consul Template / env vars |
| `vault` | task > vault | Vault token integration |
| `consul` | task > consul | Consul token / cluster configuration |
| `resources` | task > resources | CPU, memory, disk, device requirements |
| `lifecycle` | task > lifecycle | Sidecar / init task hooks (prestart, poststart, poststop) |
| `scaling` | group > scaling | Horizontal autoscaling policy |

### Update Strategy

```hcl
update {
  max_parallel      = 1          # deploy 1 at a time
  health_check      = "checks"   # checks | task_states | manual
  min_healthy_time  = "30s"
  healthy_deadline  = "5m"
  progress_deadline = "10m"
  canary            = 1          # promote manually: nomad job promote <id>
  auto_revert       = true       # revert on failed deploy
  auto_promote      = false      # set true to auto-promote canaries
  stagger           = "30s"      # delay between groups
}
```

### Constraint / Affinity / Spread

```hcl
# Hard constraint — must match
constraint {
  attribute = "${attr.kernel.name}"
  value     = "linux"
}

# Soft affinity — prefer but not required
affinity {
  attribute = "${node.datacenter}"
  value     = "us-west-1"
  weight    = 80   # -100 to 100
}

# Spread allocations across racks
spread {
  attribute = "${meta.rack}"
  weight    = 100
  target "r1" { percent = 50 }
  target "r2" { percent = 50 }
}

# Distinct hosts — one alloc per node
constraint {
  operator = "distinct_hosts"
  value    = "true"
}
```

### Template Stanza (Consul Template)

```hcl
template {
  data        = <<-EOF
    DB_HOST={{ key "config/db/host" }}
    DB_PORT={{ key "config/db/port" }}
    {{ range service "postgres" }}
    PG_ADDR={{ .Address }}:{{ .Port }}
    {{ end }}
  EOF
  destination = "local/env.txt"
  env         = true          # load as env vars
  change_mode = "restart"     # restart | signal | noop
}
```

## Scheduling Concepts

### Job Types

| Type | Scheduler | Behavior |
|------|-----------|----------|
| `service` | Generic | Long-lived, always restarted, rolling deploys |
| `batch` | Generic | Run to completion, optionally periodic/parameterized |
| `system` | System | Runs on every eligible node |
| `sysbatch` | SysBatch | One-time batch on every eligible node |

### Evaluation → Allocation Flow

1. Job registered → **Evaluation** created
2. Scheduler processes evaluation → feasibility checks + scoring
3. **Plan** produced → submitted to leader
4. Plan applied → **Allocations** placed on nodes
5. Client starts tasks within allocations

Evaluations trigger on: job register/deregister, node status change, alloc failure, periodic timer.

## API Reference Highlights

### Jobs API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/jobs` | Register a new job |
| `GET` | `/v1/jobs` | List all jobs |
| `GET` | `/v1/job/:id` | Read job definition |
| `POST` | `/v1/job/:id/plan` | Plan a job change (dry-run) |
| `GET` | `/v1/job/:id/allocations` | List job allocations |
| `GET` | `/v1/job/:id/deployments` | List job deployments |
| `DELETE` | `/v1/job/:id` | Deregister (stop) a job |
| `POST` | `/v1/job/:id/dispatch` | Dispatch parameterized job |
| `POST` | `/v1/job/:id/periodic/force` | Force periodic job run |

### Allocations API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/allocations` | List allocations |
| `GET` | `/v1/allocation/:id` | Read allocation detail |
| `POST` | `/v1/client/allocation/:id/restart` | Restart allocation |
| `GET` | `/v1/client/fs/logs/:alloc_id` | Stream logs |

### Nodes API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/nodes` | List nodes |
| `GET` | `/v1/node/:id` | Read node detail |
| `POST` | `/v1/node/:id/drain` | Enable/disable drain |
| `POST` | `/v1/node/:id/eligibility` | Set scheduling eligibility |

Default API address: `http://localhost:4646`. Set via `NOMAD_ADDR` env var.

## Common Patterns

### Rolling Deploy with Canary

```hcl
update {
  canary       = 1
  auto_promote = false
  auto_revert  = true
}
```
Deploy → verify canary → `nomad job promote <id>` → rollout continues.

### Consul Connect Sidecar

```hcl
service {
  name = "web"
  port = "http"

  connect {
    sidecar_service {
      proxy {
        upstreams {
          destination_name = "backend"
          local_bind_port  = 9090
        }
      }
    }
  }
}
```
Task reaches backend at `localhost:9090` through encrypted mesh.

### Parameterized Batch Job

```hcl
job "report" {
  type = "batch"
  parameterized {
    meta_required = ["report_date"]
  }
  # ...
}
```
Dispatch: `nomad job dispatch report -meta report_date=2024-01-01`

### Periodic Batch Job

```hcl
periodic {
  crons            = ["0 */6 * * *"]   # every 6 hours
  prohibit_overlap = true
}
```

## Consul Integration

Nomad natively integrates with Consul for:

1. **Service registration** — `service` blocks in job specs auto-register with Consul
2. **Health checks** — HTTP, TCP, gRPC, script checks forwarded to Consul
3. **Connect (service mesh)** — `connect.sidecar_service` injects Envoy proxy
4. **Template** — `template` stanza uses Consul Template to read KV store and service catalog
5. **Auto-join** — Servers/clients discover each other via Consul

### Nomad Agent Consul Configuration

```hcl
consul {
  address = "127.0.0.1:8500"
  token   = "consul-acl-token"

  server_service_name = "nomad"
  client_service_name = "nomad-client"
  auto_advertise      = true

  server_auto_join = true
  client_auto_join = true
}
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Allocation stuck in `pending` | `nomad alloc status <id>` — check constraint failures, resource exhaustion |
| Deployment failing | `nomad job deployments <id>` — check health check config and deadlines |
| Task restarting in loop | `nomad alloc logs <id> <task> -stderr` — check application errors |
| Node not receiving allocs | `nomad node status <id>` — verify eligibility and drain status |
| "No cluster leader" | `nomad server members` — check quorum (need majority of `bootstrap_expect`) |

## Scripts

```bash
# Cluster overview
python scripts/nomad_status.py http://localhost:4646

# With ACL token and namespace filter
python scripts/nomad_status.py http://localhost:4646 --token <token> --namespace default

# JSON output
python scripts/nomad_status.py http://localhost:4646 --format json
```

## Detailed Reference

- [Job Specification Reference](references/job_specification.md) — all HCL stanzas with parameter tables
- [CLI Reference](references/cli_reference.md) — complete command reference
- [API Reference](references/api_reference.md) — HTTP API endpoints
