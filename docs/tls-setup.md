# Put the app on your iPhone or iPad

This guide gets the Label Gateway running as a real app on your Apple devices,
step by step. No prior experience needed — just follow along in order.

## Why there are extra steps

An iPhone will only "install" a web app when the connection is **secure** (the
little padlock — HTTPS). On the public internet a website gets that padlock
automatically. On your own home or shop network there's no automatic way to do
it, so the gateway includes a small helper (called **Caddy**) that creates its
own security certificate. You just have to tell your iPhone once, "I trust this
certificate," and then everything works like a normal app.

That "tell your iPhone to trust it" part is the only fiddly bit. Take it slowly
and it's about five minutes.

## Before you start

You'll need:

- [ ] **Docker Desktop** installed and running on the computer that will host the
      gateway (the same computer that reaches your printer).
- [ ] Your **printer's IP address** (e.g. `10.10.100.107`).
- [ ] Your iPhone/iPad and the computer on the **same Wi-Fi network**.

---

## Step 1 — Find this computer's IP address

Your phone needs an address to reach this computer. Open **PowerShell** on the
host computer and run:

```powershell
ipconfig
```

Look for **IPv4 Address** under your active Wi-Fi or Ethernet adapter — something
like `192.168.1.50`. Write it down; you'll use it in the next step and on your
phone.

## Step 2 — Enter your settings

In the project folder, make a copy of `.env.example` and name the copy `.env`,
then open `.env` in Notepad and fill in three things:

```
ZLG_PRINTER_HOST=10.10.100.107     # your printer's IP
ZLG_HOSTNAME=192.168.1.50          # this computer's IP from Step 1
ZLG_HOST_PORT=8080
```

Save the file.

## Step 3 — Start it

In PowerShell, from the project folder:

```powershell
docker compose --profile tls up -d --build
```

The first run takes a couple of minutes to build. When it finishes, the gateway
is running with HTTPS.

**Quick check on this computer:** open a browser and go to
`https://192.168.1.50` (your IP from Step 1). You'll see a **security warning**
— that's expected right now, because we haven't told this device to trust the
certificate yet. Click through it (Advanced → Continue) just to confirm the app
loads. We fix the warning next.

## Step 4 — Get the trust certificate

The gateway made a certificate file; copy it out so you can send it to your
phone. In PowerShell:

```powershell
docker cp zlg-caddy:/data/caddy/pki/authorities/local/root.crt zlg-root-ca.crt
```

This creates `zlg-root-ca.crt` in the current folder. That's the file your
devices need to trust.

## Step 5 — Trust the certificate on your iPhone/iPad

**Get the file onto the phone:** the easiest way is **AirDrop** it from a Mac,
or email `zlg-root-ca.crt` to yourself and open the attachment on the phone.

Then, on the iPhone/iPad, there are **two** parts (both required):

**Part A — install the profile**

1. When you open the file, iOS says *"Profile Downloaded."*
2. Go to **Settings** (you'll see *Profile Downloaded* near the top) → tap it →
   tap **Install** (top right) → enter your passcode → **Install** again.

**Part B — turn on full trust** (this is the step people miss)

3. Go to **Settings → General → About → Certificate Trust Settings**.
4. Find **"Caddy Local Authority"** and turn its switch **ON**. Confirm.

That's it — your phone now trusts the gateway.

> On a **Mac**: double-click `zlg-root-ca.crt`, add it to the **System**
> keychain, then find it in Keychain Access, open it, expand *Trust*, and set
> *When using this certificate: Always Trust*.
> On another **Windows PC**: run PowerShell as Administrator and
> `certutil -addstore -f Root zlg-root-ca.crt`.

## Step 6 — Install the app on your iPhone

1. Open **Safari** (it must be Safari) and go to `https://192.168.1.50` (your IP).
   This time there's **no warning** and you'll see the padlock. 🎉
2. Tap the **Share** button (the square with an up arrow).
3. Tap **Add to Home Screen** → **Add**.

You now have a **Label Gateway** icon on your home screen. It opens full-screen
like a normal app, remembers your printer, and works over your Wi-Fi.

---

## Troubleshooting

- **"Safari can't open the page" / it won't load on the phone.** The phone and
  computer must be on the same Wi-Fi. Double-check the IP from Step 1 (it can
  change after a reboot — consider a DHCP reservation in your router so it stays
  put).
- **Still getting a security warning on the phone after Step 5.** You probably
  did Part A but not Part B. Go back to **Settings → General → About →
  Certificate Trust Settings** and switch on *Caddy Local Authority*.
- **"Add to Home Screen" is missing.** You're not in Safari (Chrome/Firefox on
  iOS can't install web apps), or the page didn't load over HTTPS.
- **The computer's IP keeps changing.** Set a *DHCP reservation* for it in your
  router, or ask your network admin — then the address in `.env` and on your
  phone stays valid.

## Want to print straight from Mail or Files?

Build the one-tap **Apple Shortcut** — see [ios-shortcut.md](ios-shortcut.md).

## Easier option: Tailscale (no certificate to install)

Everything above is for a plain local network. If you run — or can run — the
gateway on a **Linux Docker host with Tailscale**, you get a real, automatically
trusted `https://…​.ts.net` address and can **skip Steps 4 and 5 entirely** (no
certificate file, no trust profile). Your iPhone just needs the Tailscale app.

The gateway ships a ready-made Tailscale sidecar for this. Full walkthrough —
including the two admin-console toggles and what to do if you already run
Tailscale as a container — is in
**[deploy-linux-tailscale.md](deploy-linux-tailscale.md).**

## Turning it off

```powershell
docker compose --profile tls down
```
