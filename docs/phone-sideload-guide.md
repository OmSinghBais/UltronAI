# ATLAS Phone Companion — Physical Device Sideload Guide

> **Who this is for:** Person C (Phone Track)  
> **Time required:** ~15 minutes  
> **What you need:** Android phone, USB cable, laptop with the repo checked out

---

## Prerequisites Checklist

Before starting, confirm you have all of these:

- [ ] Android phone (Android 9+)
- [ ] USB-A or USB-C cable that supports **data transfer** (not charge-only)
- [ ] Repo cloned and on `main` branch
- [ ] `adb` installed and on PATH (comes with Android SDK `platform-tools`)
- [ ] APK already built (`./gradlew assembleDebug` completed successfully)

Verify `adb` is available:
```bash
adb --version
# Expected: Android Debug Bridge version 1.0.41 (or higher)
```

Verify the APK exists:
```bash
ls -lh atlas-phone-companion/app/build/outputs/apk/debug/app-debug.apk
# Expected: -rw-r--r-- ... 5.4M ... app-debug.apk
```

If the APK is missing, build it first:
```bash
cd atlas-phone-companion
./gradlew assembleDebug
cd ..
```

---

## Step 1 — Enable Developer Mode on the Phone

1. Open **Settings** on your Android phone
2. Scroll down → tap **About phone**
3. Find **Build number** (may be under *Software information*)
4. **Tap "Build number" 7 times rapidly**
5. You will see: *"You are now a developer!"*
6. Go back to **Settings** → you will now see **Developer options**

> [!NOTE]
> On some brands the path differs:
> - **Samsung**: Settings → About phone → Software information → Build number
> - **Xiaomi/MIUI**: Settings → About phone → MIUI version (tap 7 times)
> - **OnePlus**: Settings → About device → Build number

---

## Step 2 — Enable USB Debugging

1. Go to **Settings → Developer options**
2. Toggle **Developer options** ON (top of the page)
3. Scroll down and toggle **USB debugging** ON
4. Tap **OK** on the confirmation dialog

---

## Step 3 — Connect Phone to Laptop via USB

1. Plug the phone into your laptop with the USB cable
2. On the phone, a dialog will appear:
   ```
   Allow USB debugging?
   RSA key fingerprint: XX:XX:XX:...
   [ ] Always allow from this computer
   [CANCEL]  [ALLOW]
   ```
3. Check **"Always allow from this computer"**
4. Tap **ALLOW**
5. On the phone's notification bar, tap the USB notification → select **File Transfer** (MTP) mode

---

## Step 4 — Verify Phone is Detected

Run on laptop:
```bash
adb devices
```

Expected output:
```
List of devices attached
XXXXXXXXXXXXXXXX    device
```

> [!WARNING]
> If you see `unauthorized` instead of `device`:
> - Unplug and replug the cable
> - Check the phone screen for the "Allow USB debugging?" dialog again
> - Tap ALLOW

> [!WARNING]
> If you see nothing (empty list):
> - Try a different USB cable (many cables are charge-only)
> - Try a different USB port on your laptop
> - Ensure USB mode on the phone is set to "File Transfer", not "Charging only"

---

## Step 5 — Install the APK

```bash
adb install atlas-phone-companion/app/build/outputs/apk/debug/app-debug.apk
```

Expected output:
```
Performing Streamed Install
Success
```

> [!NOTE]
> If you see `INSTALL_FAILED_ALREADY_EXISTS`, the app is already installed.  
> Force-reinstall with:
> ```bash
> adb install -r atlas-phone-companion/app/build/outputs/apk/debug/app-debug.apk
> ```

> [!WARNING]
> If you see `INSTALL_FAILED_UPDATE_INCOMPATIBLE`, uninstall the old version first:
> ```bash
> adb uninstall com.atlas.companion
> adb install atlas-phone-companion/app/build/outputs/apk/debug/app-debug.apk
> ```

---

## Step 6 — Grant Accessibility Service Permission (MANUAL — Cannot Be Scripted)

> [!IMPORTANT]
> This step **must be done by hand** on the phone. Android deliberately blocks
> accessibility grants via ADB for security reasons.

