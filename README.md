# PPPoE CGNAT Validation using GitHub + Jenkins + VS Code + Robot Framework

## Goal

This project demonstrates a complete automation test flow:

1. Develop Robot Framework test cases in VS Code.
2. Store the project in GitHub.
3. Jenkins pulls the GitHub repository.
4. Jenkins connects to a Raspberry Pi over SSH.
5. Raspberry Pi runs `tcpdump` on `eth0`.
6. Robot Framework parses PPPoE packets.
7. Test validates that PPPoE source IP belongs to Carrier-Grade NAT range `100.64.0.0/10`.

Example packet:

```text
PPPoE  [ses 0x2b58] IP 100.103.70.200.55165 > 20.189.173.26.https:
```

Expected validation:

```text
100.103.70.200 is inside 100.64.0.0/10
```

---

## Repository Structure

```text
pppoe-cgnat-robot/
├── Jenkinsfile
├── requirements.txt
├── README.md
├── tests/
│   └── pppoe_cgnat_validation.robot
├── resources/
│   └── PppoeCgnatLibrary.py
├── scripts/
│   └── run_local.sh
└── sample/
    └── sample_tcpdump.txt
```

---

## Raspberry Pi Requirements

Raspberry Pi details used in this project:

```text
IP address : 192.168.1.2
Interface  : eth0
```

Install tcpdump on Raspberry Pi:

```bash
sudo apt update
sudo apt install -y tcpdump
```

Verify manually:

```bash
sudo tcpdump -i eth0
```

Recommended command for automation:

```bash
sudo timeout 20 tcpdump -i eth0 -nn -l -c 30
```

Why `-nn`?

- Avoids DNS/service-name resolution.
- Shows port numbers instead of names like `https` or `domain`.
- Makes automation output stable.

Example with `-nn`:

```text
PPPoE  [ses 0x2b58] IP 100.103.70.200.55165 > 20.189.173.26.443:
```

---

## Jenkins Agent Requirements

Install these on the Jenkins agent:

```bash
sudo apt update
sudo apt install -y python3 python3-pip git openssh-client
```

Install Robot Framework dependencies:

```bash
pip3 install -r requirements.txt
```

---

## Jenkins SSH Access to Raspberry Pi

From Jenkins agent, verify SSH:

```bash
ssh pi@192.168.1.2 hostname
```

If using SSH key:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/jenkins_rpi_key
ssh-copy-id -i ~/.ssh/jenkins_rpi_key.pub pi@192.168.1.2
```

Then test:

```bash
ssh -i ~/.ssh/jenkins_rpi_key pi@192.168.1.2 hostname
```

For passwordless tcpdump, add sudo permission on Raspberry Pi:

```bash
sudo visudo
```

Add this line, replacing `pi` if your user is different:

```text
pi ALL=(ALL) NOPASSWD: /usr/bin/tcpdump, /usr/bin/timeout
```

Check tcpdump path:

```bash
which tcpdump
which timeout
```

---

## Run Locally from VS Code Terminal

From project root:

```bash
pip install -r requirements.txt
robot -d results \
  --variable RPI_HOST:192.168.1.2 \
  --variable RPI_USER:pi \
  --variable SSH_KEY:$HOME/.ssh/jenkins_rpi_key \
  --variable IFACE:eth0 \
  --variable CAPTURE_SECONDS:20 \
  --variable PACKET_COUNT:30 \
  tests/pppoe_cgnat_validation.robot
```

Use sample input without Raspberry Pi:

```bash
robot -d results --variable USE_SAMPLE:True tests/pppoe_cgnat_validation.robot
```

---

## Jenkins Job Flow

Jenkins Pipeline stages:

1. Checkout source from GitHub.
2. Create Python virtual environment.
3. Install Robot Framework.
4. SSH check to Raspberry Pi.
5. Run Robot test.
6. Archive Robot reports: `log.html`, `report.html`, `output.xml`.
7. Publish Robot results if Robot Framework plugin is installed.

---

## Test Logic

Robot test case:

```text
Capture PPPoE packets from Raspberry Pi
Extract source IP and source port
Check if source IP belongs to 100.64.0.0/10
Pass when at least one PPPoE packet source IP is inside CGNAT range
Fail when no valid CGNAT source IP is found
```

---

## CGNAT Range

Carrier-Grade NAT IPv4 range:

```text
100.64.0.0/10
```

This covers:

```text
100.64.0.0 to 100.127.255.255
```

Examples:

```text
100.103.70.200  -> PASS
100.64.1.10     -> PASS
100.127.255.1   -> PASS
192.168.1.10    -> FAIL
8.8.8.8         -> FAIL
```

---

## Useful GitHub Commands

```bash
git init
git add .
git commit -m "Add PPPoE CGNAT Robot Jenkins flow"
git branch -M main
git remote add origin https://github.com/<your-user>/pppoe-cgnat-robot.git
git push -u origin main
```

---

## Expected Robot Output

Pass example:

```text
Found CGNAT PPPoE flow: 100.103.70.200:55165 -> 20.189.173.26:443
```

Fail example:

```text
No PPPoE packet source IP found inside 100.64.0.0/10
```
