import React, { useEffect, useMemo, useRef, useState } from 'react'

function wsWebcamUrl(apiBaseUrl, { token, sessionId, examId }) {
  const base = apiBaseUrl || 'http://localhost:8000'
  const u = new URL(base)
  u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
  u.pathname = '/ws/webcam'
  u.searchParams.set('token', token)
  u.searchParams.set('session_id', sessionId)
  if (examId) u.searchParams.set('exam_id', examId)
  return u.toString()
}

export default function WebcamMonitor({ sessionId, examId }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const wsRef = useRef(null)
  const canvasRef = useRef(null)
  const sendTimerRef = useRef(null)
  const reconnectTimerRef = useRef(null)
  const backoffRef = useRef(500)

  const [status, setStatus] = useState('idle') // idle | camera_ready | connecting | streaming | error
  const [wsState, setWsState] = useState('disconnected')
  const [lastSaved, setLastSaved] = useState(null)
  const [error, setError] = useState('')

  const token = localStorage.getItem('access_token') || ''
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const wsUrl = useMemo(() => {
    if (!token || !sessionId) return null
    return wsWebcamUrl(apiBase, { token, sessionId, examId })
  }, [apiBase, token, sessionId, examId])

  const stopStreaming = () => {
    if (sendTimerRef.current) clearInterval(sendTimerRef.current)
    sendTimerRef.current = null
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
    reconnectTimerRef.current = null
    backoffRef.current = 500

    try {
      if (wsRef.current) wsRef.current.close()
    } catch {
      // ignore
    }
    wsRef.current = null
    setWsState('disconnected')

    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
      }
    } catch {
      // ignore
    }
    streamRef.current = null
    setStatus('idle')
  }

  const connectWs = () => {
    if (!wsUrl) {
      setError('Missing token or session id')
      setStatus('error')
      return
    }

    setWsState('connecting')
    setStatus('connecting')

    const ws = new WebSocket(wsUrl)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = () => {
      setWsState('connected')
      setStatus('streaming')
      backoffRef.current = 500
    }

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg?.type === 'saved') {
          setLastSaved({ at: msg.captured_at, size: msg.size_bytes })
        }
        if (msg?.type === 'error') {
          setError(msg.message || 'Server error')
        }
      } catch {
        // ignore non-json
      }
    }

    ws.onerror = () => {
      // keep UI calm; onclose handles reconnect
    }

    ws.onclose = () => {
      setWsState('disconnected')
      if (status === 'streaming' || status === 'connecting') scheduleReconnect()
    }
  }

  const scheduleReconnect = () => {
    if (reconnectTimerRef.current) return
    const delay = Math.min(backoffRef.current, 8000)
    reconnectTimerRef.current = setTimeout(() => {
      reconnectTimerRef.current = null
      backoffRef.current = Math.min(backoffRef.current * 1.8, 8000)
      connectWs()
    }, delay)
  }

  const captureAndSendFrame = async () => {
    const video = videoRef.current
    const ws = wsRef.current
    if (!video || !ws || ws.readyState !== WebSocket.OPEN) return
    if (video.readyState < 2) return

    const w = video.videoWidth || 640
    const h = video.videoHeight || 480
    const canvas = canvasRef.current
    if (!canvas) return
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d', { alpha: false })
    if (!ctx) return
    ctx.drawImage(video, 0, 0, w, h)

    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', 0.6) // low latency + smaller payload
    )
    if (!blob) return

    const buf = await blob.arrayBuffer()
    try {
      ws.send(buf)
    } catch {
      // if send fails, onclose will reconnect
    }
  }

  const start = async () => {
    setError('')
    if (!sessionId) {
      setError('Session id is required')
      setStatus('error')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 15, max: 30 } },
        audio: false
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setStatus('camera_ready')
      connectWs()

      // send at low fps for latency/bandwidth balance; server saves periodically
      if (sendTimerRef.current) clearInterval(sendTimerRef.current)
      sendTimerRef.current = setInterval(() => {
        captureAndSendFrame().catch(() => {})
      }, 250) // ~4 fps
    } catch (err) {
      setError(err?.message || 'Failed to access webcam (permission denied?)')
      setStatus('error')
    }
  }

  useEffect(() => {
    return () => stopStreaming()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="bg-white rounded-xl shadow p-6 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Webcam Monitoring</h2>
          <div className="text-sm text-gray-600 mt-1">
            <div>
              <span className="font-medium">Session:</span> <span className="font-mono">{sessionId || '-'}</span>
            </div>
            <div>
              <span className="font-medium">WebSocket:</span> {wsState}
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            className="rounded-lg bg-black text-white px-4 py-2 text-sm font-medium disabled-opacity-50"
            onClick={start}
            disabled={!sessionId || status === 'streaming' || status === 'connecting'}
          >
            Start monitoring
          </button>
          <button className="rounded-lg border px-4 py-2 text-sm font-medium" onClick={stopStreaming}>
            Stop
          </button>
        </div>
      </div>

      {error ? <div className="text-sm text-red-600">{error}</div> : null}

      <div className="grid grid-cols-1 md-grid-cols-2 gap-4 items-start">
        <div className="rounded-xl border bg-gray-50 overflow-hidden">
          <div className="w-full h-48 flex items-center justify-center text-gray-500">
            Webcam Disabled
          </div>
        </div>
        <div className="space-y-2">
          <div className="text-sm text-gray-700">
            <span className="font-medium">Status:</span> {status}
          </div>
          <div className="text-sm text-gray-700">
            <span className="font-medium">Last saved screenshot:</span>{' '}
            {lastSaved ? (
              <span className="font-mono text-xs">
                {lastSaved.at} · {lastSaved.size} bytes
              </span>
            ) : (
              '—'
            )}
          </div>
          <div className="text-xs text-gray-500">
            Frames are streamed over WebSocket for low latency; the backend saves periodic screenshots and writes metadata
            to MongoDB.
          </div>
        </div>
      </div>

      <canvas ref={canvasRef} className="hidden" />
    </div>
  )
}

