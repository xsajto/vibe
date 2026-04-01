# Consul Connect Service Mesh Reference

## Overview

Consul Connect provides service mesh capabilities including service-to-service
encryption via mTLS, traffic management through L7 routing, and multi-datacenter
federation. All traffic policies are defined as configuration entries.

---

## Proxy Configuration

### Proxy Defaults (Global)

Applies to all Connect proxies cluster-wide.

```hcl
Kind = "proxy-defaults"
Name = "global"

Config {
  protocol                 = "http"
  local_connect_timeout_ms = 5000
  local_request_timeout_ms = 10000
  handshake_timeout_ms     = 10000
}

MeshGateway {
  Mode = "local"
}

TransparentProxy {
  OutboundListenerPort = 15001
  DialedDirectly       = false
}

Expose {
  Checks = true
  Paths  = [
    {
      Path          = "/health"
      LocalPathPort = 8080
      ListenerPort  = 21500
      Protocol      = "http"
    }
  ]
}

AccessLogs {
  Enabled             = true
  DisableListenerLogs = false
  Type                = "stdout"
  JSONFormat           = "{ \"start_time\": \"%START_TIME%\", \"route_name\": \"%ROUTE_NAME%\" }"
}
```

### Service Defaults

Per-service proxy configuration and upstream defaults.

```hcl
Kind     = "service-defaults"
Name     = "web"
Protocol = "http"

MeshGateway {
  Mode = "local"
}

UpstreamConfig {
  Defaults {
    MeshGateway {
      Mode = "remote"
    }
    ConnectTimeoutMs = 5000
    Limits {
      MaxConnections        = 512
      MaxPendingRequests    = 512
      MaxConcurrentRequests = 512
    }
    PassiveHealthCheck {
      Interval     = "30s"
      MaxFailures  = 10
      EnforcingConsecutive5xx = 100
      MaxEjectionPercent      = 10
      BaseEjectionTime        = "30s"
    }
  }

  Overrides = [
    {
      Name             = "api"
      ConnectTimeoutMs = 10000
      Limits {
        MaxConnections = 1024
      }
    }
  ]
}

EnvoyExtensions = [
  {
    Name      = "builtin/lua"
    Arguments = {
      ProxyType  = "connect-proxy"
      Listener   = "inbound"
      Script     = "function envoy_on_request(handle) handle:headers():add('x-custom', 'value') end"
    }
  }
]
```

---

## Traffic Management

### Service Router

L7 HTTP path and header matching to direct traffic to different service subsets.

```hcl
Kind = "service-router"
Name = "web"

Routes = [
  # Route by path prefix
  {
    Match {
      HTTP {
        PathPrefix = "/api/v2"
      }
    }
    Destination {
      Service       = "web"
      ServiceSubset = "v2"
      PrefixRewrite = "/api"
    }
  },
  # Route by header
  {
    Match {
      HTTP {
        Header = [
          {
            Name  = "x-debug"
            Exact = "true"
          }
        ]
      }
    }
    Destination {
      Service       = "web"
      ServiceSubset = "canary"
      NumRetries    = 5
      RetryOnStatusCodes = [503, 504]
    }
  },
  # Route by query parameter
  {
    Match {
      HTTP {
        QueryParam = [
          {
            Name  = "version"
            Exact = "2"
          }
        ]
      }
    }
    Destination {
      Service       = "web"
      ServiceSubset = "v2"
    }
  },
  # Route by method
  {
    Match {
      HTTP {
        Methods    = ["POST", "PUT"]
        PathPrefix = "/admin"
      }
    }
    Destination {
      Service            = "web-admin"
      RequestTimeout     = "30s"
      IdleTimeout        = "60s"
      PrefixRewrite      = "/"
    }
  }
]
```

### Service Splitter

Weighted traffic splitting between service subsets.

```hcl
Kind = "service-splitter"
Name = "web"

Splits = [
  {
    Weight        = 90
    ServiceSubset = "stable"
    RequestHeaders {
      Set {
        "x-version" = "v1"
      }
    }
  },
  {
    Weight        = 10
    ServiceSubset = "canary"
    RequestHeaders {
      Set {
        "x-version" = "v2"
      }
    }
  }
]
```

