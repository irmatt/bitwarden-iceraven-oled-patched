#!/usr/bin/env python3
"""Replace the stale Iceraven fingerprint in Bitwarden's FIDO2 community allowlist.

Defaults are for Iceraven OLED (GoodyOG). Set env vars to override for another build.
"""
import copy
import json
import os
from zipfile import ZipFile

SRC = os.environ.get("SRC_APK", "bitwarden.apk")
DST = os.environ.get("DST_APK", "bitwarden-patched-unsigned.apk")
ASSET = "assets/fido2_privileged_community.json"
OLD = os.environ.get(
    "OLD_FP",
    "9C:0D:22:37:9F:48:7B:70:A4:F9:F8:BE:C0:17:3C:F9:1A:16:44:F0:8F:93:38:5B:5B:78:2C:E3:76:60:BA:81",
)
NEW = os.environ.get(
    "NEW_FP",
    "79:13:7C:D3:F5:02:FD:9D:F9:B0:BB:6A:97:D5:18:FA:28:34:5F:03:FF:F0:CE:FA:40:9F:68:9A:BB:39:E2:14",
)
PKG = os.environ.get("PKG_NAME", "io.github.forkmaintainers.iceraven")


def main():
    assert len(OLD) == len(NEW) == 95, "fingerprints must be 32 colon-separated bytes"
    with ZipFile(SRC) as z:
        original = json.loads(z.read(ASSET))
        patched = copy.deepcopy(original)
        hits = 0
        for app in patched["apps"]:
            if app.get("info", {}).get("package_name") != PKG:
                continue
            for sig in app["info"].get("signatures", []):
                if sig.get("cert_fingerprint_sha256") == OLD:
                    sig["cert_fingerprint_sha256"] = NEW
                    hits += 1
        assert hits == 1, f"expected exactly one fingerprint to replace, got {hits}"
        blob = json.dumps(patched, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
        json.loads(blob)
        with ZipFile(DST, "w") as out:
            for info in z.infolist():
                out.writestr(info, blob if info.filename == ASSET else z.read(info.filename))
        count = len(z.infolist())
    with ZipFile(DST) as z:
        assert json.loads(z.read(ASSET))["apps"] == patched["apps"]
        assert z.testzip() is None
        assert len(z.infolist()) == count
    print(f"patched {ASSET}: {OLD} -> {NEW}; {count} archive entries preserved")


if __name__ == "__main__":
    main()
