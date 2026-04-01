# Nomad Job Specification Reference (HCL)

Complete reference for HashiCorp Nomad job specification stanzas in HCL format.

---

## job

Top-level stanza defining the job.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | `string` | yes | - | Job name (the label on the `job` block) |
| `type` | `string` | no | `service` | Job type: `service`, `batch`, `system`, `sysbatch` |
| `datacenters` | `list(string)` | yes | - | Target datacenters |
| `region` | `string` | no | `global` | Target region |
| `namespace` | `string` | no | `default` | Nomad namespace |
| `priority` | `int` | no | `50` | Scheduling priority (1-100) |
| `all_at_once` | `bool` | no | `false` | Schedule all groups simultaneously |
| `meta` | `map(string)` | no | - | User-defined key/value metadata |
| `node_pool` | `string` | no | `default` | Target node pool |

```hcl
job "webapp" {
  type        = "service"
  datacenters = ["dc1", "dc2"]
  region      = "us-east"
  namespace   = "production"
  priority    = 75

  meta {
    version = "1.5.0"
  }
}
```

---

## group

Defines a group of co-located tasks.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `count` | `int` | no | `1` | Number of allocations |
| `shutdown_delay` | `string` | no | `"0s"` | Delay before killing tasks on deregistration |
| `stop_after_client_disconnect` | `string` | no | - | Time to wait before stopping after client disconnect |
| `max_client_disconnect` | `string` | no | - | Maximum disconnect duration before rescheduling |
| `prevent_reschedule_on_lost` | `bool` | no | `false` | Prevent rescheduling when client is lost |
| `meta` | `map(string)` | no | - | Group-level metadata |

```hcl
group "web" {
  count = 3

  shutdown_delay    = "10s"
  max_client_disconnect = "24h"

  meta {
    tier = "frontend"
  }
}
```

---

## task

Defines an individual unit of work within a group.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `driver` | `string` | yes | - | Task driver: `docker`, `exec`, `raw_exec`, `java`, `qemu` |
| `config` | `block` | yes | - | Driver-specific configuration |
| `user` | `string` | no | - | User to run the task as |
| `env` | `map(string)` | no | - | Environment variables |
| `kill_timeout` | `string` | no | `"5s"` | Time before force-killing the task |
| `kill_signal` | `string` | no | `SIGINT` | Signal sent to stop the task |
| `leader` | `bool` | no | `false` | Mark as group leader (group stops when leader exits) |
| `shutdown_delay` | `string` | no | `"0s"` | Delay before sending kill signal |
| `meta` | `map(string)` | no | - | Task-level metadata |

```hcl
task "server" {
  driver = "docker"

  config {
    image = "nginx:1.25"
    ports = ["http"]
    volumes = [
      "local/nginx.conf:/etc/nginx/nginx.conf",
    ]
  }

  env {
    APP_ENV = "production"
    LOG_LEVEL = "info"
  }

  kill_timeout = "30s"
  leader       = true
}
```

---

## network

Configures networking for a group.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `mode` | `string` | no | `host` | Network mode: `host`, `bridge`, `cni/<name>`, `none` |
| `hostname` | `string` | no | - | Hostname (bridge mode only) |
| `dns` | `block` | no | - | DNS configuration |

### port

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `static` | `int` | no | - | Static port number |
| `to` | `int` | no | - | Port inside the container/network namespace |
| `host_network` | `string` | no | `default` | Host network to bind to |

```hcl
network {
  mode = "bridge"

  port "http" {
    to = 8080
  }

  port "metrics" {
    to = 9090
  }

  port "admin" {
    static = 9999
    to     = 9999
  }

  dns {
    servers  = ["8.8.8.8"]
    searches = ["service.consul"]
  }
}
```

> **Note:** In `bridge` mode, ports are mapped from the host to the allocation network namespace. In `host` mode, the task binds directly to the host port. Use `NOMAD_PORT_<label>` env vars to discover assigned ports.

---

## service

