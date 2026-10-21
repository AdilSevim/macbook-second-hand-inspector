#!/usr/bin/env python3
"""Read-only macOS used-Mac inspection. Python 3 standard library only."""
import subprocess, re, pathlib, datetime, platform

EXPECTED_CYCLES = 76
def run(*cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        return (p.stdout + ("\n" + p.stderr if p.returncode else "")).strip()
    except Exception as e:
        return "Unavailable: " + str(e)

def field(text, key):
    match = re.search(r"^\s*" + re.escape(key) + r":\s*(.*?)\s*$", text, re.M | re.I)
    return match.group(1) if match else "UNKNOWN"

def status(label, value, note=""):
    lines.append(f"{label}: {value}" + (f" | {note}" if note else ""))

lines = ["MACBOOK SECOND-HAND INSPECTOR", "Date: " + datetime.datetime.now().isoformat(timespec="seconds"),
         "Read-only diagnostics; UNKNOWN means not verified.", ""]
if platform.system() != "Darwin":
    lines.append("WARNING: This tool must run on macOS.")
hardware = run("system_profiler", "SPHardwareDataType")
power = run("system_profiler", "SPPowerDataType")
storage = run("system_profiler", "SPStorageDataType")
profiles = run("profiles", "status", "-type", "enrollment")
disk = run("diskutil", "info", "disk0")
status("Model Identifier", field(hardware, "Model Identifier"), "PASS" if field(hardware, "Model Identifier") == "Mac14,15" else "WARN: expected Mac14,15")
status("Chip", field(hardware, "Chip"))
status("Memory", field(hardware, "Memory"))
status("Serial number", "[REDACTED]")
status("Storage", storage[:1300])
cycle = field(power, "Cycle Count")
try:
    n = int(cycle)
    note = "PASS: matches advertised 76" if n == EXPECTED_CYCLES else f"WARN: advertised {EXPECTED_CYCLES}, difference {n-EXPECTED_CYCLES:+d}"
except ValueError:
    note = "UNKNOWN: could not read"
status("Battery cycle count", cycle, note)
status("Battery condition", field(power, "Condition"))
status("Maximum capacity", field(power, "Maximum Capacity"))
status("Full charge capacity", field(power, "Full Charge Capacity (mAh)"))
status("Disk SMART", field(disk, "SMART Status"))
status("System Integrity Protection", run("csrutil", "status"))
status("Gatekeeper", run("spctl", "--status"))
status("FileVault", run("fdesetup", "status"))
status("MDM enrollment", profiles, "WARNING: absence of MDM here is NOT proof of no remote enrollment")
lines += ["", "MANUAL CHECKS:", "[ ] Seller removes Find My / Activation Lock",
          "[ ] Erase all content and settings", "[ ] Activate with Wi-Fi and check Remote Management screen",
          "[ ] Set up new owner account before paying", "[ ] Run Apple Diagnostics",
          "[ ] Inspect display, keyboard, trackpad, ports, camera, audio, casing",
          "[ ] Ask for repair history and proof of ownership",
          "", "This report cannot authenticate replaced parts or rule out liquid damage."]
out = pathlib.Path.home() / "Desktop" / ("MacBook_Kontrol_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt")
try:
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print("\nSaved:", out)
except OSError as e:
    print("\n".join(lines))
    print("Could not save report:", e)
