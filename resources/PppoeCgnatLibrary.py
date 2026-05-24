import ipaddress
import re
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class PppoeCgnatLibrary:
    """
    Robot Framework library for:
    - Capturing tcpdump output from Raspberry Pi over SSH
    - Parsing PPPoE IP packet lines
    - Validating source IP against CGNAT network 100.64.0.0/10
    """

    # Example lines supported:
    # PPPoE  [ses 0x2b58] IP 100.103.70.200.55165 > 20.189.173.26.https:
    # PPPoE  [ses 0x2b58] IP 100.103.70.200.55165 > 20.189.173.26.443:
    # PPPoE  [ses 0x2b58] IP 100.103.70.200.13227 > 117.96.122.77.domain:
    PPPOE_IP_RE = re.compile(
        r"PPPoE\s+\[ses\s+(?P<session>0x[0-9a-fA-F]+)\]\s+IP\s+"
        r"(?P<src_endpoint>\S+)\s+>\s+(?P<dst_endpoint>\S+?):"
    )

    IPV4_WITH_PORT_RE = re.compile(
        r"^(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\.(?P<port>[^.\s:]+)$"
    )

    def read_sample_tcpdump_file(self, file_path: str) -> str:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise AssertionError(f"Sample tcpdump file does not exist: {path}")
        return path.read_text(encoding="utf-8")

    def capture_tcpdump_from_raspberry(
        self,
        host: str,
        user: str = "pi",
        iface: str = "eth0",
        seconds: int = 20,
        packet_count: int = 30,
        ssh_key: str = "",
    ) -> str:
        """
        Runs tcpdump on Raspberry Pi over SSH.

        Notes:
        - Uses -nn to avoid DNS/service name resolution.
        - Uses timeout to prevent tcpdump from running forever.
        - Uses sudo because tcpdump usually requires elevated privilege.
        """

        remote_cmd = (
            f"sudo timeout {int(seconds)} "
            f"tcpdump -i {shlex.quote(iface)} -nn -l -c {int(packet_count)}"
        )

        ssh_cmd = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
        ]

        if ssh_key:
            ssh_cmd.extend(["-i", str(Path(ssh_key).expanduser())])

        ssh_cmd.append(f"{user}@{host}")
        ssh_cmd.append(remote_cmd)

        completed = subprocess.run(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=int(seconds) + 10,
            check=False,
        )

        output = completed.stdout.strip()

        # tcpdump can return non-zero when timeout stops capture. Do not fail only because rc != 0.
        if not output:
            raise AssertionError(
                f"No tcpdump output received from Raspberry Pi {user}@{host} on interface {iface}"
            )

        return output

    def extract_pppoe_ip_flows(self, tcpdump_output: str) -> List[Dict[str, str]]:
        flows: List[Dict[str, str]] = []

        for line in tcpdump_output.splitlines():
            match = self.PPPOE_IP_RE.search(line)
            if not match:
                continue

            src = self._split_ipv4_endpoint(match.group("src_endpoint"))
            dst = self._split_ipv4_endpoint(match.group("dst_endpoint"))

            if not src:
                continue

            flow = {
                "session": match.group("session"),
                "src_ip": src["ip"],
                "src_port": src["port"],
                "dst_ip": dst["ip"] if dst else "",
                "dst_port": dst["port"] if dst else "",
                "raw_line": line.strip(),
            }
            flows.append(flow)

        return flows

    def get_flows_with_source_ip_in_network(
        self, flows: List[Dict[str, str]], network: str = "100.64.0.0/10"
    ) -> List[Dict[str, str]]:
        ip_network = ipaddress.ip_network(network, strict=False)
        matching = []

        for flow in flows:
            try:
                src_ip = ipaddress.ip_address(flow["src_ip"])
            except ValueError:
                continue

            if src_ip in ip_network:
                matching.append(flow)

        return matching

    def log_matching_flows(self, flows: List[Dict[str, str]]) -> None:
        if not flows:
            print("No matching flows found")
            return

        print("\nMatching CGNAT PPPoE flows:")
        for flow in flows:
            print(
                f"Session={flow['session']} "
                f"{flow['src_ip']}:{flow['src_port']} > "
                f"{flow['dst_ip']}:{flow['dst_port']}"
            )
            print(f"Raw: {flow['raw_line']}")

    def _split_ipv4_endpoint(self, endpoint: str) -> Optional[Dict[str, str]]:
        """
        Splits endpoint like:
        - 100.103.70.200.55165
        - 20.189.173.26.443
        - 20.189.173.26.https
        - 117.96.122.77.domain

        Returns:
        {
            "ip": "100.103.70.200",
            "port": "55165"
        }
        """

        endpoint = endpoint.strip().rstrip(":,")

        match = self.IPV4_WITH_PORT_RE.match(endpoint)
        if not match:
            return None

        ip = match.group("ip")
        port = match.group("port")

        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return None

        return {"ip": ip, "port": port}
