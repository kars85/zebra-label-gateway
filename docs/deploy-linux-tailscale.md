# Deploy on a Linux Docker host (with Tailscale)

Running the gateway on an always-on **Linux Docker host** (a NUC, a small server,
a Raspberry Pi, a VM) is the sturdiest setup for a print station — it doesn't
depend on a desktop being logged in, and Docker Desktop isn't involved at all.
Pairing it with **Tailscale** gives you HTTPS with real, automatically-trusted
certificates, so there's **no certificate to install on your iPhone** (unlike the
Caddy option in [tls-setup.md](tls-setup.md)).

## Part 1 — Run the gateway on a Linux host

### Install Docker Engine (once)

On the Linux host (Debian/Ubuntu shown; see docs.docker.com for other distros):

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"   # log out/in so you can run docker without sudo
```

This installs Docker Engine and the Compose plugin — **not** Docker Desktop.

### Get the gateway running

```bash
git clone https://github.com/kars85/zebra-label-gateway.git
cd zebra-label-gateway
cp .env.example .env
nano .env            # set ZLG_PRINTER_HOST (your printer's IP)
docker compose up -d --build
```

The app is now on `http://<linux-host-ip>:8080` (or whatever `ZLG_HOST_PORT` you
set). The host reaches the printer over your LAN exactly as a desktop would.

> **Ports are easy on Linux.** The Windows "port 8000 is reserved" problem
> doesn't exist here, and binding 80/443 works without special handling — which
> is what the TLS options below rely on.

### Managing it remotely

- **SSH** into the host and run `docker compose` commands there, **or**
- drive it from your workstation with a Docker context (no SSH into a shell
  needed for day-to-day):
  ```bash
  docker context create shop --docker "host=ssh://user@linux-host"
  docker --context shop compose ps
  ```

Update later with `git pull && docker compose up -d --build`.

## Part 2 — Expose it over Tailscale

This is the recommended way to reach the gateway from your iPhone/iPad and other
machines: you get a stable `https://label-gateway.<your-tailnet>.ts.net` address
with a **real certificate** — no trust profile to install, and it works from
anywhere on your tailnet, not just the local Wi-Fi.

The gateway ships a ready-made Tailscale sidecar (the `tailscale` Compose
profile) that fronts it. You just need an auth key and two toggles in the admin
console.

### In the Tailscale admin console (one-time)

1. **DNS** tab → enable **MagicDNS**.
2. **DNS** tab → enable **HTTPS Certificates** (this is what lets Tailscale issue
   the `*.ts.net` certificate).
3. **Settings → Keys → Generate auth key.** Make it **Reusable** (so the node can
   re-authenticate) and copy the key. Optionally tag it (e.g. `tag:label-gateway`)
   if your tailnet uses ACL tags.

### Configure and start

In `.env` on the Linux host:

```
TS_AUTHKEY=tskey-auth-xxxxxxxxxxxx      # the key you just generated
ZLG_TS_HOSTNAME=label-gateway           # becomes label-gateway.<tailnet>.ts.net
```

Then start the gateway **with the Tailscale profile** (instead of the Caddy `tls`
profile):

```bash
docker compose --profile tailscale up -d --build
```

The sidecar registers a node named `label-gateway` in your tailnet and proxies
its HTTPS to the gateway container. Give it a minute the first time (it has to
fetch the certificate), then confirm it's up:

```bash
docker compose logs -f tailscale     # look for "serve" running; Ctrl+C to exit
```

### Use it from your iPhone/iPad

1. Install the **Tailscale** app from the App Store and sign in to the same
   tailnet.
2. Open **Safari** and go to `https://label-gateway.<your-tailnet>.ts.net`
   (the admin console shows the exact name under **Machines**).
3. There's a padlock and **no warning** — tap **Share → Add to Home Screen**.

That's it: a real app icon, real HTTPS, reachable wherever the device has
Tailscale on.

### If you already run Tailscale as a container on this host

You have two clean choices:

- **Run this project's dedicated sidecar anyway** (recommended). It's a separate,
  self-contained tailnet node (`label-gateway`) and won't touch your existing
  Tailscale container. That's the `--profile tailscale` command above.
- **Reuse your existing Tailscale container.** Put it on the same Docker network
  as the gateway (`docker network connect zebra-label-gateway_default <your-ts>`),
  then add a serve handler inside it:
  ```bash
  docker exec <your-ts-container> \
    tailscale serve --bg --https 443 http://zebra-label-gateway:8000
  ```
  The app is then at `https://<that-container-hostname>.<tailnet>.ts.net`.

### Keep it private (don't use Funnel)

The setup above uses `tailscale serve`, which exposes the gateway **only to your
tailnet** — exactly right for a private print station. Do **not** use
`tailscale funnel`; that would publish it to the open internet.
