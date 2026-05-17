#!/usr/bin/env python3
"""Apply iptables egress rules for the tsuba proxy sidecar.

Usage: setup_iptables.py <proxy_port>

Creates a TSUBA chain in the nat and filter tables (IPv4) and
in ip6tables (IPv6), then wires it into OUTPUT.

Design notes:
  - We use OUTPUT, not PREROUTING, because `-m owner` (used to exempt
    the proxy's own traffic) is only valid for locally-generated packets
    and cannot be evaluated in PREROUTING under iptables-nft.
  - Non-root traffic to ports 80/443 is REDIRECT'd to the proxy.
  - Non-root UDP 53 is REDIRECT'd to the DNS interceptor (port 5353).
  - Everything else from non-root is DROP'd so non-HTTP protocols
    (SSH, arbitrary TCP, raw UDP) cannot bypass egress controls.
  - All IPv6 is blocked (no IPv6 proxy support).
"""

import subprocess
import sys

_DNS_INTERCEPTOR_PORT = 5353


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[iptables] {' '.join(cmd)}: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def _ipt(*args: str, check: bool = True) -> None:
    cmd = ["iptables"] + list(args)
    if check:
        _run(cmd)
    else:
        subprocess.run(cmd, capture_output=True)


def _ip6t(*args: str, check: bool = True) -> None:
    cmd = ["ip6tables"] + list(args)
    if check:
        _run(cmd)
    else:
        subprocess.run(cmd, capture_output=True)


def teardown() -> None:
    print("[iptables] Removing rules...", file=sys.stderr)
    _ipt("-t", "nat", "-F", "TSUBA", check=False)
    _ipt("-t", "filter", "-D", "OUTPUT", "-j", "TSUBA", check=False)
    _ipt("-t", "filter", "-F", "TSUBA", check=False)
    _ipt("-t", "filter", "-X", "TSUBA", check=False)
    _ip6t("-D", "OUTPUT", "-j", "TSUBA", check=False)
    _ip6t("-F", "TSUBA", check=False)
    _ip6t("-X", "TSUBA", check=False)
    print("[iptables] Rules removed.", file=sys.stderr)


def setup(proxy_port: int) -> None:
    print(f"[iptables] Setting up rules (proxy port {proxy_port})...", file=sys.stderr)

    # NAT: redirect HTTP/HTTPS from non-root through mitmproxy
    _ipt("-t", "nat", "-N", "TSUBA", check=False)
    _ipt("-t", "nat", "-F", "TSUBA")
    _ipt("-t", "nat", "-A", "OUTPUT", "-j", "TSUBA")
    for port in [80, 443]:
        _ipt("-t", "nat", "-A", "TSUBA",
             "-p", "tcp", "--dport", str(port),
             "-m", "owner", "!", "--uid-owner", "root",
             "-j", "REDIRECT", "--to-port", str(proxy_port))

    # Intercept non-root UDP 53 → DNS interceptor
    _ipt("-t", "nat", "-A", "TSUBA",
         "-p", "udp", "--dport", "53",
         "-m", "owner", "!", "--uid-owner", "root",
         "-j", "REDIRECT", "--to-port", str(_DNS_INTERCEPTOR_PORT))

    # Filter: block non-root traffic not going through the proxy
    _ipt("-t", "filter", "-N", "TSUBA", check=False)
    _ipt("-t", "filter", "-F", "TSUBA")
    _ipt("-t", "filter", "-A", "OUTPUT", "-j", "TSUBA")
    _ipt("-t", "filter", "-A", "TSUBA", "-m", "owner", "--uid-owner", "root", "-j", "RETURN")
    _ipt("-t", "filter", "-A", "TSUBA", "-o", "lo", "-j", "RETURN")
    # After a NAT REDIRECT the filter chain evaluates the packet with the rewritten
    # destination port but before the kernel commits the reroute to loopback.
    # The "-o lo" rule above does NOT match at this point, so we must explicitly
    # allow packets headed for each redirected local port.
    _ipt("-t", "filter", "-A", "TSUBA",
         "-p", "tcp", "--dport", str(proxy_port), "-d", "127.0.0.1", "-j", "RETURN")
    _ipt("-t", "filter", "-A", "TSUBA",
         "-p", "udp", "--dport", str(_DNS_INTERCEPTOR_PORT), "-d", "127.0.0.1", "-j", "RETURN")
    _ipt("-t", "filter", "-A", "TSUBA", "-j", "DROP")

    # IPv6: block all non-root outbound
    _ip6t("-N", "TSUBA", check=False)
    _ip6t("-F", "TSUBA")
    _ip6t("-A", "OUTPUT", "-j", "TSUBA")
    _ip6t("-A", "TSUBA", "-m", "owner", "--uid-owner", "root", "-j", "RETURN")
    _ip6t("-A", "TSUBA", "-o", "lo", "-j", "RETURN")
    _ip6t("-A", "TSUBA", "-j", "DROP")

    print("[iptables] Rules installed.", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <proxy_port>", file=sys.stderr)
        sys.exit(1)
    setup(int(sys.argv[1]))
