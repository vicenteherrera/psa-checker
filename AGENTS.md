# AGENTS.md

Instructions for AI coding assistants working in this repository. `CLAUDE.md` and `.github/copilot-instructions.md` are symlinks to this file.

## Task list

The current backlog of specific tasks for agents lives in [`AGENTS-tasks.md`](./AGENTS-tasks.md). Read it on demand when the user asks you to pick up, continue, or check the status of work — not on every turn (the file is large). If a user request matches an item there, use that entry's context and acceptance criteria instead of re-deriving them.

## Project

`psa-checker` is a Go CLI that statically checks Kubernetes YAML manifests against [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) using the upstream [Pod Security Admission](https://github.com/kubernetes/pod-security-admission) library. It works on raw manifests, Helm-rendered output, and running pods — without a live cluster.

- Module: `github.com/vicenteherrera/psa-checker`
- Go version: see `go.mod`
- Status: alpha — input/output shapes may still change

## Domain

Three Pod Security Standard levels, evaluated against `--level`:

- **privileged** — unrestricted
- **baseline** — minimally restrictive, prevents known privilege escalations
- **restricted** — heavily restricted, current hardening best practices

Supported Kubernetes kinds (anything containing a `PodSpec` / `PodTemplateSpec`):

- `Pod`
- `Deployment`, `DaemonSet`, `ReplicaSet`, `StatefulSet`
- `Job`, `CronJob`

Other kinds (e.g. `ServiceAccount`, `ConfigMap`, CRDs) are silently skipped — that's intentional, not a bug.

## CLI contract

- Input: `-f/--filename <path>`, or `-f -` to read from stdin (enables pipes like `helm template ... | psa-checker -f -` and `kubectl get pods -oyaml | psa-checker -f -`).
- Multi-document YAML is supported; every doc is evaluated independently.
- Exit code **0** = all evaluated objects compliant. Exit code **1** = one or more violations. CI/CD pipelines depend on this — don't change it casually.

## Layout

- `main.go` — entry point
- `cmd/psa-checker/` — Cobra commands (`root.go`, `version.go`)
- `pkg/analyzer/` — core library
  - `client.go` — file I/O, YAML parsing, orchestration
  - `psaEvaluator.go` — PSS evaluation via `k8s.io/pod-security-admission`
  - `model.go` — result data structures
  - `psaEvaluator_test.go` — Ginkgo unit tests
- `test/` — YAML fixtures and shell-based e2e tests (`test-success.sh`, `test-fail.sh`)
- `build/Containerfile` — multi-stage build (golang builder → distroless runtime)
- `install/install.sh` — cross-platform installer
- `.goreleaser.yml` — multi-platform release config (Linux/macOS/Windows × amd64/arm/arm64)
- `.github/workflows/` — CI (build, unit tests, e2e tests, release)

## Architecture

- Clean split: CLI layer (`cmd/`) is thin; business logic lives in `pkg/analyzer/`.
- `Client` and `PsaEvaluator` are interfaces — preserve them when refactoring; they exist for dependency injection in tests.
- Configuration via Viper, bound to Cobra flags.
- Version info (git SHA, tag, build date, builder) is injected at build time via ldflags; surfaced by `psa-checker version`.

## Common commands

Use the `makefile` rather than invoking `go` directly when a target exists:

- `make build` — compile binary
- `make build-release` — release build (`CGO_ENABLED=0`, static)
- `make test` — Ginkgo unit tests (randomized, race detection, coverage)
- `make test-e2e` — end-to-end shell tests
- `make test-noginkgo` — plain `go test` (used in release path)
- `make lint` — runs `lint-go`, `lint-yaml`, `lint-containerfile`
- `make vet` — `go vet`
- `make tidy` — `go mod tidy`
- `make container-build` / `make container-run` — container workflow

Run `make lint test` before declaring work done on a Go change.

## Conventions

- Keep changes minimal and focused; this is a small CLI, not a framework.
- Don't introduce new dependencies without a clear reason — the upstream `pod-security-admission` package is the core dependency and should stay that way.
- Preserve the existing CLI surface unless the user explicitly asks to change it (alpha, but users exist and CI pipelines depend on flags + exit codes).
- Tests use Ginkgo/Gomega; match the surrounding style when adding tests. Add fixtures under `test/` when introducing new evaluation cases.
- Container builds use a distroless runtime and static binaries — don't add runtime dependencies that need a shell or libc.

## Known TODOs (already on the roadmap — don't propose as new ideas)

- Accept PSS version as a parameter (currently hardcoded to `latest`).
- Break-on-first-error flag for early exit.
- Verbose logging options for debugging.
- Configurable handling of non-evaluable API versions.
- Additional output formats (JSON, SARIF, etc.).

If asked to implement one of these, treat it as in-scope.

## Out of scope

- Custom Resource Definition driven pod creation (e.g. Tekton step pods) — the controller decides the final `PodSpec` at runtime, so static analysis can't see it. Documented limitation; don't try to "fix" it.
- Runtime cluster checks — this tool is intentionally static. Use the in-cluster Pod Security Admission controller for that.
