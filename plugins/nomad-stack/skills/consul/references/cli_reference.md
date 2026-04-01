# Consul CLI Reference

## Agent Commands

### consul agent

Start a Consul agent (server or client).

```shell
consul agent -config-dir=/etc/consul.d -data-dir=/opt/consul
```

Key flags: `-server`, `-bootstrap-expect=N`, `-datacenter=dc1`, `-node=name`,
`-bind=addr`, `-client=addr`, `-ui`, `-encrypt=key`, `-retry-join=addr`,
`-config-file=path`, `-dev` (development mode).

### consul members

List cluster members.

```shell
consul members -detailed
consul members -wan              # WAN members (servers only)
consul members -status=alive     # Filter by status
consul members -segment=seg1     # Filter by network segment
```

### consul join

Join an agent to a cluster.

```shell
consul join 10.0.0.1
consul join -wan 198.51.100.1    # Join WAN gossip pool
```

### consul leave

Gracefully leave the cluster.

```shell
consul leave
```

### consul reload

Reload agent configuration without restart.

```shell
consul reload
```

### consul monitor

Stream log output from a running agent.

```shell
consul monitor -log-level=debug
consul monitor -log-level=trace -log-json
```

### consul info

Display debugging information about the agent.

```shell
consul info
```

Returns: agent, consul, raft, serf_lan, serf_wan stats.

---

## Catalog Commands

### consul catalog services

List all registered services.

```shell
consul catalog services
consul catalog services -tags          # Include tags
consul catalog services -node=web-01   # Services on a specific node
```

### consul catalog nodes

List all registered nodes.

```shell
consul catalog nodes
consul catalog nodes -detailed         # Include metadata
consul catalog nodes -service=web      # Nodes running a service
consul catalog nodes -near=web-01      # Sort by distance
```

### consul catalog datacenters

List all known datacenters.

```shell
consul catalog datacenters
```

---

## Service Commands

### consul services register

Register a service from a definition file.

```shell
consul services register web.json
consul services register -name=web -port=8080 -tag=production
```

### consul services deregister

Deregister a service.

```shell
consul services deregister web.json
consul services deregister -id=web-1
```

---

## KV Commands

### consul kv put

Write a value to a key.

```shell
consul kv put config/db/host 10.0.0.5
consul kv put -flags=42 config/db/host 10.0.0.5
consul kv put config/db/password @password.txt      # From file
consul kv put -cas -modify-index=123 key value      # Check-and-set
consul kv put -acquire=session-id key value          # Lock acquisition
consul kv put -release=session-id key value          # Lock release
```

### consul kv get

Read a value.

```shell
consul kv get config/db/host
consul kv get -detailed config/db/host    # Include metadata
consul kv get -recurse config/db/         # All keys under prefix
consul kv get -keys config/               # List keys only
consul kv get -separator=/ config/        # List top-level "folders"
```

### consul kv delete

Delete a key.

```shell
consul kv delete config/db/host
consul kv delete -recurse config/db/      # Delete prefix recursively
consul kv delete -cas -modify-index=123 key   # Check-and-set delete
```

### consul kv export

Export KV tree as JSON.

```shell
consul kv export config/                  # Export subtree
consul kv export ""                       # Export everything
consul kv export config/ > backup.json
```

### consul kv import

Import KV data from JSON.

```shell
consul kv import @backup.json
consul kv import -prefix=restored/ @backup.json
cat backup.json | consul kv import -
```

---

## Intention Commands

### consul intention create

Create a service intention (allow/deny).

```shell
consul intention create web api              # Allow web -> api
consul intention create -deny web database   # Deny web -> database
consul intention create -meta key=value web api
```

### consul intention check

Test whether a connection is allowed.

```shell
consul intention check web api
# Returns exit code 0 (allowed) or 1 (denied)
```

### consul intention delete

Delete an intention.

```shell
consul intention delete web api
consul intention delete -id=intention-id
```

### consul intention list

List all intentions.

```shell
consul intention list
```

### consul intention match

Show intentions affecting a service.

```shell
consul intention match web                    # Source match
consul intention match -destination api       # Destination match
```

