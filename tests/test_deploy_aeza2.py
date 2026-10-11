from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy" / "deploy_aeza2.sh"
CADDY = ROOT / "deploy" / "Caddyfile.aeza2"
FRPS = ROOT / "deploy" / "frps.aeza2.toml.template"
UNIT = ROOT / "deploy" / "neyroloc-broker.service"
RELIABILITY = ROOT / "deploy" / "caddy-reliability.conf"


class Aeza2DeploySafetyTests(unittest.TestCase):
    def test_shell_script_is_syntactically_valid(self) -> None:
        subprocess.run(["bash", "-n", str(DEPLOY)], check=True)

    def test_shared_xray_and_rdev9_are_not_mutated(self) -> None:
        script = DEPLOY.read_text(encoding="utf-8")
        service_commands = [
            line.strip().lower()
            for line in script.splitlines()
            if line.lstrip().startswith("systemctl ")
        ]
        self.assertFalse(
            any("xray" in line and "is-active" not in line for line in service_commands)
        )
        self.assertFalse(any("rdev9" in line for line in service_commands))
        self.assertIn("xray_pid_before", script)
        self.assertIn('systemctl reload caddy', script)
        self.assertNotIn('systemctl restart caddy', script)

    def test_deploy_has_backup_validation_and_rollback(self) -> None:
        script = DEPLOY.read_text(encoding="utf-8")
        self.assertIn("backup_file /etc/caddy/Caddyfile", script)
        self.assertIn("trap rollback ERR", script)
        self.assertIn('caddy validate --config "$work/Caddyfile.validate"', script)
        self.assertIn('/usr/local/bin/frps verify -c "$work/frps.toml"', script)
        self.assertIn("registry.json token", script)
        self.assertIn("caddy-reliability.conf", script)
        self.assertIn("systemctl restart neyroloc-broker", script)
        self.assertNotIn("cat > /etc/caddy/Caddyfile", script)

    def test_network_boundaries_match_aeza2_port_map(self) -> None:
        caddy = CADDY.read_text(encoding="utf-8")
        frps = FRPS.read_text(encoding="utf-8")
        unit = UNIT.read_text(encoding="utf-8")

        self.assertIn("neyroloc.static-assets-io.website:7443", caddy)
        self.assertIn("https://:7443", caddy)
        self.assertIn("disable_tlsalpn_challenge", caddy)
        self.assertIn("path /~!frp*", caddy)
        self.assertIn("reverse_proxy 127.0.0.1:7000", caddy)
        self.assertIn("proxyBindAddr = \"127.0.0.1\"", frps)
        self.assertIn("vhostHTTPPort = 8080", frps)
        self.assertIn("bindPort = 7000", frps)
        self.assertIn("NEYROLOC_PUBLIC_HTTPS_PORT=7443", unit)
        self.assertIn("NEYROLOC_FRPS_PORT=7443", unit)
        self.assertIn("NEYROLOC_FRPS_PROTOCOL=wss", unit)
        reliability = RELIABILITY.read_text(encoding="utf-8")
        self.assertIn("Restart=on-failure", reliability)


if __name__ == "__main__":
    unittest.main()
