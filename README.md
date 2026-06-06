# MiCommunityBypass

Global-device helper scripts for Xiaomi Community unlock request timing (HyperOS 1/2/3), including token collection helpers for Windows and Linux.

## Credits

- Thanks to @dotKin
- Thanks to @nicogrimaldi (translation)
- Thanks to @redmugen (detailed guidance)
- Thanks to @bybestix (GetTokens updates/hotfix)
- Linux GetTokens variant thanks to @Jenna-66

## Important Notes

- Works with global devices and HyperOS 1/2/3 (including devices released with HyperOS 3).
- The Xiaomi Community app status can be misleading during this process.
- This workflow is intended to reduce quota-limit failures when sending unlock requests.
- Use desktop tools only: Chrome, Firefox, PowerShell/Terminal, Python.
- Do not use Windows mobile apps for this process.
- Run network diagnostics as Administrator when using Ping.bat.

## Repository Files

- NScript.py: main request-timing script.
- GetTokens.py: Windows token helper (automates login flow + token.txt + 4 script windows).
- gettokens_linux.py: Linux/GNOME token helper (same idea as Windows helper).
- token.txt: token slots used by NScript.py (rows 1-4).
- timeshift.txt: timing offsets used by NScript.py.
- Ping.bat: quick connectivity/packet-loss checks for NTP/Mi endpoints.

## Prerequisites

1. Python 3 installed and available in PATH.
2. Firefox installed.
3. Chrome installed.
4. Stable internet connection (VPN to US only if Xiaomi pages fail).

## Quick Start (Recommended: Automatic Token Flow)

### Windows

1. Open terminal in this folder.
2. Run:

```bash
py GetTokens.py
```

3. When prompted, provide the script path/name to run (for this repo use NScript.py).
4. Log in on Firefox when asked, then press OK.
5. Log in on Chrome when asked, then press OK.
6. The script writes token.txt automatically and opens 4 windows for NScript.py (rows 1-4).

### Linux (GNOME)

1. Open terminal in this folder.
2. Run:

```bash
python3 gettokens_linux.py
```

3. Log in on Firefox when asked, then press OK.
4. The script reads Firefox and Chrome cookies directly (no WebDriver required).
	It also supports Chromium-family browsers on Linux (Thorium, Chromium, Brave, Edge, Opera) for token retry/open steps.
5. If Chrome token is not found automatically, it opens a fallback login retry and allows manual token paste.
6. The script writes token.txt automatically and opens 4 terminals for NScript.py (rows 1-4).

## Manual Token Method (Fallback)

Use this only if automatic token scripts do not work.

1. In Firefox, log in to Xiaomi Community using one of:
- https://c.mi.com/global/
- https://new.c.mi.com/global/

2. Get cookie new_bbs_serviceToken from Firefox (Cookie Editor or equivalent).
3. Put this token into rows 1 and 3 of token.txt.

4. In Chrome, log in to Xiaomi Community and run this in the URL bar:

```javascript
javascript:(function(){var token=document.cookie.match(/popRunToken=([^;]+)/);if(token){prompt("Copy the token:", token[1]);}else{alert("Token not found");}})()
```

5. Put this token into rows 2 and 4 of token.txt.

## Running NScript Manually

You can also run manually in separate terminals:

```bash
python3 NScript.py
```

When prompted for token row number, run rows 1, 2, 3, and 4 in separate windows.

## Verification Steps (Very Important)

After script execution, always do this on the phone:

1. Settings -> Mi Account -> Sign out.
2. Reboot device.
3. Sign in again.
4. Settings -> Additional/Advanced settings -> Developer options -> Mi Unlock Status.
5. Link account to device.
6. Attempt unlock with Mi Unlock tool.

If account linking succeeds, enable OEM unlock and continue with Mi Unlock.

## Network Check

If requests fail or timeout frequently, run Ping.bat as Administrator and verify packet loss/latency to listed hosts.

## Useful Links

- L1: https://c.mi.com/global/
- L2: https://new.c.mi.com/global/
- L3: https://xiaomitools.com/download/mi-unlock-tool-v7-6-727-43/

## Troubleshooting

- If L1/L2 do not load, try a VPN endpoint in the United States.
- Refresh tokens shortly before use (recommended within 30 minutes).
- Keep all script windows open until around 00:00 China time.
- If the script name changes in future versions, provide the updated file name/path when GetTokens.py asks.

## Disclaimer

Use these scripts responsibly and only on devices/accounts you own or are authorized to manage. You are responsible for compliance with Xiaomi policies and local laws.