---

## Connect Commands

### consul connect proxy

Run a local Connect proxy (development only).

```shell
consul connect proxy -sidecar-for=web
consul connect proxy -service=web -upstream=api:9191
```

### consul connect ca

Interact with the Connect CA.

```shell
consul connect ca get-config                 # Show CA configuration
consul connect ca set-config -config-file=ca.json  # Update CA config
```

### consul connect envoy

Run Envoy as a Connect sidecar proxy.

```shell
consul connect envoy -sidecar-for=web
consul connect envoy -sidecar-for=web -admin-bind=127.0.0.1:19000
consul connect envoy -gateway=mesh -register
consul connect envoy -gateway=ingress -register -service=ingress
consul connect envoy -gateway=terminating -register -service=terminating
```

Key flags: `-grpc-addr`, `-token`, `-bootstrap`, `-envoy-binary`,
`-envoy-version`, `-prometheus-backend-port`.

---

## Config Entry Commands

### consul config write

Create or update a configuration entry.

```shell
consul config write service-defaults.hcl
consul config write -cas -modify-index=25 service-defaults.hcl
```

### consul config read

Read a configuration entry.

```shell
consul config read -kind=service-defaults -name=web
consul config read -kind=proxy-defaults -name=global
```

### consul config list

List configuration entries by kind.

```shell
consul config list -kind=service-defaults
consul config list -kind=service-router
consul config list -kind=ingress-gateway
```

### consul config delete

Delete a configuration entry.

```shell
consul config delete -kind=service-defaults -name=web
consul config delete -cas -modify-index=25 -kind=service-defaults -name=web
```

---

## ACL Commands

### consul acl bootstrap

Bootstrap the ACL system (run once).

```shell
consul acl bootstrap
```

### consul acl policy

Manage ACL policies.

```shell
# Create
consul acl policy create -name=web-policy -rules=@web-policy.hcl
consul acl policy create -name=web-policy -rules='service "web" { policy = "write" }'

# Read
consul acl policy read -name=web-policy
consul acl policy read -id=policy-id

# Update
consul acl policy update -name=web-policy -rules=@web-policy-v2.hcl
consul acl policy update -id=policy-id -description="Updated policy"

# Delete
consul acl policy delete -name=web-policy
consul acl policy delete -id=policy-id

# List
consul acl policy list
```

### consul acl token

Manage ACL tokens.

```shell
# Create
consul acl token create -description="Web token" -policy-name=web-policy
consul acl token create -service-identity="web:dc1"
consul acl token create -node-identity="node1:dc1"
consul acl token create -role-name=web-role

# Read
consul acl token read -self
consul acl token read -id=token-accessor-id

# Update
consul acl token update -id=token-accessor-id -policy-name=new-policy -merge-policies

# Delete
consul acl token delete -id=token-accessor-id

# List
consul acl token list
```

### consul acl role

Manage ACL roles.

```shell
consul acl role create -name=web-role -policy-name=web-policy -description="Web role"
consul acl role read -name=web-role
consul acl role update -name=web-role -policy-name=additional-policy -merge-policies
consul acl role delete -name=web-role
consul acl role list
```

### consul acl auth-method

Manage ACL auth methods (Kubernetes, JWT, OIDC).

```shell
consul acl auth-method create -name=k8s \
  -type=kubernetes \
  -kubernetes-host=https://k8s.example.com:6443 \
  -kubernetes-ca-cert=@ca.pem \
  -kubernetes-service-account-jwt=@token.jwt

consul acl auth-method read -name=k8s
consul acl auth-method update -name=k8s -config=@auth-config.json
consul acl auth-method delete -name=k8s
consul acl auth-method list
```

---

## Operator Commands

### consul operator raft

Manage Raft consensus.

```shell
consul operator raft list-peers          # List Raft peers
consul operator raft remove-peer -address=10.0.0.5:8300  # Remove failed server
```

### consul operator autopilot

Manage Autopilot settings.

```shell
consul operator autopilot get-config
consul operator autopilot set-config -cleanup-dead-servers=true
consul operator autopilot set-config -last-contact-threshold=200ms
consul operator autopilot state                # Show server health
```

