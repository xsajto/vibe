# Nomad CLI Reference

Complete reference for the `nomad` command-line interface, organized by category.

---

## Job Commands

### nomad job run

Submit or update a job.

```
nomad job run [options] <jobfile>
```

| Flag | Description |
|------|-------------|
| `-check-index <index>` | Submit only if job modify index matches (optimistic locking) |
| `-detach` | Return immediately instead of monitoring |
| `-verbose` | Show full allocation IDs |
| `-var 'key=value'` | Set HCL variable |
| `-var-file <path>` | Load variables from file |
| `-consul-token` | Consul token for service registration |
| `-vault-token` | Vault token for secret access |
| `-hcl1` | Parse as HCLv1 |
| `-json` | Parse as JSON job spec |

```bash
nomad job run webapp.nomad.hcl
nomad job run -var 'image_tag=v1.5' -detach webapp.nomad.hcl
nomad job run -check-index 42 webapp.nomad.hcl
```

### nomad job status

Display status of a job.

```
nomad job status [options] [job_id]
```

| Flag | Description |
|------|-------------|
| `-short` | Show condensed output |
| `-evals` | Show evaluations |
| `-all-allocs` | Show all allocations, not just latest |
| `-verbose` | Show full IDs and timestamps |
| `-json` | Output as JSON |
| `-namespace <ns>` | Target namespace (`*` for all) |

```bash
nomad job status webapp
nomad job status -all-allocs -verbose webapp
nomad job status -namespace=production webapp
```

### nomad job plan

Dry-run a job submission to preview changes.

```
nomad job plan [options] <jobfile>
```

```bash
nomad job plan webapp.nomad.hcl
nomad job plan -var 'count=5' webapp.nomad.hcl
```

> Returns a modify index to use with `nomad job run -check-index`.

### nomad job stop

Stop a running job.

```
nomad job stop [options] <job_id>
```

| Flag | Description |
|------|-------------|
| `-purge` | Remove job from system entirely |
| `-detach` | Return immediately |
| `-yes` | Skip confirmation |
| `-global` | Stop in all regions (multiregion) |
| `-no-shutdown-delay` | Skip shutdown delay |

```bash
nomad job stop webapp
nomad job stop -purge -yes old-job
```

### nomad job validate

Validate a job file without submitting.

```
nomad job validate <jobfile>
```

```bash
nomad job validate webapp.nomad.hcl
```

### nomad job inspect

Display the full job specification as JSON.

```
nomad job inspect [options] <job_id>
```

```bash
nomad job inspect webapp
nomad job inspect -version 3 webapp
```

### nomad job history

Show version history.

```
nomad job history [options] <job_id>
```

| Flag | Description |
|------|-------------|
| `-p` | Show diff between versions |
| `-full` | Show full job spec for each version |
| `-json` | JSON output |

```bash
nomad job history -p webapp
```

### nomad job dispatch

Dispatch an instance of a parameterized job.

```
nomad job dispatch [options] <job_id> [payload_file]
```

| Flag | Description |
|------|-------------|
| `-meta <key>=<value>` | Meta key/value pair |
| `-detach` | Return immediately |
| `-id-prefix-template` | Template for child job ID |

```bash
nomad job dispatch -meta type=daily report-gen payload.json
```

### nomad deployment status

Show deployment status.

```
nomad deployment status [options] <deployment_id>
```

| Flag | Description |
|------|-------------|
| `-verbose` | Full output |
| `-json` | JSON output |
| `-monitor` | Stream deployment updates |

```bash
nomad deployment status abc123
nomad deployment status -monitor abc123
```

### nomad deployment promote

Promote a canary deployment.

```
nomad deployment promote [options] <deployment_id>
```

| Flag | Description |
|------|-------------|
| `-group <name>` | Promote only this group |
| `-detach` | Return immediately |

```bash
nomad deployment promote abc123
nomad deployment promote -group web abc123
```

### nomad deployment fail

Manually fail a deployment.

```
nomad deployment fail <deployment_id>
```

### nomad job revert

Revert a job to a previous version.

```
nomad job revert [options] <job_id> <version>
```

```bash
nomad job revert webapp 3
```

### nomad job periodic force

Force a periodic job to run immediately.

```
nomad job periodic force <job_id>
```

```bash
nomad job periodic force nightly-backup
```

### nomad job eval

Create a new evaluation for a job (force rescheduling).

```
nomad job eval [options] <job_id>
```

| Flag | Description |
|------|-------------|
| `-force-reschedule` | Force reschedule of failed allocs |
| `-detach` | Return immediately |

```bash
nomad job eval -force-reschedule webapp
```

### nomad eval status

Show details of an evaluation.

```
nomad eval status [options] <eval_id>
```

