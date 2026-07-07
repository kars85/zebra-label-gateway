import '@fontsource-variable/inter'
import '@fontsource/jetbrains-mono/400.css'
import '@fontsource/jetbrains-mono/500.css'
import './styles/tokens.css'
import './styles/global.css'
import { mount } from 'svelte'
import App from './App.svelte'

// Register the service worker for offline app-shell + installability.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      /* SW needs a secure context (https or localhost); ignore otherwise */
    })
  })
}

export default mount(App, { target: document.getElementById('app')! })
