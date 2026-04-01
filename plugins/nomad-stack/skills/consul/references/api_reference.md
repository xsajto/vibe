# Consul HTTP API Reference

## Overview

Base URL: `http://127.0.0.1:8500/v1/`

All endpoints support these common parameters:
- `dc=<datacenter>` - Target datacenter (defaults to agent's datacenter)
- `ns=<namespace>` - Target namespace (Enterprise)
- `partition=<partition>` - Target admin partition (Enterprise)

Authentication: Pass ACL token via `X-Consul-Token` header or `token` query parameter.

### Blocking Queries

Many read endpoints support blocking (long-poll) queries for change notification.

| Parameter | Description |
|-----------|-------------|
| `index` | The `X-Consul-Index` value from a previous response. The request blocks until the index advances. |
| `wait` | Maximum blocking duration (e.g., `5m`, `10s`). Default: `5m`. Max: `10m`. |
| `stale` | Allow any server to respond (not just leader). Reduces latency and load on leader. |
| `consistent` | Force consistent read from leader. Higher latency but guarantees latest data. |

Usage pattern:
1. Make initial request, note `X-Consul-Index` response header.
2. Make subsequent request with `?index=<value>&wait=5m`.
3. Response returns immediately if data changed, or after `wait` timeout.

Response headers: `X-Consul-Index`, `X-Consul-KnownLeader`, `X-Consul-LastContact`.

---

## Agent API

### List Services

```
GET /v1/agent/services
```

Returns all services registered with the local agent. Supports `filter` parameter.

### List Checks

```
GET /v1/agent/checks
```

Returns all checks registered with the local agent. Supports `filter` parameter.

### Register Service

```
PUT /v1/agent/service/register
```

Register a new service with the local agent.

```json
{
  "Name": "web",
  "ID": "web-1",
  "Tags": ["production", "v1"],
  "Port": 8080,
  "Address": "10.0.0.5",
  "Meta": { "version": "1.0" },
  "Check": {
    "HTTP": "http://localhost:8080/health",
    "Interval": "10s",
    "Timeout": "5s",
    "DeregisterCriticalServiceAfter": "90m"
  },
  "Connect": {
    "SidecarService": {
      "Proxy": {
        "Upstreams": [
          {
            "DestinationName": "api",
            "LocalBindPort": 9191
          }
        ]
      }
    }
  }
}
```

Parameters: `replace-existing-checks` (bool).

### Deregister Service

```
PUT /v1/agent/service/deregister/:service_id
```

### Join Cluster

```
PUT /v1/agent/join/:address
```

Parameters: `wan` (bool) - Join WAN gossip pool.

### Leave Cluster

```
PUT /v1/agent/leave
```

Gracefully leave the cluster.

### List Members

```
GET /v1/agent/members
```

Parameters: `wan` (bool), `segment` (string).

### Read Agent Self

```
GET /v1/agent/self
```

Returns agent configuration and stats.

### Reload Agent

```
PUT /v1/agent/reload
```

Reload agent configuration files.

### Toggle Maintenance

```
PUT /v1/agent/maintenance
```

Parameters: `enable` (bool, required), `reason` (string).

---

## Catalog API

### List Services

```
GET /v1/catalog/services
```

Returns all registered services and their tags. Supports blocking queries.

Parameters: `node-meta=key:value`.

### Query Service

```
GET /v1/catalog/service/:service
```

Returns nodes providing a service. Supports blocking queries.

Parameters: `tag`, `near` (sort by network distance), `node-meta`, `filter`.

### List Nodes

```
GET /v1/catalog/nodes
```

Returns all registered nodes. Supports blocking queries.

Parameters: `near`, `node-meta`, `filter`.

### Query Node

```
GET /v1/catalog/node/:node
```

Returns services registered on a specific node. Supports blocking queries.

### List Datacenters

```
GET /v1/catalog/datacenters
```

Returns all known datacenters sorted by estimated median RTT.

### Register Entity

```
PUT /v1/catalog/register
```

Low-level registration of nodes, services, and checks. Typically used for
external service registration.

```json
{
  "Datacenter": "dc1",
  "Node": "external-node",
  "Address": "10.0.0.100",
  "Service": {
    "Service": "external-db",
    "Port": 5432,
    "Tags": ["external"]
  },
  "Check": {
    "Node": "external-node",
    "CheckID": "external-db-check",
    "Name": "External DB Health",
    "Status": "passing",
    "ServiceID": "external-db"
  }
}
```

### Deregister Entity

```
PUT /v1/catalog/deregister
```

```json
{
  "Node": "external-node",
  "ServiceID": "external-db"
}
```

---

## Health API

### Service Health

```
GET /v1/health/service/:service
```

Returns service instances with health check status. Supports blocking queries.

Parameters: `passing` (only healthy), `tag`, `near`, `node-meta`, `filter`.

### Service Checks

```
GET /v1/health/checks/:service
```

Returns checks associated with a service. Supports blocking queries.

### State

```
GET /v1/health/state/:state
```

Returns checks in a specific state: `any`, `passing`, `warning`, `critical`.
Supports blocking queries.

### Node Health

```
GET /v1/health/node/:node
```

Returns checks registered on a node. Supports blocking queries.

### Connect-Capable Service

```
GET /v1/health/connect/:service
```

Returns Connect-capable instances (sidecar proxies). Same parameters as service health.

---

## KV API

All KV operations use the `/v1/kv/:key` endpoint.

### Read Key

```
GET /v1/kv/:key
```

Returns the value (base64-encoded) and metadata. Supports blocking queries.

Parameters:
- `recurse` - Return all keys under prefix
- `keys` - Return only key names (no values)
- `separator` - List keys up to separator (folder-like listing)
- `raw` - Return raw value (not base64/JSON wrapped)
- `dc` - Target datacenter

Response fields: `CreateIndex`, `ModifyIndex`, `LockIndex`, `Key`, `Flags`, `Value`, `Session`.

### Write Key

```
PUT /v1/kv/:key
```

Body: raw value bytes.

Parameters:
- `flags` - Unsigned integer metadata (0-2^64)
- `cas` - Check-and-set index (set only if `ModifyIndex` matches)
- `acquire` - Session ID for lock acquisition
- `release` - Session ID for lock release

Returns `true` on success, `false` on CAS failure.

### Delete Key

```
DELETE /v1/kv/:key
```

Parameters:
- `recurse` - Delete all keys under prefix
- `cas` - Check-and-set index

---

## Session API

### Create Session

```
PUT /v1/session/create
```

```json
{
  "Name": "my-lock",
  "Node": "web-01",
  "LockDelay": "15s",
  "Behavior": "release",
  "TTL": "30s",
  "Checks": ["serfHealth"],
  "ServiceChecks": [
    { "ID": "web", "Namespace": "default" }
  ]
}
```

Behaviors: `release` (default, release locks on invalidation), `delete` (delete locked keys).

### Destroy Session

```
PUT /v1/session/destroy/:uuid
```

### Read Session

```
GET /v1/session/info/:uuid
```

Supports blocking queries.

### List Sessions

```
GET /v1/session/list
```

Supports blocking queries.

### Node Sessions

```
GET /v1/session/node/:node
```

List sessions belonging to a node. Supports blocking queries.

### Renew Session

```
PUT /v1/session/renew/:uuid
```

Renew a TTL-based session. Must be called before TTL expires.

---

## Connect / Intentions API

### List Intentions

```
GET /v1/connect/intentions
```

Parameters: `filter`.

### Read Intention

```
GET /v1/connect/intentions/exact
```

Parameters: `source`, `destination` (required).

### Upsert Intention

```
PUT /v1/connect/intentions/exact
```

Parameters: `source`, `destination` (required).

```json
{
  "Action": "allow",
  "Description": "Allow web to api",
  "Meta": { "team": "platform" }
}
```

For L7 intentions with permissions:

```json
{
  "Description": "L7 permissions for web -> api",
  "Permissions": [
    {
      "Action": "allow",
      "HTTP": {
        "PathPrefix": "/api/v1",
        "Methods": ["GET", "POST"],
        "Header": [
          { "Name": "x-api-key", "Present": true }
        ]
      }
    },
    {
      "Action": "deny",
      "HTTP": {
        "PathPrefix": "/admin"
      }
    }
  ]
}
```

### Delete Intention

```
DELETE /v1/connect/intentions/exact
```

Parameters: `source`, `destination` (required).

### CA Roots

```
GET /v1/connect/ca/roots
```

Returns the current set of trusted CA root certificates.

### CA Configuration

```
GET /v1/connect/ca/configuration
```

Returns the current CA provider configuration.

```
PUT /v1/connect/ca/configuration
```

Update CA provider configuration.

---

## Config Entries API

### List Entries

```
GET /v1/config/:kind
```

List all config entries of a given kind. Supports blocking queries.

Kinds: `service-defaults`, `proxy-defaults`, `service-router`, `service-splitter`,
`service-resolver`, `ingress-gateway`, `terminating-gateway`, `mesh`,
`exported-services`, `api-gateway`, `http-route`, `tcp-route`,
`inline-certificate`.

### Read Entry

```
GET /v1/config/:kind/:name
```

Supports blocking queries.

### Write Entry

```
PUT /v1/config
```

Body: JSON config entry. Parameters: `cas` (check-and-set index).

### Delete Entry

```
DELETE /v1/config/:kind/:name
```

Parameters: `cas`.

---

## ACL API

### Bootstrap

```
PUT /v1/acl/bootstrap
```

Bootstrap the ACL system and get the initial management token. Can only be called once.

### Token CRUD

```
PUT    /v1/acl/token              # Create token
GET    /v1/acl/token/:AccessorID  # Read token
PUT    /v1/acl/token/:AccessorID  # Update token
DELETE /v1/acl/token/:AccessorID  # Delete token
GET    /v1/acl/tokens             # List tokens
GET    /v1/acl/token/self         # Read own token
```

Create token body:

```json
{
  "Description": "Web service token",
  "Policies": [{ "Name": "web-policy" }],
  "Roles": [{ "Name": "web-role" }],
  "ServiceIdentities": [{ "ServiceName": "web", "Datacenters": ["dc1"] }],
  "NodeIdentities": [{ "NodeName": "web-01", "Datacenter": "dc1" }],
  "ExpirationTTL": "24h",
  "Local": false
}
```

### Policy CRUD

```
PUT    /v1/acl/policy              # Create
GET    /v1/acl/policy/:id          # Read by ID
GET    /v1/acl/policy/name/:name   # Read by name
PUT    /v1/acl/policy/:id          # Update
DELETE /v1/acl/policy/:id          # Delete
GET    /v1/acl/policies            # List
```

### Role CRUD

```
PUT    /v1/acl/role              # Create
GET    /v1/acl/role/:id          # Read by ID
GET    /v1/acl/role/name/:name   # Read by name
PUT    /v1/acl/role/:id          # Update
DELETE /v1/acl/role/:id          # Delete
GET    /v1/acl/roles             # List
```

### Auth Method CRUD

```
PUT    /v1/acl/auth-method              # Create
GET    /v1/acl/auth-method/:name        # Read
PUT    /v1/acl/auth-method/:name        # Update
DELETE /v1/acl/auth-method/:name        # Delete
GET    /v1/acl/auth-methods             # List
```

### Binding Rule CRUD

```
PUT    /v1/acl/binding-rule              # Create
GET    /v1/acl/binding-rule/:id          # Read
PUT    /v1/acl/binding-rule/:id          # Update
DELETE /v1/acl/binding-rule/:id          # Delete
GET    /v1/acl/binding-rules             # List
```

Parameters: `authmethod` (filter by auth method name).

---

## Event API

### Fire Event

```
PUT /v1/event/fire/:name
```

Body: optional opaque payload.

Parameters: `node` (filter), `service` (filter), `tag` (filter).

### List Events

```
GET /v1/event/list
```

Parameters: `name` (filter by event name). Supports blocking queries.

---

## Operator API

### Raft

```
GET /v1/operator/raft/configuration
```

Returns current Raft peer configuration.

```
DELETE /v1/operator/raft/peer
```

Remove a failed peer. Parameters: `address` or `id` (required).

### Autopilot

```
GET /v1/operator/autopilot/configuration    # Read config
PUT /v1/operator/autopilot/configuration    # Update config
GET /v1/operator/autopilot/health           # Server health
GET /v1/operator/autopilot/state            # Detailed state
```

### Usage

```
GET /v1/operator/usage
```

Returns service instance and node counts.

---

## Snapshot API

### Save Snapshot

```
GET /v1/snapshot
```

Returns a binary snapshot of the cluster state. Parameters: `stale` (bool).

Save with curl:

```shell
curl -o backup.snap http://127.0.0.1:8500/v1/snapshot?stale
```

### Restore Snapshot

```
PUT /v1/snapshot
```

Body: binary snapshot data.

```shell
curl --request PUT --data-binary @backup.snap http://127.0.0.1:8500/v1/snapshot
```

---

## Status API

### Leader

```
GET /v1/status/leader
```

Returns the address of the current Raft leader.

### Peers

```
GET /v1/status/peers
```

Returns the list of Raft peers (server addresses).

---

## Peering API

### Generate Token

```
POST /v1/peering/token
```

Generate a peering establishment token (run on acceptor).

```json
{
  "PeerName": "dc2",
  "Meta": { "env": "production" },
  "ServerExternalAddresses": ["1.2.3.4:8503"]
}
```

### Establish Peering

```
POST /v1/peering/establish
```

Establish a peering connection using a token (run on dialer).

```json
{
  "PeerName": "dc1",
  "PeeringToken": "<base64-encoded-token>",
  "Meta": { "env": "production" }
}
```

### Read Peering

```
GET /v1/peering/:name
```

Returns peering connection details including state and imported/exported service counts.

### List Peerings

```
GET /v1/peerings
```

Returns all peering connections.

### Delete Peering

```
DELETE /v1/peering/:name
```

Deletes a peering connection and removes all imported data.

---

## Content Types and Formats

| Content-Type | Usage |
|---|---|
| `application/json` | Default for most endpoints |
| `application/octet-stream` | Snapshot save/restore |
| `text/plain` | KV raw value reads |

## Error Responses

All errors return a JSON body:

```json
{
  "error": "Permission denied: token with AccessorID 'xxx' lacks permission 'service:write' on \"web\""
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `401` - Unauthorized (missing or invalid ACL token)
- `403` - Forbidden (insufficient ACL permissions)
- `404` - Not found
- `500` - Internal server error
