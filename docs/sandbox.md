# M1 isolated execution

## Security contract

The sandbox is called only by trusted, typed tool adapters. A language model cannot submit a raw shell string. Each request contains an executable and an argument tuple, and both the image and executable must be allowlisted.

Docker executions include:

- `--network none`;
- `--read-only`;
- `--cap-drop ALL`;
- `--security-opt no-new-privileges:true`;
- numeric unprivileged user;
- CPU, memory and PID limits;
- execution timeout and external kill switch;
- bounded stdout and stderr capture;
- a single writable artifact mount;
- no Docker socket mount.

Production policies require images pinned by SHA-256 digest. The mutable `python:3.11-alpine` tag is used only by the CI integration test.

## Network boundary

Declared target URLs are validated against the immutable scope manifest. M1 still disables container networking entirely. M2 will introduce scoped egress through a controlled gateway or proxy; unrestricted Docker bridge mode is not an accepted fallback.

## Artifacts

Only regular files are collected. Absolute paths, traversal segments, symbolic links, oversized files and excessive file counts are rejected. Logs and copied artifacts are hashed with SHA-256 and stored under a UUID run directory.
