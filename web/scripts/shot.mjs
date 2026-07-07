// UI verification harness: launch system Chrome, optionally upload a label,
// toggle theme, set viewport, and screenshot. Usage:
//   node scripts/shot.mjs <url> <out.png> [--upload <file>] [--w 1200] [--h 800]
//   [--theme light|dark] [--wait 1200] [--manual] [--zoom]
import puppeteer from 'puppeteer-core'

const args = process.argv.slice(2)
const [url, out] = args
const opt = (name, def) => {
  const i = args.indexOf('--' + name)
  return i >= 0 ? args[i + 1] : def
}
const has = (name) => args.includes('--' + name)

const CHROME =
  process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe'

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'shell',
  args: ['--no-sandbox', '--hide-scrollbars', '--force-color-profile=srgb'],
})
const page = await browser.newPage()
await page.setViewport({
  width: Number(opt('w', 1280)),
  height: Number(opt('h', 820)),
  deviceScaleFactor: Number(opt('dpr', 1)),
})

const theme = opt('theme', null)
if (theme) {
  await page.evaluateOnNewDocument((t) => {
    localStorage.setItem('zlg-theme', t)
  }, theme)
}

await page.goto(url, { waitUntil: 'networkidle2' })

const upload = opt('upload', null)
if (upload) {
  const input = await page.waitForSelector('input[type=file]', { timeout: 5000 })
  await input.uploadFile(upload)
  // wait for the editor grid to appear + first render
  await page.waitForSelector('.grid', { timeout: 8000 }).catch(() => {})
  await new Promise((r) => setTimeout(r, Number(opt('wait', 1600))))
}

if (has('manual')) {
  // click the "Manual" crop segment
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Manual')
    btn?.click()
  })
  await new Promise((r) => setTimeout(r, 900))
}

if (has('zoom')) {
  await page.evaluate(() => document.querySelector('.viewport img')?.click())
  await new Promise((r) => setTimeout(r, 400))
}

await new Promise((r) => setTimeout(r, 300))
await page.screenshot({ path: out })
await browser.close()
console.log('shot ->', out)