```bash
nomad eval status abc123
```

---

## Allocation Commands

### nomad alloc status

Display allocation status and events.

```
nomad alloc status [options] <alloc_id>
```

| Flag | Description |
|------|-------------|
| `-short` | Condensed output |
| `-stats` | Include resource usage stats |
| `-json` | JSON output |
| `-verbose` | Full timestamps and IDs |

```bash
nomad alloc status abc123
nomad alloc status -stats abc123
```

### nomad alloc logs

Stream logs from an allocation.

```
nomad alloc logs [options] <alloc_id> [task]
```

| Flag | Description |
|------|-------------|
| `-stderr` | Show stderr instead of stdout |
| `-tail` | Tail the logs |
| `-f` | Follow (stream) logs |
| `-n <lines>` | Number of lines to show |

```bash
nomad alloc logs -f abc123 web
nomad alloc logs -stderr -tail -n 100 abc123
```

### nomad alloc exec

Execute a command inside an allocation.

```
nomad alloc exec [options] <alloc_id> <command> [args...]
```

| Flag | Description |
|------|-------------|
| `-task <name>` | Target task |
| `-i` | Pass stdin (default true) |
| `-t` | Allocate a pseudo-TTY |
| `-e <escape>` | Escape character |

```bash
nomad alloc exec -task web abc123 /bin/sh
nomad alloc exec abc123 curl localhost:8080/health
```

### nomad alloc signal

Send a signal to an allocation or task.

```
nomad alloc signal [options] <alloc_id> [task] [signal]
```

```bash
nomad alloc signal abc123 web SIGHUP
```

### nomad alloc restart

Restart a running allocation or task.

```
nomad alloc restart [options] <alloc_id> [task]
```

| Flag | Description |
|------|-------------|
| `-all-tasks` | Restart all tasks |
| `-no-shutdown-delay` | Skip shutdown delay |

```bash
nomad alloc restart abc123
nomad alloc restart -all-tasks abc123
```

### nomad alloc fs

Browse files in an allocation directory.

```
nomad alloc fs [options] <alloc_id> <path>
```

| Flag | Description |
|------|-------------|
| `-stat` | Show file details |
| `-f` | Follow a file |
| `-tail` | Show end of file |
| `-task <name>` | Target task |

```bash
nomad alloc fs abc123 alloc/logs/
nomad alloc fs -tail -f abc123 alloc/logs/web.stdout.0
```

### nomad alloc checks

Display Nomad service check status for an allocation.

```
nomad alloc checks <alloc_id>
```

```bash
nomad alloc checks abc123
```

---

## Node Commands

### nomad node status

Display node status.

```
nomad node status [options] [node_id]
```

| Flag | Description |
|------|-------------|
| `-short` | Condensed output |
| `-stats` | Include resource statistics |
| `-allocs` | Show allocations on node |
| `-json` | JSON output |
| `-verbose` | Full output |
| `-self` | Query local agent node |

```bash
nomad node status
nomad node status -stats -allocs abc123
```

### nomad node drain

Toggle drain mode on a node.

```
nomad node drain [options] <node_id>
```

| Flag | Description |
|------|-------------|
| `-enable` | Enable drain |
| `-disable` | Disable drain |
| `-deadline <dur>` | Drain deadline (e.g., `1h`) |
| `-force` | Force drain (ignore system jobs) |
| `-no-deadline` | No deadline (wait indefinitely) |
| `-monitor` | Stream drain progress |
| `-detach` | Return immediately |
| `-ignore-system` | Ignore system jobs |
| `-keep-ineligible` | Keep node ineligible after drain |

```bash
nomad node drain -enable -deadline 1h -monitor abc123
nomad node drain -disable abc123
```

### nomad node eligibility

Toggle scheduling eligibility on a node.

```
nomad node eligibility [options] <node_id>
```

| Flag | Description |
|------|-------------|
| `-enable` | Enable scheduling |
| `-disable` | Disable scheduling |

```bash
nomad node eligibility -disable abc123
nomad node eligibility -enable abc123
```

---

## Server Commands

### nomad server members

List Nomad server cluster members.

```
nomad server members [options]
```

| Flag | Description |
|------|-------------|
| `-detailed` | Detailed member info |

```bash
nomad server members
nomad server members -detailed
```

### nomad server force-leave

Force a server from the cluster (failed nodes).

```
nomad server force-leave [options] <node>
```

```bash
nomad server force-leave server-3.global
```

---

## Namespace Commands

### nomad namespace list

```
nomad namespace list [options]
```

```bash
nomad namespace list
nomad namespace list -json
```

### nomad namespace apply

Create or update a namespace.

```
nomad namespace apply [options] <name>
```