1. Open **Settings** on the phone
2. Go to **Accessibility** (may be under *Additional settings* on some brands)
3. Scroll down to **Downloaded apps** or **Installed services**
4. Tap **ATLAS Companion**
5. Toggle the service **ON**
6. Tap **ALLOW** on the confirmation dialog:
   ```
   Allow ATLAS Companion to observe actions and retrieve window content?
   [DENY]  [ALLOW]
   ```

Verify the service started — check logcat:
```bash
adb logcat -s AtlasAccessibility
```
Expected log line:
```
I AtlasAccessibility: AccessibilityControlService connected.
I AtlasWSServer:      WebSocket server started on port 8765
```
Press `Ctrl+C` to stop logcat.

---

## Step 7 — Grant "Draw Over Other Apps" Permission (MANUAL)

1. Go to **Settings → Apps → ATLAS Companion**
2. Tap **Display over other apps** (or *Appear on top*)
3. Toggle **Allow display over other apps** ON

---

## Step 8 — Find the Phone's Local IP Address

Both the laptop and phone must be on the **same Wi-Fi network**.

**Method A — via ADB (easiest):**
```bash
adb shell ip route | grep wlan
```
Look for the `src` address:
```
192.168.1.0/24 dev wlan0 proto kernel scope link src 192.168.1.105
```
Your phone IP is `192.168.1.105` (example — yours will differ).

**Method B — on the phone:**
Settings → About phone → Status → IP address

---

## Step 9 — Configure `.env` on the Laptop

Edit (or create) the `.env` file in the project root:
```bash
# .env
PHONE_IP=192.168.1.105      # ← replace with your phone's actual IP
PHONE_PORT=8765
```

Verify settings load correctly:
```bash
.venv313/bin/python -c "from config.settings import settings; print(settings.phone_ip, settings.phone_port)"
# Expected: 192.168.1.105 8765
```

---

## Step 10 — Run the Live End-to-End Test

USB cable can now be **unplugged** — all further communication is over Wi-Fi.

Run the smoke test from the project root:
```bash
.venv313/bin/python - <<'EOF'
import asyncio
from phone.bridge_server import PhoneController

async def main():
    pc = PhoneController()
    print("Connecting to phone...")
    await pc.connect()
    print("Connected!\n")

    print("--- read_screen ---")
    screen = await pc.read_screen()
    print(screen)

    print("\n--- scroll down ---")
    res = await pc.scroll("down")
    print(res)

    print("\n--- tap centre ---")
    res = await pc.tap(540, 960)
    print(res)

    await pc.disconnect()
    print("\nDone.")

asyncio.run(main())
EOF
```

Expected output (approximate):
```
Connecting to phone...
Connected!

--- read_screen ---
{'status': 'ok', 'elements': [{'text': 'Clock', 'class': '...', 'bounds': [...], 'clickable': True}, ...]}

--- scroll down ---
{'status': 'ok', 'action': 'scroll', 'direction': 'down'}

--- tap centre ---
{'status': 'ok', 'action': 'tap'}

Done.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Connection refused` on port 8765 | Open ATLAS Companion on the phone — the WebSocket server only starts when the Accessibility Service is active |
| `Connection timed out` | Check both devices are on the **same Wi-Fi** — mobile data bypass won't work |
| Screen elements list is empty | The Accessibility Service may have been killed. Re-enable it in Settings → Accessibility |
| `adb: command not found` | Add Android SDK `platform-tools/` to your `PATH` |
| App crashes on install | Run `adb logcat \| grep com.atlas.companion` to see the crash log |
| Phone shows `Offline` in `adb devices` | Restart ADB: `adb kill-server && adb start-server` |

---

## Ongoing Debugging (adb logcat)

```bash
# All ATLAS logs
adb logcat -s AtlasAccessibility AtlasWSServer

# Full logcat filtered to the app
adb logcat | grep com.atlas.companion

# Clear logcat buffer before a fresh test run
adb logcat -c
```

---

## What Happens at Runtime (No USB Required After Step 5)

```
Phone (Wi-Fi)                       Laptop (Wi-Fi)
─────────────────────────────────   ──────────────────────────────
ATLAS Companion app                 core/orchestrator.py
  └─ AccessibilityControlService  ◄────── PhoneController.connect()
       └─ CompanionWebSocketServer         │
            ws://192.168.1.105:8765        ├─ scroll("down")
                                           ├─ tap(540, 960)
                                           ├─ read_screen()
                                           └─ open_app("com.whatsapp")
```

ADB is completely **out of the runtime path** — it was only used once for the install.