Registers a service with Consul (or Nomad native service discovery).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | `string` | no | `<task_name>` | Service name |
| `port` | `string` | yes | - | Port label to advertise |
| `tags` | `list(string)` | no | - | Service tags |
| `canary_tags` | `list(string)` | no | - | Tags applied during canary deployments |
| `provider` | `string` | no | `consul` | Provider: `consul` or `nomad` |
| `address_mode` | `string` | no | `auto` | Address mode: `auto`, `host`, `driver`, `alloc` |
| `on_update` | `string` | no | `require_healthy` | Update behavior: `require_healthy`, `ignore_warnings`, `ignore` |
| `enable_tag_override` | `bool` | no | `false` | Allow external tag modification |

### check

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `type` | `string` | yes | - | Check type: `http`, `tcp`, `grpc`, `script` |
| `path` | `string` | no | - | HTTP path (for `http` checks) |
| `interval` | `string` | yes | - | Check frequency |
| `timeout` | `string` | yes | - | Check timeout |
| `method` | `string` | no | `GET` | HTTP method |
| `port` | `string` | no | - | Override port label for check |
| `grpc_service` | `string` | no | - | gRPC service name |
| `grpc_use_tls` | `bool` | no | `false` | Use TLS for gRPC check |
| `tls_skip_verify` | `bool` | no | `false` | Skip TLS verification |

### connect (Consul Connect sidecar)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sidecar_service` | `block` | no | - | Sidecar proxy configuration |
| `sidecar_task` | `block` | no | - | Override sidecar task defaults |
| `gateway` | `block` | no | - | Gateway configuration |

```hcl
service {
  name = "web"
  port = "http"
  tags = ["urlprefix-/web", "production"]

  check {
    type     = "http"
    path     = "/health"
    interval = "10s"
    timeout  = "3s"
  }

  check {
    type     = "tcp"
    port     = "http"
    interval = "15s"
    timeout  = "2s"
  }

  connect {
    sidecar_service {
      proxy {
        upstreams {
          destination_name = "database"
          local_bind_port  = 5432
        }
      }
    }
  }
}
```

---

## update

Controls rolling update and canary deployment strategy.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_parallel` | `int` | no | `1` | Max allocations updated simultaneously |
| `health_check` | `string` | no | `checks` | Health check type: `checks`, `task_states`, `manual` |
| `min_healthy_time` | `string` | no | `"10s"` | Minimum time alloc must be healthy |
| `healthy_deadline` | `string` | no | `"5m"` | Time before marking alloc unhealthy |
| `progress_deadline` | `string` | no | `"10m"` | Time before marking deployment failed |
| `auto_revert` | `bool` | no | `false` | Auto-revert on failed deployment |
| `auto_promote` | `bool` | no | `false` | Auto-promote canary deployments |
| `canary` | `int` | no | `0` | Number of canary allocations |
| `stagger` | `string` | no | `"30s"` | Delay between update batches |

```hcl
update {
  max_parallel     = 2
  canary           = 1
  min_healthy_time = "30s"
  healthy_deadline = "5m"
  auto_revert      = true
  auto_promote     = false
  stagger          = "15s"
}
```

> **Note:** When `canary > 0`, the deployment pauses after launching canaries until promoted (`nomad deployment promote`) or `auto_promote = true`.

---

## migrate

Controls allocation migration when a node is draining.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_parallel` | `int` | no | `1` | Max allocations migrated simultaneously |
| `health_check` | `string` | no | `checks` | Health verification method |
| `min_healthy_time` | `string` | no | `"10s"` | Minimum healthy duration |
| `healthy_deadline` | `string` | no | `"5m"` | Deadline for healthy check |

```hcl
migrate {
  max_parallel     = 1
  health_check     = "checks"
  min_healthy_time = "15s"
  healthy_deadline = "5m"
}
```

---

## reschedule

Controls rescheduling of failed allocations.

| Parameter | Type | Required | Default (service) | Description |
|-----------|------|----------|-------------------|-------------|
| `attempts` | `int` | no | unlimited | Max reschedule attempts |
| `interval` | `string` | no | - | Window for `attempts` |
| `delay` | `string` | no | `"30s"` | Initial delay before rescheduling |
| `delay_function` | `string` | no | `"exponential"` | Delay growth: `constant`, `exponential`, `fibonacci` |
| `max_delay` | `string` | no | `"1h"` | Maximum delay between attempts |
| `unlimited` | `bool` | no | `true` (service) | Unlimited reschedule attempts |