| Flag | Description |
|------|-------------|
| `-description <desc>` | Namespace description |
| `-quota <name>` | Attach quota specification |

```bash
nomad namespace apply -description "Production workloads" production
```

### nomad namespace delete

```
nomad namespace delete <name>
```

### nomad namespace status

```
nomad namespace status <name>
```

---

## Variable Commands

### nomad var put

Create or update a variable.

```
nomad var put [options] <path> [key=value...]
```

| Flag | Description |
|------|-------------|
| `-namespace <ns>` | Target namespace |
| `-force` | Skip check-and-set |
| `-in <format>` | Input format: `json`, `hcl` |

```bash
nomad var put nomad/jobs/webapp db_host=10.0.0.5 db_port=5432
nomad var put -in json nomad/jobs/webapp @vars.json
```

### nomad var get

Read a variable.

```
nomad var get [options] <path>
```

```bash
nomad var get nomad/jobs/webapp
nomad var get -out json nomad/jobs/webapp
```

### nomad var list

List variables.

```
nomad var list [options] [prefix]
```

```bash
nomad var list
nomad var list nomad/jobs/
```

### nomad var purge

Delete a variable.

```
nomad var purge [options] <path>
```

```bash
nomad var purge nomad/jobs/webapp
```

---

## System Commands

### nomad system gc

Trigger garbage collection.

```
nomad system gc
```

### nomad system reconcile summaries

Reconcile job summaries.

```
nomad system reconcile summaries
```

---

## Operator Commands

### nomad operator raft list-peers

List Raft peers.

```
nomad operator raft list-peers
```

### nomad operator raft remove-peer

Remove a Raft peer.

```
nomad operator raft remove-peer -peer-address <addr>
```

### nomad operator snapshot save

Save a Raft snapshot.

```
nomad operator snapshot save <file>
```

```bash
nomad operator snapshot save backup.snap
```

### nomad operator snapshot restore

Restore a Raft snapshot.

```
nomad operator snapshot restore <file>
```

### nomad operator autopilot get-config

```
nomad operator autopilot get-config
```

### nomad operator autopilot set-config

```
nomad operator autopilot set-config [options]
```

| Flag | Description |
|------|-------------|
| `-cleanup-dead-servers` | Enable/disable dead server cleanup |
| `-max-trailing-logs <n>` | Max log entries behind leader |
| `-server-stabilization-time <dur>` | Server stabilization time |

---

## ACL Commands

### nomad acl bootstrap

Bootstrap the ACL system (first time only).

```
nomad acl bootstrap
```

### nomad acl policy apply

Create or update an ACL policy.

```
nomad acl policy apply [options] <name> <file>
```

```bash
nomad acl policy apply admin admin-policy.hcl
```

### nomad acl policy list

```
nomad acl policy list
```

### nomad acl policy delete

```
nomad acl policy delete <name>
```

### nomad acl token create

Create an ACL token.

```
nomad acl token create [options]
```

| Flag | Description |
|------|-------------|
| `-name <name>` | Token name |
| `-type <type>` | Token type: `client`, `management` |
| `-policy <name>` | Attach policy (repeatable) |
| `-global` | Replicate to all regions |
| `-ttl <dur>` | Token TTL |

```bash
nomad acl token create -name "deploy" -type client -policy deploy-policy -ttl 8h
```

### nomad acl token list

```
nomad acl token list
```

### nomad acl token delete

```
nomad acl token delete <accessor_id>
```

### nomad acl role create

```
nomad acl role create -name <name> -policy <policy> [-policy <policy>...]
```

### nomad acl role list

```
nomad acl role list
```

### nomad acl role delete

```
nomad acl role delete <role_id>
```

---

## Common Global Flags

These flags work with most commands:

| Flag | Description |
|------|-------------|
| `-address <addr>` | Nomad API address (default `http://127.0.0.1:4646`) |
| `-region <region>` | Target region |
| `-namespace <ns>` | Target namespace |
| `-token <token>` | ACL token |
| `-tls-ca-cert <path>` | TLS CA certificate |
| `-tls-client-cert <path>` | TLS client certificate |
| `-tls-client-key <path>` | TLS client key |
| `-tls-server-name <name>` | TLS server name for verification |
| `-no-color` | Disable colored output |

Environment variable equivalents:

```bash
export NOMAD_ADDR=https://nomad.example.com:4646
export NOMAD_TOKEN=<acl_token>
export NOMAD_NAMESPACE=production
export NOMAD_REGION=us-east-1
export NOMAD_CACERT=/path/to/ca.pem
export NOMAD_CLIENT_CERT=/path/to/client.pem
export NOMAD_CLIENT_KEY=/path/to/client-key.pem
```
