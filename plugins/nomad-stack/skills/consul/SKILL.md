---
name: consul
description: >
  Manage HashiCorp Consul service networking. Use when configuring service
  discovery, health checks, KV store, service mesh (Connect), intentions,
  gateways (mesh, ingress, terminating, API), prepared queries, ACLs,
  or DNS interface. Covers agent configuration, CLI, HTTP API, and
  Nomad integration.
---

# Consul

HashiCorp Consul — service discovery, service mesh, and configuration platform for distributed systems.

## Quick Reference

### Essential CLI Commands

| Command | Description |
|---------|-------------|
| `consul agent -dev` | Start single-node dev agent |
| `consul agent -server -bootstrap-expect=3` | Start server in cluster mode |
| `consul members` | List cluster members |
| `consul catalog services` | List registered services |
| `consul catalog nodes` | List registered nodes |
| `consul services register <file.hcl>` | Register a service |
| `consul services deregister <file.hcl>` | Deregister a service |
| `consul kv put <key> <value>` | Write key-value pair |
| `consul kv get <key>` | Read value by key |
| `consul kv get -recurse <prefix/>` | List keys under prefix |
| `consul kv delete <key>` | Delete key |
| `consul kv export <prefix/>` | Export KV tree as JSON |
| `consul kv import @backup.json` | Import KV from JSON |
| `consul intention create -allow web backend` | Allow web→backend |
| `consul intention check web backend` | Check if allowed |
| `consul intention delete web backend` | Remove intention |
| `consul connect envoy -sidecar-for <svc>` | Start Envoy sidecar |
| `consul operator raft list-peers` | Show Raft peer set |
| `consul snapshot save backup.snap` | Save cluster snapshot |
| `consul snapshot restore backup.snap` | Restore from snapshot |
| `consul acl bootstrap` | Bootstrap ACL system |
| `consul acl token create -policy-name=<p>` | Create ACL token |
| `consul config write <file.hcl>` | Apply config entry |
| `consul config read -kind <kind> -name <n>` | Read config entry |
| `consul watch -type service -service <svc>` | Watch for changes |

Common flags: `-http-addr=<url>`, `-token=<acl>`, `-datacenter=<dc>`, `-stale`

## DNS Interface

Consul provides DNS-based service discovery on port **8600** (default).

```bash
# Service lookup
dig @127.0.0.1 -p 8600 web.service.consul

# Tagged service
dig @127.0.0.1 -p 8600 production.web.service.consul

# Cross-datacenter
dig @127.0.0.1 -p 8600 web.service.us-west.consul

# SRV record (includes port)
dig @127.0.0.1 -p 8600 web.service.consul SRV

# Node lookup
dig @127.0.0.1 -p 8600 node-1.node.consul

# Virtual IP (Connect)
dig @127.0.0.1 -p 8600 web.virtual.consul
```

For production, configure DNS forwarding so `.consul` domain resolves via Consul.

## Service Registration

### Service Definition (HCL)

```hcl
service {
  name = "web"
  port = 8080
  tags = ["production", "v2"]

  meta {
    version = "2.1.0"
    team    = "platform"
  }

  check {
    id       = "web-health"
    name     = "HTTP Health Check"
    http     = "http://localhost:8080/health"
    interval = "10s"
    timeout  = "2s"
  }

  check {
    id       = "web-tcp"
    name     = "TCP Port Check"
    tcp      = "localhost:8080"
    interval = "15s"
    timeout  = "3s"
  }
}
```

### Health Check Types

| Type | Field | Example |
|------|-------|---------|
| HTTP | `http` | `http://localhost:8080/health` |
| TCP | `tcp` | `localhost:8080` |
| gRPC | `grpc` | `localhost:8080/service.Health` |
| Script | `args` | `["/bin/check.sh"]` |
| TTL | `ttl` | `"30s"` (app must PUT to pass endpoint) |

All checks support: `interval`, `timeout`, `deregister_critical_service_after`

## Key-Value Store

### CLI Patterns