```hcl
reschedule {
  delay          = "15s"
  delay_function = "exponential"
  max_delay      = "2m"
  unlimited      = true
}
```

---

## restart

Controls local task restart policy before rescheduling.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `attempts` | `int` | no | `2` | Max restart attempts within `interval` |
| `interval` | `string` | no | `"30m"` | Window for restart attempts |
| `delay` | `string` | no | `"15s"` | Delay between restarts |
| `mode` | `string` | no | `"fail"` | Behavior after exhausting attempts: `fail`, `delay` |
| `render_templates` | `bool` | no | `false` | Re-render templates on restart |

```hcl
restart {
  attempts = 3
  interval = "10m"
  delay    = "30s"
  mode     = "fail"
}
```

---

## constraint

Restricts placement to nodes matching criteria. Can appear at job, group, or task level.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `attribute` | `string` | yes | - | Node attribute to evaluate (`${attr.*}`, `${node.*}`, `${meta.*}`) |
| `operator` | `string` | no | `=` | Operator: `=`, `!=`, `>`, `<`, `>=`, `<=`, `regexp`, `set_contains`, `set_contains_any`, `set_contains_all`, `is_set`, `is_not_set`, `version` |
| `value` | `string` | cond. | - | Value to compare against |

```hcl
constraint {
  attribute = "${attr.kernel.name}"
  value     = "linux"
}

constraint {
  attribute = "${node.class}"
  value     = "high-memory"
}

constraint {
  attribute = "${meta.rack}"
  operator  = "set_contains_any"
  value     = "r1,r2"
}

# Distinct hosts - each alloc on a different node
constraint {
  operator = "distinct_hosts"
  value    = "true"
}
```

---

## affinity

Soft preference for placement (scored, not required).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `attribute` | `string` | yes | - | Node attribute to evaluate |
| `operator` | `string` | no | `=` | Same operators as constraint |
| `value` | `string` | yes | - | Value to compare |
| `weight` | `int` | no | `50` | Weight from -100 (avoid) to 100 (prefer) |

```hcl
affinity {
  attribute = "${meta.datacenter_tier}"
  value     = "premium"
  weight    = 80
}
```

---

## spread

Distributes allocations across a property (e.g., datacenter, rack).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `attribute` | `string` | yes | - | Attribute to spread on |
| `weight` | `int` | no | `50` | Importance (0-100) |
| `target` | `block` | no | - | Desired distribution per value |

```hcl
spread {
  attribute = "${node.datacenter}"
  weight    = 100

  target "dc1" { percent = 60 }
  target "dc2" { percent = 40 }
}
```

---

## volume / volume_mount

Declare and mount CSI or host volumes.

### volume (group-level)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `type` | `string` | yes | - | Volume type: `host`, `csi` |
| `source` | `string` | yes | - | Volume name or CSI volume ID |
| `read_only` | `bool` | no | `false` | Mount as read-only |
| `access_mode` | `string` | cond. | - | CSI access mode: `single-node-reader-only`, `single-node-writer`, `multi-node-reader-only`, `multi-node-single-writer`, `multi-node-multi-writer` |
| `attachment_mode` | `string` | cond. | - | CSI attachment: `file-system`, `block-device` |
| `per_alloc` | `bool` | no | `false` | Create per-allocation volumes |

### volume_mount (task-level)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `volume` | `string` | yes | - | Volume label from group |
| `destination` | `string` | yes | - | Mount path inside task |
| `read_only` | `bool` | no | `false` | Mount as read-only |

```hcl
group "db" {
  volume "data" {
    type   = "csi"
    source = "postgres-data"
    access_mode     = "single-node-writer"
    attachment_mode = "file-system"
  }

  task "postgres" {
    volume_mount {
      volume      = "data"
      destination = "/var/lib/postgresql/data"
    }
  }
}
```

---

## artifact

