import puppeteer from 'puppeteer-core'

const url = process.argv[2] || 'http://localhost:5180/'
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe'

const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'shell', args: ['--no-sandbox'] })
const page = await browser.newPage()
await page.goto(url, { waitUntil: 'networkidle2' })

// manifest reachable + parseable
const manifest = await page.evaluate(async () => {
  const res = await fetch('/manifest.webmanifest')
  return res.ok ? await res.json() : null
})

// service worker registers (localhost is a secure context)
await new Promise((r) => setTimeout(r, 1500))
const sw = await page.evaluate(async () => {
  if (!('serviceWorker' in navigator)) return 'unsupported'
  const reg = await navigator.serviceWorker.getRegistration()
  return reg ? (reg.active ? 'active' : reg.installing ? 'installing' : 'registered') : 'none'
})

const swjs = await page.evaluate(async () => {
  const res = await fetch('/sw.js')
  return { ok: res.ok, allowed: res.headers.get('service-worker-allowed'), type: res.headers.get('content-type') }
})

console.log(JSON.stringify({
  manifest_name: manifest?.name,
  manifest_icons: manifest?.icons?.length,
  manifest_display: manifest?.display,
  sw_state: sw,
  sw_served: swjs,
}, null, 2))
await browser.close()
