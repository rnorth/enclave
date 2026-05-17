<p align="center">
  <img src="docs/logo.png" alt="tsuba logo" width="120"/>
</p>

<h1 align="center">tsuba</h1>

Run any command inside an ephemeral Docker container, with optional egress filtering.

```
$ tsuba -- pi
```

The supplied command runs inside a one-shot Docker container built from tsuba's curated Ubuntu base (git, gh, docker CLI, jq, ripgrep, build tools, [mise](https://mise.jdx.dev/), …). The working directory is mounted at the same absolute path, the container runs as your host user (non-root, matching UID/GID), and outbound HTTP/HTTPS is filtered through a mitmproxy sidecar according to a policy in your config file.

## Philosophy

**Containment, not just isolation.** Every filesystem operation, every shell command, every subprocess your program spawns happens inside a container that is created on invocation and destroyed when the program exits.

**Fail-closed network.** A config with no `networkPolicies` means no outbound HTTP/HTTPS, not "everything allowed." tsuba warns you at startup so you can add policies if you want them.

**Generic.** tsuba wraps any program; there is no special integration with the wrapped tool.

## Quick start

```bash
git clone https://github.com/rnorth/tsuba ~/code/tsuba
cd ~/code/tsuba/tsuba
npm install
npm run build
npm link    # installs `tsuba` globally

mkdir -p ~/.config/tsuba
cat > ~/.config/tsuba/config.yaml <<'YAML'
networkPolicies:
  - host: api.github.com
    policies:
      - action: ALLOW
        path: /repos/.*
        method: GET
YAML

tsuba -- pi
```

On first run, tsuba builds its curated base image — takes a few minutes, then it's cached for every subsequent invocation.

### Language runtimes

The curated image ships [mise](https://mise.jdx.dev/) but **no language runtimes**. Keep your project's runtime versions in a checked-in `.mise.toml` and bring them in at the start of each tsuba session:

```toml
# .mise.toml
[tools]
node = "22"
python = "3.12"
```

```bash
tsuba -- bash -c "mise install && pi"
```

Container teardown is total — `mise install` results don't persist across invocations.

## Configuration

`~/.config/tsuba/config.yaml`:

```yaml
image: <docker image>          # optional; defaults to tsuba's curated base image
networkPolicies:               # optional; missing/empty == default-deny
  - host: <hostname>
    policies:
      - action: ALLOW | DENY
        path: <regex>          # Python re.fullmatch against the request path
        method: GET | POST | ... | "*"
```

See [`docs/container-image.md`](./docs/container-image.md) for the curated tool set, mise integration, and the bring-your-own-base contract; [`docs/container-configuration.md`](./docs/container-configuration.md) for config file details.

See [`docs/egress-control.md`](./docs/egress-control.md) for the full policy semantics and limitations.

## Development

Two independent modules:

```
tsuba/
├── tsuba/    # The CLI (Node/TS) — run `npm test` from inside
└── proxy/      # The mitmproxy egress sidecar (Python + Docker image)
```

See [`docs/architecture.md`](./docs/architecture.md) for an overview and links to the feature docs.

```bash
cd tsuba && npm test           # CLI + integration tests
sh scripts/test-proxy.sh         # proxy tests (Python/pytest)
```