Downloads artifacts before task starts.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source` | `string` | yes | - | URL to download (supports `http`, `https`, `s3`, `git`, `hg`) |
| `destination` | `string` | no | `local/` | Download destination |
| `mode` | `string` | no | `any` | Download mode: `any`, `file`, `dir` |
| `headers` | `map(string)` | no | - | HTTP headers |
| `options` | `map(string)` | no | - | go-getter options |

```hcl
artifact {
  source      = "https://releases.example.com/app-v1.5.tar.gz"
  destination = "local/"
  options {
    checksum = "sha256:abc123..."
  }
}

artifact {
  source      = "s3://my-bucket/config.json"
  destination = "local/config.json"
  mode        = "file"
}
```

---

## template

Renders files from Consul, Vault, Nomad variables, or inline content using Go templates.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `data` | `string` | cond. | - | Inline template content |
| `source` | `string` | cond. | - | Path to template file on disk |
| `destination` | `string` | yes | - | Rendered output path |
| `change_mode` | `string` | no | `restart` | Action on change: `restart`, `noop`, `signal`, `script` |
| `change_signal` | `string` | no | - | Signal to send (when `change_mode = "signal"`) |
| `perms` | `string` | no | `"644"` | File permissions |
| `env` | `bool` | no | `false` | Parse as KEY=VALUE env file |
| `error_on_missing_key` | `bool` | no | `false` | Fail on missing template keys |
| `wait` | `block` | no | - | Min/max wait before re-render |
| `left_delimiter` | `string` | no | `{{` | Template left delimiter |
| `right_delimiter` | `string` | no | `}}` | Template right delimiter |

```hcl
# Render config from Consul KV and Vault secrets
template {
  data = <<-EOF
    DB_HOST={{ key "db/host" }}
    DB_PORT={{ key "db/port" }}
    DB_PASS={{ with secret "database/creds/app" }}{{ .Data.password }}{{ end }}
  EOF
  destination = "secrets/db.env"
  env         = true
  change_mode = "restart"
}

# Render a config file
template {
  data = <<-EOF
    server {
      listen {{ env "NOMAD_PORT_http" }};
      location / {
        proxy_pass http://{{ range service "backend" }}{{ .Address }}:{{ .Port }}{{ end }};
      }
    }
  EOF
  destination = "local/nginx.conf"
  change_mode = "signal"
  change_signal = "SIGHUP"
}

# Use Nomad variables
template {
  data        = "{{ with nomadVar \"nomad/jobs/webapp\" }}{{ .secret_key }}{{ end }}"
  destination = "secrets/key.txt"
}
```

---

## vault

Configures Vault integration for the task.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `policies` | `list(string)` | no | - | Vault ACL policies (legacy) |
| `role` | `string` | no | - | Vault role for workload identity |
| `change_mode` | `string` | no | `restart` | Action when token changes: `restart`, `signal`, `noop` |
| `change_signal` | `string` | no | - | Signal on change |
| `env` | `bool` | no | `true` | Inject `VAULT_TOKEN` env var |
| `disable_file` | `bool` | no | `false` | Disable writing token to file |

```hcl
vault {
  role        = "webapp"
  change_mode = "restart"
}
```

---

## consul

Configures Consul integration at the task or group level.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cluster` | `string` | no | `default` | Consul cluster name |

```hcl
consul {
  cluster = "default"
}
```

---

## resources

Defines resource requirements for a task.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cpu` | `int` | no | `100` | CPU in MHz |
| `cores` | `int` | no | - | Exact CPU core count (overrides `cpu`) |
| `memory` | `int` | no | `300` | Memory in MB (hard limit) |
| `memory_max` | `int` | no | - | Memory oversubscription max in MB |
| `disk` | `int` | no | `300` | Deprecated; use `ephemeral_disk` |

### device

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | `string` | yes | - | Device type (e.g., `nvidia/gpu`) |
| `count` | `int` | no | `1` | Number of devices |

```hcl
resources {
  cpu        = 500
  memory     = 512
  memory_max = 1024

  device "nvidia/gpu" {
    count = 1
    constraint {
      attribute = "${device.attr.memory}"
      operator  = ">="
      value     = "4 GiB"
    }
  }
}
```

---

## lifecycle

Controls task execution order within a group (sidecars, init containers).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hook` | `string` | yes | - | Lifecycle hook: `prestart`, `poststart`, `poststop` |
| `sidecar` | `bool` | no | `false` | Keep running alongside main task |