### Service Resolver

Defines subsets, failover, and redirect behavior.

```hcl
Kind          = "service-resolver"
Name          = "web"
DefaultSubset = "stable"

Subsets = {
  "stable" = {
    Filter = "Service.Meta.version == v1"
  }
  "canary" = {
    Filter = "Service.Meta.version == v2"
  }
  "v2" = {
    Filter = "Service.Meta.version == v2"
    OnlyPassing = true
  }
}

Redirect {
  Service    = ""
  Datacenter = ""
}

Failover = {
  "*" = {
    Datacenters = ["dc2", "dc3"]
  }
  "canary" = {
    ServiceSubset = "stable"
  }
}

ConnectTimeout = "15s"

RequestTimeout = "30s"

LoadBalancer {
  Policy = "least_request"
  LeastRequestConfig {
    ChoiceCount = 5
  }
}
```

**Load balancer policies**: `round_robin`, `random`, `least_request`, `ring_hash`, `maglev`.

Ring hash and maglev support header/cookie/query-parameter-based consistent hashing:

```hcl
LoadBalancer {
  Policy = "ring_hash"
  RingHashConfig {
    MinimumRingSize = 1024
    MaximumRingSize = 8192
  }
  HashPolicies = [
    {
      Field      = "header"
      FieldValue = "x-user-id"
    },
    {
      Field    = "cookie"
      FieldValue = "session"
      CookieConfig {
        TTL  = "0s"
        Path = "/"
      }
      Terminal = true
    }
  ]
}
```

---

## L7 Traffic Shifting Patterns

### Canary Deployment

Gradually shift traffic from stable to canary:

1. Deploy canary instances with `version = v2` metadata
2. Create resolver with subsets (see above)
3. Start with 1% canary traffic, increase over time:

```hcl
# Phase 1: 1% canary
Splits = [
  { Weight = 99, ServiceSubset = "stable" },
  { Weight = 1,  ServiceSubset = "canary" }
]

# Phase 2: 10% canary
Splits = [
  { Weight = 90, ServiceSubset = "stable" },
  { Weight = 10, ServiceSubset = "canary" }
]

# Phase 3: 50/50
Splits = [
  { Weight = 50, ServiceSubset = "stable" },
  { Weight = 50, ServiceSubset = "canary" }
]

# Phase 4: Full rollout
Splits = [
  { Weight = 100, ServiceSubset = "canary" }
]
```

### A/B Testing

Route specific users to a variant using header matching:

```hcl
Kind = "service-router"
Name = "web"
Routes = [
  {
    Match {
      HTTP {
        Header = [
          { Name = "x-test-group", Exact = "B" }
        ]
      }
    }
    Destination {
      ServiceSubset = "variant-b"
    }
  }
  # Default route goes to variant-a (no match block)
]
```

### Blue-Green Deployment

Use a service resolver redirect to flip all traffic:

```hcl
# Active: blue
Kind = "service-resolver"
Name = "web"
Redirect {
  Service = "web-blue"
}

# Cutover: switch to green
Kind = "service-resolver"
Name = "web"
Redirect {
  Service = "web-green"
}
```

---

## mTLS Certificate Management

### Built-in CA

Default provider. Consul manages the full PKI lifecycle.

```hcl
# Server agent configuration
connect {
  enabled = true
  ca_provider = "consul"
  ca_config {
    private_key_type  = "ec"
    private_key_bits  = 256
    leaf_cert_ttl     = "72h"
    rotation_period   = "2160h"     # 90 days
    intermediate_cert_ttl = "8760h" # 1 year
    root_cert_ttl     = "87600h"    # 10 years
  }
}
```

### Vault CA Provider

Delegate certificate management to HashiCorp Vault.