```bash
# Write
consul kv put config/db/host "db.example.com"
consul kv put config/db/port 5432

# Read
consul kv get config/db/host

# List
consul kv get -recurse config/

# Atomic check-and-set (CAS)
consul kv put -cas -modify-index=42 config/db/host "new-db.example.com"

# Delete tree
consul kv delete -recurse config/old/

# Export / Import for backup
consul kv export config/ > backup.json
consul kv import @backup.json
```

### API Patterns

```bash
# Read key
curl http://localhost:8500/v1/kv/config/db/host

# Write key
curl -X PUT -d 'db.example.com' http://localhost:8500/v1/kv/config/db/host

# Blocking query (long-poll for changes)
curl "http://localhost:8500/v1/kv/config/db/host?index=42&wait=5m"

# List keys only
curl "http://localhost:8500/v1/kv/config/?keys"

# Recursive read
curl "http://localhost:8500/v1/kv/config/?recurse"
```

### Common Use Cases
- **Feature flags**: `consul kv put features/new-ui true`
- **Configuration distribution**: apps watch KV for config changes
- **Leader election**: using sessions + KV locks
- **Semaphore**: distributed locking with sessions

## Service Mesh (Consul Connect)

### Core Concepts

- **mTLS**: All service-to-service traffic encrypted with mutual TLS
- **Sidecar proxies**: Envoy proxies handle encryption, routing, and authorization
- **Intentions**: Access control rules for service-to-service communication
- **Config entries**: Declarative traffic management (routing, splitting, resolution)

### Sidecar Proxy Configuration

```hcl
service {
  name = "web"
  port = 8080

  connect {
    sidecar_service {
      proxy {
        upstreams {
          destination_name = "backend"
          local_bind_port  = 9090
        }
        upstreams {
          destination_name = "cache"
          local_bind_port  = 6379
        }
      }
    }
  }
}
```

Application connects to `localhost:9090` for backend and `localhost:6379` for cache — proxy handles mTLS.

### Intentions

```bash
# Allow web to call backend
consul intention create -allow web backend

# Deny by default
consul config write - <<EOF
Kind = "service-intentions"
Name = "backend"
Sources = [
  { Name = "web", Action = "allow" },
  { Name = "*", Action = "deny" }
]
EOF
```

### Configuration Entries

| Kind | Purpose | Key Fields |
|------|---------|------------|
| `service-defaults` | Per-service defaults | protocol, mesh gateway mode, upstream config |
| `service-router` | L7 route matching | routes (match → destination) |
| `service-splitter` | Traffic splitting | splits (weight → service) |
| `service-resolver` | Service resolution | subsets, failover, redirect |
| `service-intentions` | Access control | sources with action/permissions |
| `proxy-defaults` | Global proxy config | mesh gateway mode, access logs |
| `mesh` | Global mesh settings | TLS, peering, transparent proxy |
| `ingress-gateway` | Ingress listener config | protocol, services, TLS |
| `terminating-gateway` | External service mapping | services outside the mesh |

### Traffic Splitting (Canary)

```hcl
Kind = "service-splitter"
Name = "web"
Splits = [
  { Weight = 90, Service = "web", ServiceSubset = "v1" },
  { Weight = 10, Service = "web", ServiceSubset = "v2" },
]
```

### Gateways

| Gateway Type | Direction | Use Case |
|-------------|-----------|----------|
| **Mesh Gateway** | DC ↔ DC | Cross-datacenter or partition communication |
| **Ingress Gateway** | External → Mesh | External traffic enters the mesh |
| **Terminating Gateway** | Mesh → External | Mesh services call external (non-mesh) services |
| **API Gateway** | External → Mesh | L7 HTTP routing with path/header rules |

## ACL System

### Bootstrap

```bash
consul acl bootstrap    # returns initial management token
```

### Common Policy Patterns

```hcl
# Service write (for service registration)
service "web" { policy = "write" }
service "web-sidecar-proxy" { policy = "write" }
node_prefix "" { policy = "read" }

# KV read-only
key_prefix "config/" { policy = "read" }

# Full operator access
operator = "write"
```

## API Reference Highlights

### Agent API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/agent/services` | List local services |
| `PUT` | `/v1/agent/service/register` | Register service |
| `PUT` | `/v1/agent/service/deregister/:id` | Deregister service |
| `GET` | `/v1/agent/checks` | List local checks |
| `GET` | `/v1/agent/members` | List cluster members |