```hcl
# Init task (runs before main tasks)
task "init" {
  lifecycle {
    hook    = "prestart"
    sidecar = false
  }
  driver = "docker"
  config {
    image   = "busybox:1"
    command = "/bin/sh"
    args    = ["-c", "echo initializing"]
  }
}

# Sidecar (runs alongside main tasks)
task "log-shipper" {
  lifecycle {
    hook    = "poststart"
    sidecar = true
  }
  driver = "docker"
  config { image = "fluent/fluentbit:latest" }
}

# Cleanup task (runs after main tasks exit)
task "cleanup" {
  lifecycle {
    hook = "poststop"
  }
  driver = "docker"
  config {
    image   = "busybox:1"
    command = "/bin/sh"
    args    = ["-c", "echo cleaning up"]
  }
}
```

> **Execution order:** `prestart` (non-sidecar) -> `prestart` (sidecar) -> main tasks + `poststart` (sidecar) -> `poststop`.

---

## scaling

Configures external autoscaling (used with Nomad Autoscaler).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `min` | `int` | no | `0` | Minimum group count |
| `max` | `int` | yes | - | Maximum group count |
| `enabled` | `bool` | no | `true` | Enable autoscaling |
| `policy` | `block` | no | - | Autoscaler policy block |

```hcl
scaling {
  min     = 2
  max     = 10
  enabled = true

  policy {
    evaluation_interval = "30s"
    cooldown            = "3m"

    check "cpu" {
      source = "nomad-apm"
      query  = "avg_cpu"
      strategy "target-value" {
        target = 70
      }
    }
  }
}
```

---

## multiregion

Configures multi-region job deployments.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `strategy.max_parallel` | `int` | no | `0` | Regions deployed simultaneously (0 = all) |
| `strategy.on_failure` | `string` | no | `fail_all` | `fail_all` or `fail_local` |

```hcl
multiregion {
  strategy {
    max_parallel = 1
    on_failure   = "fail_all"
  }

  region "us-east-1" {
    count       = 3
    datacenters = ["dc1"]
    meta { region_tier = "primary" }
  }

  region "eu-west-1" {
    count       = 2
    datacenters = ["dc2"]
    meta { region_tier = "secondary" }
  }
}
```

---

## periodic

Schedules the job to run on a cron schedule (batch jobs only).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cron` | `string` | yes | - | Cron expression |
| `prohibit_overlap` | `bool` | no | `false` | Prevent concurrent runs |
| `time_zone` | `string` | no | `UTC` | IANA time zone |
| `enabled` | `bool` | no | `true` | Enable periodic scheduling |

```hcl
job "backup" {
  type = "batch"

  periodic {
    cron             = "0 2 * * *"
    prohibit_overlap = true
    time_zone        = "America/New_York"
  }
}
```

---

## parameterized

Defines a parameterized job (dispatch with payload/metadata).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `payload` | `string` | no | `optional` | Payload requirement: `optional`, `required`, `forbidden` |
| `meta_required` | `list(string)` | no | - | Required meta keys on dispatch |
| `meta_optional` | `list(string)` | no | - | Optional meta keys on dispatch |

```hcl
job "report-generator" {
  type = "batch"

  parameterized {
    payload       = "required"
    meta_required = ["report_type"]
    meta_optional = ["email", "format"]
  }

  group "generate" {
    task "run" {
      driver = "docker"
      config {
        image   = "reports:latest"
        command = "/bin/generate"
        args    = ["${NOMAD_META_report_type}"]
      }

      dispatch_payload {
        file = "input.json"
      }
    }
  }
}
```

> **Dispatch:** `nomad job dispatch -meta report_type=quarterly -id-prefix-template=q1 report-generator payload.json`

---

## ephemeral_disk

Configures the ephemeral disk for a group.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `size` | `int` | no | `300` | Disk size in MB |
| `migrate` | `bool` | no | `false` | Migrate data during allocation migration |
| `sticky` | `bool` | no | `false` | Prefer placing on the same node for data locality |

```hcl
ephemeral_disk {
  size    = 1000
  migrate = true
  sticky  = true
}
```
