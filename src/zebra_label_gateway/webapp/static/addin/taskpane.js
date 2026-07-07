/* Word add-in task pane: export the document as PDF and send it to the gateway.
 * Hosted on the gateway, so /api/* calls are same-origin (no CORS). The gateway
 * address box only matters if this pane is hosted somewhere other than the
 * gateway; blank means "same origin as this page". */

let gatewayBase = ''

Office.onReady((info) => {
  if (info.host !== Office.HostType.Word) {
    setStatus('This add-in runs in Microsoft Word.', 'err')
    return
  }
  const saved = localStorage.getItem('zlg-gateway') || ''
  document.getElementById('gw').value = saved
  gatewayBase = saved
  document.getElementById('gw').addEventListener('change', (e) => {
    gatewayBase = e.target.value.trim().replace(/\/$/, '')
    localStorage.setItem('zlg-gateway', gatewayBase)
  })
  document.getElementById('send').onclick = () => run(false)
  document.getElementById('print').onclick = () => run(true)
  document.getElementById('send').disabled = false
  document.getElementById('print').disabled = false
})

function setStatus(msg, kind) {
  const el = document.getElementById('status')
  el.textContent = msg
  el.className = kind || ''
}

function getPdfBytes() {
  return new Promise((resolve, reject) => {
    Office.context.document.getFileAsync(
      Office.FileType.Pdf,
      { sliceSize: 65536 },
      (result) => {
        if (result.status !== Office.AsyncResultStatus.Succeeded) return reject(result.error)
        const file = result.value
        const count = file.sliceCount
        const slices = new Array(count)
        let received = 0
        for (let i = 0; i < count; i++) {
          file.getSliceAsync(i, (sr) => {
            if (sr.status !== Office.AsyncResultStatus.Succeeded) {
              file.closeAsync()
              return reject(sr.error)
            }
            slices[sr.value.index] = sr.value.data
            if (++received === count) {
              file.closeAsync()
              const total = slices.reduce((n, s) => n + s.length, 0)
              const bytes = new Uint8Array(total)
              let offset = 0
              for (const s of slices) {
                bytes.set(s, offset)
                offset += s.length
              }
              resolve(bytes)
            }
          })
        }
      },
    )
  })
}

async function run(doPrint) {
  const buttons = document.querySelectorAll('button')
  buttons.forEach((b) => (b.disabled = true))
  setStatus('Rendering document…')
  try {
    const bytes = await getPdfBytes()
    const form = new FormData()
    form.append('file', new Blob([bytes], { type: 'application/pdf' }), 'document.pdf')

    const uploadRes = await fetch(gatewayBase + '/api/upload', { method: 'POST', body: form })
    if (!uploadRes.ok) throw new Error('Upload failed (' + uploadRes.status + ')')
    const up = await uploadRes.json()
    let msg = `Uploaded (${up.width}×${up.height}, ${up.pages} page(s)).`

    if (doPrint) {
      const printRes = await fetch(gatewayBase + '/api/print', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: up.id, profile: 'generic_4x6' }),
      })
      const pr = await printRes.json()
      msg += '\n' + (pr.detail || (printRes.ok ? 'Printed.' : 'Print failed.'))
    } else {
      msg += '\nReview and print it in the Label Gateway.'
    }
    setStatus(msg, 'ok')
  } catch (e) {
    setStatus('Failed: ' + (e.message || e), 'err')
  } finally {
    buttons.forEach((b) => (b.disabled = false))
  }
}
