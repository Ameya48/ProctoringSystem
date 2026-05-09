function wsEventsUrl(apiBaseUrl, token) {
  const base = apiBaseUrl || 'http://localhost:8000'
  const u = new URL(base)
  u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
  u.pathname = '/ws/events'
  u.searchParams.set('token', token)
  return u.toString()
}

export function createEventsSocket({ apiBaseUrl, token, onMessage, onOpen, onClose }) {
  const url = wsEventsUrl(apiBaseUrl, token)
  const ws = new WebSocket(url)

  ws.onopen = () => onOpen && onOpen()
  ws.onclose = () => onClose && onClose()
  ws.onerror = () => {
    // keep quiet; close triggers reconnect
  }
  ws.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data)
      onMessage && onMessage(msg)
    } catch {
      // ignore
    }
  }

  return ws
}