```hcl
connect {
  enabled = true
  ca_provider = "vault"
  ca_config {
    address               = "https://vault.example.com:8200"
    token                 = "s.xxxxxxxxxxxxx"
    root_pki_path         = "connect-root"
    intermediate_pki_path = "connect-intermediate"
    leaf_cert_ttl         = "72h"
    rotation_period       = "2160h"
    private_key_type      = "ec"
    private_key_bits      = 256
    namespace             = "admin"
    auth_method {
      type       = "approle"
      mount_path = "approle"
      params = {
        role_id   = "xxxx"
        secret_id = "xxxx"
      }
    }
  }
}
```

**CA rotation**: `consul connect ca set-config -config-file new-ca.json` triggers
automatic leaf certificate rotation across all services.

---

## Gateway Configurations

### Mesh Gateway

Enables cross-datacenter and cross-partition traffic through WAN.

```hcl
Kind = "mesh"
TransparentProxy {
  MeshDestinationsOnly = true
}
Peering {
  PeerThroughMeshGateways = true
}
```

Mesh gateway modes (set in proxy-defaults, service-defaults, or upstream config):
- **local**: Traffic routes to a local mesh gateway, which forwards to the remote datacenter.
- **remote**: Traffic routes directly to a mesh gateway in the remote datacenter.
- **none**: No mesh gateway; direct connection (requires network connectivity).

Service registration for mesh gateway:

```hcl
service {
  name = "mesh-gateway"
  kind = "mesh-gateway"
  port = 8443

  proxy {
    config {
      envoy_mesh_gateway_no_default_bind = true
      envoy_mesh_gateway_bind_tagged_addresses = true
    }
  }

  tagged_addresses {
    lan {
      address = "10.0.0.5"
      port    = 8443
    }
    wan {
      address = "198.51.100.5"
      port    = 443
    }
  }
}
```

### Ingress Gateway

Exposes Connect services to non-mesh traffic.

```hcl
Kind = "ingress-gateway"
Name = "ingress"

TLS {
  Enabled       = true
  TLSMinVersion = "TLSv1_2"
  CipherSuites  = ["TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"]
}

Listeners = [
  {
    Port     = 8080
    Protocol = "http"
    Services = [
      {
        Name  = "web"
        Hosts = ["web.example.com"]
        RequestHeaders {
          Add {
            "x-forwarded-by" = "ingress"
          }
        }
        ResponseHeaders {
          Remove = ["server"]
        }
      },
      {
        Name  = "api"
        Hosts = ["api.example.com"]
      }
    ]
  },
  {
    Port     = 8443
    Protocol = "http"
    Services = [
      {
        Name = "dashboard"
        Hosts = ["dashboard.example.com"]
      }
    ]
    TLS {
      Enabled = true
      SDS {
        ClusterName  = "sds-cluster"
        CertResource = "dashboard.example.com"
      }
    }
  },
  {
    Port     = 9090
    Protocol = "tcp"
    Services = [
      { Name = "db-proxy" }
    ]
  }
]
```

### Terminating Gateway

Allows mesh services to reach external (non-mesh) services with mTLS origination.

```hcl
Kind = "terminating-gateway"
Name = "terminating"

Services = [
  {
    Name     = "legacy-api"
    CAFile   = "/etc/consul/certs/legacy-ca.pem"
    CertFile = "/etc/consul/certs/legacy-client.pem"
    KeyFile  = "/etc/consul/certs/legacy-client-key.pem"
    SNI      = "legacy-api.example.com"
  },
  {
    Name = "external-db"
  }
]
```

Register the external service so mesh services can discover it:

```hcl
service {
  name    = "legacy-api"
  port    = 443
  address = "legacy-api.example.com"

  connect {
    native = false
  }
}
```

### API Gateway

Cloud-native API gateway (based on Envoy Gateway).

```hcl
Kind = "api-gateway"
Name = "api-gw"

Listeners = [
  {
    Name     = "https"
    Port     = 443
    Protocol = "http"
    Hostname = "*.example.com"
    TLS {
      MinVersion   = "TLSv1_2"
      MaxVersion   = "TLSv1_3"
      Certificates = [
        {
          Kind = "inline-certificate"
          Name = "wildcard-cert"
        }
      ]
    }
  },
  {
    Name     = "http-redirect"
    Port     = 80
    Protocol = "http"
  }
]
```