### consul operator usage

Show usage metrics.

```shell
consul operator usage instances           # Service instance counts
```

---

## Snapshot Commands

### consul snapshot save

Save a point-in-time cluster snapshot.

```shell
consul snapshot save backup.snap
consul snapshot save -stale backup.snap   # Allow stale reads (any server)
```

### consul snapshot restore

Restore a cluster from a snapshot.

```shell
consul snapshot restore backup.snap
```

### consul snapshot inspect

Inspect a snapshot file.

```shell
consul snapshot inspect backup.snap
consul snapshot inspect -kvdetails backup.snap   # Include KV stats
```

---

## Watch Commands

### consul watch

Watch for data changes and invoke a handler.

```shell
# Watch a key
consul watch -type=key -key=config/db/host /usr/local/bin/handler.sh

# Watch a key prefix
consul watch -type=keyprefix -prefix=config/ handler.sh

# Watch services catalog
consul watch -type=services handler.sh

# Watch a specific service
consul watch -type=service -service=web handler.sh
consul watch -type=service -service=web -tag=production handler.sh

# Watch health checks
consul watch -type=checks -service=web handler.sh
consul watch -type=checks -state=critical handler.sh

# Watch nodes
consul watch -type=nodes handler.sh

# Watch custom events
consul watch -type=event -name=deploy handler.sh
```

Watch types: `key`, `keyprefix`, `services`, `service`, `checks`, `nodes`, `event`.

---

## Peering Commands

### consul peering generate-token

Generate a peering token (run on acceptor cluster).

```shell
consul peering generate-token -name=dc2
consul peering generate-token -name=dc2 -meta=env=production
consul peering generate-token -name=dc2 -server-external-addresses=1.2.3.4:8503
```

### consul peering establish

Establish a peering connection (run on dialer cluster).

```shell
consul peering establish -name=dc1 -peering-token=<token>
consul peering establish -name=dc1 -peering-token=<token> -meta=env=production
```

### consul peering list

List all peering connections.

```shell
consul peering list
```

### consul peering read

Read a specific peering connection.

```shell
consul peering read -name=dc1
```

### consul peering delete

Delete a peering connection.

```shell
consul peering delete -name=dc1
```

---

## Namespace Commands (Enterprise)

### consul namespace create

Create a namespace.

```shell
consul namespace create -name=team-web -description="Web team namespace"
consul namespace create -name=team-web -meta=team=web
```

### consul namespace read

Read a namespace.

```shell
consul namespace read team-web
```

### consul namespace update

Update a namespace.

```shell
consul namespace update -name=team-web -description="Updated description"
```

### consul namespace delete

Delete a namespace.

```shell
consul namespace delete team-web
```

### consul namespace list

List all namespaces.

```shell
consul namespace list
```

---

## Common Global Flags

These flags work with most commands:

| Flag | Description |
|------|-------------|
| `-http-addr=addr` | Consul agent address (default: `127.0.0.1:8500`) |
| `-token=token` | ACL token for authentication |
| `-token-file=path` | File containing ACL token |
| `-datacenter=dc` | Target datacenter |
| `-stale` | Allow stale reads (any server, not just leader) |
| `-ca-file=path` | CA certificate for TLS |
| `-client-cert=path` | Client certificate for TLS |
| `-client-key=path` | Client key for TLS |
| `-tls-server-name=name` | Server name for TLS verification |
| `-namespace=ns` | Target namespace (Enterprise) |
| `-partition=part` | Target admin partition (Enterprise) |

Environment variable alternatives:

```shell
export CONSUL_HTTP_ADDR=https://consul.example.com:8501
export CONSUL_HTTP_TOKEN=s.xxxxxxxxxxxx
export CONSUL_HTTP_SSL=true
export CONSUL_CACERT=/etc/consul/ca.pem
export CONSUL_CLIENT_CERT=/etc/consul/client.pem
export CONSUL_CLIENT_KEY=/etc/consul/client-key.pem
export CONSUL_NAMESPACE=default
```
