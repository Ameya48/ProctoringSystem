import React, { useEffect, useRef, useState } from 'react'
import api from '../api/axios'
import { createEventsSocket } from '../api/eventsWs'
import useScreenMonitoring from '../hooks/useScreenMonitoring'

export default function ScreenMonitorPage() {
  const [me, setMe] = useState(null)
  const [error, setError] = useState('')
  const [wsState, setWsState] = useState('disconnected')
  const [events, setEvents] = useState([])
  const [sessionId, setSessionId] = useState('')
  const [examId, setExamId] = useState('exam-101')

  const token = localStorage.getItem('access_token') || ''
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const wsRef = useRef(null)
  const reconnectRef = useRef(null)
  const backoffRef = useRef(500)

  const { screenStream, setEmitter, startScreenShare, stopScreenShare } = useScreenMonitoring({ idleMs: 15000 })

  const pushEventLocal = (evt) => {
    setEvents((prev) => [evt, ...prev].slice(0, 50))
  }

  const sendEvent = (payload) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    try {
      ws.send(JSON.stringify(payload))
    } catch {
      // ignore
    }
  }

  const connectWs = () => {
    if (!token) return
    setWsState('connecting')
    wsRef.current = createEventsSocket({
      apiBaseUrl: apiBase,
      token,
      onOpen: () => {
        setWsState('connected')
        backoffRef.current = 500
      },
      onClose: () => {
        setWsState('disconnected')
        scheduleReconnect()
      },
      onMessage: (msg) => {
        // proctors receive broadcasts; students also see their own echoes
        if (msg?.type === 'event' || msg?.type === 'alert') {
          pushEventLocal(msg)
        }
      }
    })
  }

  const scheduleReconnect = () => {
    if (reconnectRef.current) return
    const delay = Math.min(backoffRef.current, 8000)
    reconnectRef.current = setTimeout(() => {
      reconnectRef.current = null
      backoffRef.current = Math.min(backoffRef.current * 1.8, 8000)
      connectWs()
    }, delay)
  }

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const res = await api.get('/auth/me')
        if (!mounted) return
        setMe(res.data)
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load profile')
      }
    })()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    connectWs()
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      reconnectRef.current = null
      try {
        wsRef.current?.close()
      } catch {
        // ignore
      }
      wsRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setEmitter(({ event_type, details }) => {
      const payload = {
        session_id: sessionId,
        exam_id: examId,
        event_type,
        timestamp: new Date().toISOString(),
        details
      }
      pushEventLocal({ type: 'local', event: payload })
      if (sessionId) sendEvent(payload)
    })
  }, [examId, pushEventLocal, sessionId, setEmitter])

  const start = async () => {
    setError('')
    try {
      await startScreenShare()
    } catch (err) {
      setError(err?.message || 'Failed to start screen sharing (permission denied?)')
    }
  }

  const stop = () => stopScreenShare()

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h1 className="text-2xl font-semibold">Screen Monitoring</h1>
          <p className="text-sm text-gray-500 mt-1">
            Detects tab switching, fullscreen exit, minimize (blur), and inactivity; sends suspicious events to backend.
          </p>
          {error ? <div className="mt-4 text-sm text-red-600">{error}</div> : null}

          <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">Session ID (required to send)</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="Paste your active session id"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Exam ID</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring"
                value={examId}
                onChange={(e) => setExamId(e.target.value)}
              />
            </div>
            <div className="flex gap-3">
              <button
                className="rounded-lg bg-black text-white px-4 py-2 font-medium disabled:opacity-50"
                onClick={start}
                disabled={!me || me.role !== 'student'}
              >
                Start screen share
              </button>
              <button className="rounded-lg border px-4 py-2 font-medium" onClick={stop}>
                Stop
              </button>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-700 flex flex-wrap gap-6">
            <div>
              <span className="font-medium">User:</span> {me ? `${me.full_name} (${me.role})` : 'Loading...'}
            </div>
            <div>
              <span className="font-medium">WS:</span> {wsState}
            </div>
            <div>
              <span className="font-medium">Screen:</span> {screenStream ? 'sharing' : 'not sharing'}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold">Real-time events</h2>
          <p className="text-sm text-gray-500 mt-1">
            Students send events; proctors receive broadcasts and alerts.
          </p>
          <div className="mt-4 space-y-2">
            {events.length === 0 ? (
              <div className="text-sm text-gray-600">No events yet.</div>
            ) : (
              events.map((e, idx) => (
                <div key={idx} className="rounded-lg border p-3">
                  <div className="text-xs font-mono">{e.type}</div>
                  <pre className="mt-2 text-xs overflow-auto whitespace-pre-wrap">
                    {JSON.stringify(e, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