### Catalog API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/catalog/services` | List all services |
| `GET` | `/v1/catalog/service/:svc` | List service instances |
| `GET` | `/v1/catalog/nodes` | List all nodes |
| `GET` | `/v1/catalog/node/:node` | Node detail with services |
| `GET` | `/v1/catalog/datacenters` | List datacenters |

### Health API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/health/service/:svc` | Service instances with health |
| `GET` | `/v1/health/service/:svc?passing` | Only healthy instances |
| `GET` | `/v1/health/checks/:svc` | Health checks for service |
| `GET` | `/v1/health/state/critical` | All critical checks |

### KV API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/kv/:key` | Read key (base64 encoded value) |
| `PUT` | `/v1/kv/:key` | Write key |
| `DELETE` | `/v1/kv/:key` | Delete key |
| `GET` | `/v1/kv/:key?recurse` | Read tree |
| `GET` | `/v1/kv/:key?keys` | List keys only |

### Connect / Config API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/connect/intentions` | List all intentions |
| `GET` | `/v1/config/:kind` | List config entries by kind |
| `GET` | `/v1/config/:kind/:name` | Read specific config entry |
| `PUT` | `/v1/config` | Write config entry |
| `DELETE` | `/v1/config/:kind/:name` | Delete config entry |

Default API address: `http://localhost:8500`. Set via `CONSUL_HTTP_ADDR` env var. Use `CONSUL_HTTP_TOKEN` for ACL token.

## Nomad Integration

Consul integrates with Nomad for:

1. **Auto service registration** — `service` blocks in Nomad job specs register with Consul
2. **Health checks** — Nomad forwards check definitions to Consul
3. **Connect sidecar** — `connect.sidecar_service` in Nomad injects Envoy proxy task
4. **Consul Template** — Nomad `template` stanza uses Consul Template to read KV and service catalog
5. **Auto-join** — Nomad servers/clients discover each other via Consul

### Nomad Job with Consul Connect

```hcl
# In a Nomad job spec
group "web" {
  network {
    mode = "bridge"
    port "http" { to = 8080 }
  }

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

  task "app" {
    driver = "docker"
    config { image = "web:latest" }
  }
}
```

### Consul Template in Nomad

```hcl
# In a Nomad task
template {
  data = <<-EOF
    {{ range service "database" }}
    DB_HOST={{ .Address }}
    DB_PORT={{ .Port }}
    {{ end }}
    FEATURE_FLAG={{ key "config/features/new-ui" }}
  EOF
  destination = "local/env"
  env         = true
}
```

## Common Patterns

- **Multi-DC**: WAN gossip between servers + mesh gateways for service traffic
- **DNS forwarding**: Configure system DNS to forward `.consul` to Consul agent
- **Prepared queries**: Failover to other DCs when local service unhealthy
- **Watch**: `consul watch -type service -service web` for reactive automation
- **Snapshot & DR**: `consul snapshot save` on cron for disaster recovery

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Service not resolving via DNS | `consul catalog services` — verify registered; check DNS port (8600) |
| Connect proxy not starting | `consul connect envoy -sidecar-for <svc>` — check Envoy binary, certs |
| Intention denied | `consul intention check <src> <dst>` — verify allow rule exists |
| "No cluster leader" | `consul operator raft list-peers` — check server quorum |
| Agent can't join | Verify `-retry-join` address, check network/firewall, gossip encryption key |
| Stale reads | Use `?consistent` query param for strong consistency (slower) |
| Health check failing | `consul catalog service <svc>` — inspect check output |

## Scripts

```bash
# Cluster overview
python scripts/consul_status.py http://localhost:8500

# With ACL token and datacenter
python scripts/consul_status.py http://localhost:8500 --token <token> --datacenter dc1

# JSON output
python scripts/consul_status.py http://localhost:8500 --format json
```

## Detailed Reference

- [Service Mesh Reference](references/service_mesh.md) — Connect deep-dive with config entries and gateways
- [CLI Reference](references/cli_reference.md) — complete command reference
- [API Reference](references/api_reference.md) — HTTP API endpoints
