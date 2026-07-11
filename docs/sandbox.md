# M1 isolated execution

The M1 runner executes one structured, allowlisted command in a disposable Docker container. It is not exposed directly to an LLM. Tool adapters added in M2 must construct `ExecutionSpec` objects after validating tool-specific arguments.

## Enforced controls

- Exact image allowlist; digest pinning is required by default.
- Exact executable allowlist per image. Shell interpreters must not be allowlisted.
- Docker access is restricted to a configured local `unix://` socket.
- No arbitrary Docker flags, host paths, devices, capabilities or privileged mode.
- Read-only root filesystem.
- All Linux capabilities dropped and `no-new-privileges` enabled.
- Non-root container user.
- CPU, memory, PID, timeout, tmpfs and file-descriptor limits.
- No network by default.
- Optional named lab networks must be explicitly allowlisted and created with Docker's `--internal` flag.
- Every declared target is checked against the immutable scope manifest before execution.
- Only the per-run workspace is mounted; the Docker socket is never mounted into a container.
- Stdout, stderr and declared output files are size-limited and hashed with SHA-256.
- Artifact count and total stored bytes are bounded.
- A thread-safe kill switch stops the active container and blocks future executions.
- Images are never pulled implicitly during a run (`--pull never`).

## Network boundary

`NetworkAccess.NONE` is the default and maps to `--network none`.

`NetworkAccess.LAB` requires all of the following:

1. an allowlisted Docker network name;
2. a network created with `docker network create --internal`;
3. one or more declared HTTP(S) targets;
4. every target accepted by `ScopeManifest`.

An internal Docker network prevents direct external egress, but all containers attached to that lab network remain mutually reachable. Deploy each assessment in a dedicated network and attach only authorized targets.

## Artifact layout

```text
runs/<session UUID>/<task UUID>/<run UUID>/
├── stdout.log
├── stderr.log
└── workspace/
    └── output/
```

Each returned artifact record contains its relative path, kind, byte size and SHA-256 digest. Symbolic links, path traversal, excessive file counts and oversized output are rejected.

## Deliberate limitations

M1 does not include pentesting tools, free-form shell execution, remote Docker daemons, Kubernetes, post-exploitation, credential attacks or unrestricted network egress. Those are not implied by a successful M1 test run.
