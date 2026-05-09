import React, { useEffect, useRef, useState } from 'react'
import api from '../api/axios'
import { createEventsSocket } from '../api/eventsWs'

export default function ProctorEventsPage() {
  const [me, setMe] = useState(null)
  const [error, setError] = useState('')
  const [wsState, setWsState] = useState('disconnected')
  const [events, setEvents] = useState([])

  const token = localStorage.getItem('access_token') || ''
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const wsRef = useRef(null)
  const reconnectRef = useRef(null)
  const backoffRef = useRef(500)

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
        if (msg?.type === 'event' || msg?.type === 'alert') {
          setEvents((prev) => [msg, ...prev].slice(0, 200))
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
    // initial load
    ;(async () => {
      try {
        const res = await api.get('/events/recent?limit=150')
        setEvents(res.data.map((ev) => ({ type: ev.suspicious ? 'alert' : 'event', event: ev })))
      } catch (err) {
        // ignore if forbidden for non-proctors
      }
    })()

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

  const badge = (severity) => {
    if (severity >= 80) return 'bg-red-100 text-red-700'
    if (severity >= 60) return 'bg-orange-100 text-orange-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h1 className="text-2xl font-semibold">Proctor Live Events</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time suspicious activity + alerts.</p>
          {error ? <div className="mt-4 text-sm text-red-600">{error}</div> : null}
          <div className="mt-4 text-sm text-gray-700 flex flex-wrap gap-6">
            <div>
              <span className="font-medium">You:</span> {me ? `${me.full_name} (${me.role})` : 'Loading...'}
            </div>
            <div>
              <span className="font-medium">WS:</span> {wsState}
            </div>
            <div>
              <span className="font-medium">Events:</span> {events.length}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <div className="space-y-3">
            {events.length === 0 ? (
              <div className="text-sm text-gray-600">No events yet.</div>
            ) : (
              events.map((item, idx) => {
                const ev = item.event || {}
                return (
                  <div key={idx} className="rounded-lg border p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-mono">{ev.event_type}</div>
                      <div className={`text-xs px-2 py-0.5 rounded-full ${badge(ev.severity || 0)}`}>
                        severity {ev.severity ?? 0}
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-gray-600">
                      student: <span className="font-mono">{ev.student_id}</span> · session:{' '}
                      <span className="font-mono">{ev.session_id}</span> · time:{' '}
                      <span className="font-mono">{String(ev.timestamp)}</span>
                    </div>
                    <pre className="mt-3 text-xs overflow-auto whitespace-pre-wrap">
                      {JSON.stringify(ev.details || {}, null, 2)}
                    </pre>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

