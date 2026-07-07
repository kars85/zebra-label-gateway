# LAN HTTPS (Caddy internal CA)

iOS needs a **secure context** (HTTPS) to install a PWA or run a service worker —
`http://<ip>:port` will not register one. On a LAN with no public domain, the
gateway ships a Caddy sidecar that issues a certificate from its own internal CA.
You install and trust that CA root once per device.

## 1. Start the gateway with TLS

Pick the hostname your devices will use — an mDNS name like `gateway.local`, or
the Docker host's LAN IP — and start the `tls` profile:

```bash
ZLG_HOSTNAME=gateway.local ZLG_PRINTER_HOST=10.10.100.107 \
  docker compose --profile tls up -d --build
```

Caddy now serves `https://gateway.local` (and redirects HTTP→HTTPS) and proxies
to the app. If you used an IP instead, browse `https://<that-ip>`.

> mDNS: `gateway.local` resolves automatically on Apple devices if the Docker
> host advertises it (Bonjour/avahi). If it doesn't resolve, use the host's IP
> as `ZLG_HOSTNAME`, or add a `hosts` entry.

## 2. Export the CA root

```bash
docker cp zlg-caddy:/data/caddy/pki/authorities/local/root.crt ./zlg-root-ca.crt
```

## 3. Trust it on each device

- **iPhone / iPad:** AirDrop or email `zlg-root-ca.crt` to the device → open it →
  Settings shows *Profile Downloaded* → Install. Then
  **Settings → General → About → Certificate Trust Settings** → enable full trust
  for the "Caddy Local Authority" root. (Both steps are required on iOS.)
- **macOS:** double-click → add to the System keychain → set to *Always Trust*.
- **Windows:** `certutil -addstore -f Root zlg-root-ca.crt` (elevated).

## 4. Install the app on iOS

Open `https://gateway.local` in **Safari** → Share → **Add to Home Screen**. It
launches standalone (its own icon, no browser chrome), works offline for the
app shell, and prints over your LAN.

## Alternative: Tailscale

If the shop already uses Tailscale, `tailscale serve https / http://localhost:8000`
gives a publicly-valid `*.ts.net` certificate with **no** CA-trust step. Use that
instead of the Caddy sidecar if you prefer zero cert installation.