HTTP route for the API gateway:

```hcl
Kind = "http-route"
Name = "web-route"

Parents = [
  {
    Kind        = "api-gateway"
    Name        = "api-gw"
    SectionName = "https"
  }
]

Hostnames = ["web.example.com"]

Rules = [
  {
    Matches = [
      {
        Path {
          Match = "prefix"
          Value = "/api"
        }
      }
    ]
    Filters {
      URLRewrite {
        Path = "/"
      }
      Headers = [
        {
          Add = { "x-gateway" = "consul" }
        }
      ]
    }
    Services = [
      {
        Name   = "api"
        Weight = 100
      }
    ]
  }
]
```

Inline certificate for API gateway TLS:

```hcl
Kind        = "inline-certificate"
Name        = "wildcard-cert"
Certificate = <<EOF
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
EOF
PrivateKey  = <<EOF
-----BEGIN EC PRIVATE KEY-----
...
-----END EC PRIVATE KEY-----
EOF
```

---

## Transparent Proxy Mode

Transparent proxy redirects all outbound traffic through the sidecar proxy
using iptables rules, removing the need for explicit upstream configuration.

Enabled per service in service-defaults:

```hcl
Kind = "service-defaults"
Name = "web"
TransparentProxy {
  OutboundListenerPort = 15001
  DialedDirectly       = false
}
```

Global setting via mesh config entry:

```hcl
Kind = "mesh"
TransparentProxy {
  MeshDestinationsOnly = true   # Only allow mesh destinations
}
```

Key behaviors:
- Services discover upstreams via Consul DNS or KV
- Outbound connections to registered services are automatically routed through Envoy
- `MeshDestinationsOnly = true` blocks traffic to non-mesh destinations
- Use `DialedDirectly = true` for services that need direct IP-based addressing

---

## Multi-Datacenter Mesh Federation

### WAN Federation via Mesh Gateways

Server configuration for primary datacenter:

```hcl
datacenter         = "dc1"
primary_datacenter = "dc1"

connect {
  enabled                            = true
  enable_mesh_gateway_wan_federation = true
}

acl {
  enabled                  = true
  default_policy           = "deny"
  enable_token_replication = true
}
```

Secondary datacenter joins via mesh gateways:

```hcl
datacenter            = "dc2"
primary_datacenter    = "dc1"
primary_gateways      = ["198.51.100.5:443"]
primary_gateways_interval = "30s"

connect {
  enabled                            = true
  enable_mesh_gateway_wan_federation = true
}
```

### Cluster Peering

Cluster peering connects two independent Consul clusters without WAN federation.
Peered clusters maintain independent control planes.

**Generate peering token (acceptor cluster):**

```shell
consul peering generate-token -name dc2
```

**Establish peering (dialer cluster):**

```shell
consul peering establish -name dc1 -peering-token <token>
```

**Export services to a peer:**

```hcl
Kind = "exported-services"
Name = "default"

Services = [
  {
    Name = "api"
    Consumers = [
      { Peer = "dc2" }
    ]
  },
  {
    Name = "web"
    Consumers = [
      { Peer = "dc2" },
      { Peer = "dc3" }
    ]
  }
]
```

**Reference a peered service as an upstream:**

```hcl
service {
  name = "frontend"
  connect {
    sidecar_service {
      proxy {
        upstreams = [
          {
            destination_name = "api"
            destination_peer = "dc1"
            local_bind_port  = 9091
          }
        ]
      }
    }
  }
}
```

**Failover to a peered service:**

```hcl
Kind = "service-resolver"
Name = "api"

Failover = {
  "*" = {
    Targets = [
      { Peer = "dc2" },
      { Peer = "dc3" }
    ]
  }
}
```

Peering through mesh gateways (recommended for production):

```hcl
Kind = "mesh"
Peering {
  PeerThroughMeshGateways = true
}
```
