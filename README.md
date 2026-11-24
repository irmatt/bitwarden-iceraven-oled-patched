# Bitwarden patched for Iceraven OLED (GoodyOG)

**This repository is primarily documentation.** A rebuilt APK is published in
[Releases](https://github.com/irmatt/bitwarden-iceraven-oled-patched/releases) for convenience, but you should treat it as untrusted third-party
software. A password manager signed by somebody other than its vendor is a real security
trade-off: you are trusting this repo's build process and signing key with your vault.
**Verify the fingerprints and the patch yourself, or follow the instructions below and build your
own.** This project is not affiliated with Bitwarden, Iceraven, or GoodyOG.

## The problem

Bitwarden's Android app only grants FIDO2/passkey/password-manager browser integration to
browsers whose **package name and signing certificate** appear in an allowlist shipped inside the
APK (`assets/fido2_privileged_community.json`). Out of the box, Iceraven is in that list — but with
the certificate of the **upstream** build:

| Build | Package | Certificate SHA-256 |
|-|-|-|
| Upstream Iceraven (`fork-maintainers/iceraven-browser`) | `io.github.forkmaintainers.iceraven` | `9C:0D:22:37:9F:48:7B:70:A4:F9:F8:BE:C0:17:3C:F9:1A:16:44:F0:8F:93:38:5B:5B:78:2C:E3:76:60:BA:81` |
| **Iceraven OLED** (`GoodyOG/Iceraven-OLED`) | `io.github.forkmaintainers.iceraven` | `79:13:7C:D3:F5:02:FD:9D:F9:B0:BB:6A:97:D5:18:FA:28:34:5F:03:FF:F0:CE:FA:40:9F:68:9A:BB:39:E2:14` |

GoodyOG's OLED fork re-signs every release with its own key, so the fingerprint differs from the
one Bitwarden trusts. The result is the familiar
`Passkey operation failed because browser is not privileged`, or autofill simply not appearing.

This repo replaces exactly one value in Bitwarden's allowlist: the stale upstream fingerprint is
swapped for the **Iceraven OLED** one. No other app logic is changed.

Links:

- Iceraven OLED (the fork this targets): <https://github.com/GoodyOG/Iceraven-OLED>
- Upstream Iceraven: <https://github.com/fork-maintainers/iceraven-browser>
- Bitwarden Android: <https://github.com/bitwarden/android>
- Bitwarden's community allowlist: <https://github.com/bitwarden/android/blob/main/app/src/main/assets/fido2_privileged_community.json>
- Google's privileged-app guidance: <https://developer.android.com/identity/sign-in/credential-provider#obtain-allowlist>

## Verify before you install

1. Find the fingerprint of **your** Iceraven APK (needs Python 3):

   ```sh
   python3 apkcert.py /path/to/iceraven-patched-signed.apk
   ```

   The v2 and v3 lines must both read `79:13:7C:D3:...:39:E2:14`. If GoodyOG changes their
   signing key, this repo's patch is stale — stop and patch with your own fingerprint instead.

2. Inspect the patched Bitwarden APK:

   ```sh
   unzip -p Bitwarden-IceravenOLED-patched.apk assets/fido2_privileged_community.json \
     | jq '.apps[] | select(.info.package_name == "io.github.forkmaintainers.iceraven")'
   ```

   It must show `79:13:7C:D3:...:39:E2:14` and no other signature for that package.

3. Check the release checksum in `SHA256SUMS.txt`.

## Important: installing it will cost you local app data

The patched APK is signed with this project's own key, **not** Bitwarden's, so Android will refuse
to update your existing Bitwarden in place. You must uninstall it first, and its private data goes
with it. Android backup/restore does not cross a signing-key change.

- If your vault is **synced to a Bitwarden account**, confirm you can sign in with your master
  password and 2FA *before* uninstalling. Your vault returns on sign-in; settings, biometric unlock
  and the Autofill service toggle do not.
- If it is a **local-only vault**, export it first (Settings → Vault → Export Vault) and store the
  export safely, or the vault is gone permanently.

After installing, re-enable Autofill in Android settings and reconnect the browser extension.

## Patch it yourself

You do not need this project's build or signing key. From a stock Bitwarden universal APK:

1. Download the latest `com.x8bit.bitwarden.apk` from
   [Bitwarden releases](https://github.com/bitwarden/android/releases) and verify it against the
   published `.sha256.txt`.
2. Edit `OLD_FP` / `NEW_FP` in `patch_allowlist.py` to match **your** browser's real fingerprint,
   then run `python3 patch_allowlist.py`.
3. Align and sign with your own key (`apksigner`/`zipalign`, or the workflow in
   `.github/workflows/release.yml` as a model). Use a keystore you control and keep it — every
   future update must be signed with the same key.
4. Verify with `apkcert.py` and the `jq` command above.

## Automation

`.github/workflows/release.yml` runs daily and on demand. It:

- finds the newest upstream Bitwarden release that publishes a universal APK,
- verifies the download against Bitwarden's own checksum,
- checks that the latest Iceraven OLED release still has the pinned certificate,
- patches the allowlist, zipaligns and signs with the repository's stored key,
- verifies the result and publishes a release with checksums.

Bitwarden ships roughly every two weeks (25 universal releases in the 12 months to Nov 2026),
so expect a new patched build about twice a month. If you fork this repo you must supply your own
`KS_B64`, `KS_PASS` and `KS_KEY_PASS` Actions secrets; the workflow never prints them.

## Droid-ify / F-Droid source

The same workflow also publishes a signed **binary F-Droid repository** to Cloudflare R2. Add this
URL in Droid-ify (Manage Repositories → +):

```
https://fdroid.irmatt.com/fdroid/repo?fingerprint=A4:32:08:A7:7C:E0:AE:95:FA:27:69:23:F9:9A:1D:F0:21:C3:15:52:AB:52:D5:78:8C:D5:41:4A:F9:85:36:16
```

It contains two apps: the patched Bitwarden above and an unofficial **Iceraven OLED** mirror
(GoodyOG), both with their original/own APK signatures. The repository index is signed with a key
**separate** from the APK signing key; the fingerprint above is that repo key, not the Bitwarden
certificate. Droid-ify verifies the index signature against it, then each APK against its own
signer. The R2 bucket is served at `fdroid.irmatt.com` in the same Cloudflare account as `irmatt.com`.
