import React, { useEffect, useMemo, useRef, useState } from 'react'
import api from '../api/axios'
import { createEventsSocket } from '../api/eventsWs'
import StudentMonitoringCard from '../components/StudentMonitoringCard.jsx'

function wsSessionsUrl(apiBase) {
  try {
    const u = new URL(apiBase)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    u.pathname = '/ws/sessions'
    u.search = ''
    return u.toString()
  } catch {
    return 'ws://localhost:8000/ws/sessions'
  }
}

export default function ProctorDashboard() {
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const [me, setMe] = useState(null)
  const [error, setError] = useState('')

  const [activeSessions, setActiveSessions] = useState([])
  const [eventsFeed, setEventsFeed] = useState([]) // latest broadcast items
  const [alertsFeed, setAlertsFeed] = useState([])

  // maps: studentId -> { media_url, captured_at }
  const [webcamLatest, setWebcamLatest] = useState({})

  const token = localStorage.getItem('access_token') || ''

  const wsEventsRef = useRef(null)
  const wsSessionsRef = useRef(null)

  const refreshActive = async () => {
    const res = await api.get('/sessions/active')
    setActiveSessions(res.data || [])
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
    if (!me) return
    if (me.role !== 'proctor') {
      setError('Only proctors can access this dashboard.')
      return
    }
    refreshActive().catch(() => {})
    // initial alerts
    api
      .get('/events/active-alerts?minutes=30')
      .then((res) => setAlertsFeed((res.data?.alerts || []).map((ev) => ({ type: 'alert', event: ev }))))
      .catch(() => {})
  }, [me])

  useEffect(() => {
    if (!token) return
    // events websocket
    wsEventsRef.current = createEventsSocket({
      apiBaseUrl: apiBase,
      token,
      onMessage: (msg) => {
        if (msg?.type === 'event') {
          setEventsFeed((prev) => [msg, ...prev].slice(0, 100))
        }
        if (msg?.type === 'alert') {
          setAlertsFeed((prev) => [msg, ...prev].slice(0, 100))
        }
        if (msg?.type === 'webcam_saved') {
          const w = msg.webcam
          if (w?.student_id) {
            setWebcamLatest((prev) => ({
              ...prev,
              [w.student_id]: { media_url: w.media_url, captured_at: w.captured_at }
            }))
          }
        }
      }
    })

    // sessions websocket for status changes
    const ws = new WebSocket(wsSessionsUrl(apiBase))
    wsSessionsRef.current = ws
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg?.type === 'session_started' || msg?.type === 'session_ended') {
          refreshActive().catch(() => {})
        }
      } catch {
        // ignore
      }
    }
    ws.onerror = () => {}
    ws.onclose = () => {}

    const ping = setInterval(() => {
      try {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping')
      } catch {
        // ignore
      }
    }, 15000)

    return () => {
      clearInterval(ping)
      try {
        wsEventsRef.current?.close()
      } catch {}
      try {
        wsSessionsRef.current?.close()
      } catch {}
      wsEventsRef.current = null
      wsSessionsRef.current = null
    }
  }, [apiBase, token])

  // derived data for cards
  const cards = useMemo(() => {
    const sessions = activeSessions || []

    // latest event per student
    const latestEvent = {}
    const alertCount = {}
    const maxSeverity = {}

    for (const item of eventsFeed) {
      const ev = item?.event
      if (!ev?.student_id) continue
      if (!latestEvent[ev.student_id]) latestEvent[ev.student_id] = ev
    }

    for (const item of alertsFeed) {
      const ev = item?.event
      if (!ev?.student_id) continue
      alertCount[ev.student_id] = (alertCount[ev.student_id] || 0) + 1
      maxSeverity[ev.student_id] = Math.max(maxSeverity[ev.student_id] || 0, ev.severity || 0)
      if (!latestEvent[ev.student_id]) latestEvent[ev.student_id] = ev
    }

    return sessions.map((s) => {
      const sid = s.student_id
      return {
        studentId: sid,
        session: s,
        latestWebcamMediaUrl: webcamLatest?.[sid]?.media_url || '',
        lastEvent: latestEvent?.[sid] || null,
        alertCount: alertCount?.[sid] || 0,
        maxSeverity: maxSeverity?.[sid] || 0
      }
    })
  }, [activeSessions, alertsFeed, eventsFeed, webcamLatest])

  return (
    <div className="min-h-full bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="bg-white rounded-2xl shadow p-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold">Proctor Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">
                Active students, live events, suspicious alerts, and webcam thumbnails (real-time updates).
              </p>
              {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}
            </div>
            <div className="text-sm text-gray-700">
              <div>
                <span className="font-medium">You:</span> {me ? `${me.full_name} (${me.role})` : 'Loading...'}
              </div>
              <div className="mt-1 flex flex-wrap gap-3 text-xs text-gray-600">
                <span className="inline-flex items-center rounded-full border bg-gray-50 px-2 py-0.5">
                  active: {activeSessions.length}
                </span>
                <span className="inline-flex items-center rounded-full border bg-gray-50 px-2 py-0.5">
                  events: {eventsFeed.length}
                </span>
                <span className="inline-flex items-center rounded-full border bg-gray-50 px-2 py-0.5">
                  alerts: {alertsFeed.length}
                </span>
              </div>
              <button
                className="mt-3 rounded-lg border px-3 py-2 text-xs"
                onClick={() => refreshActive().catch(() => {})}
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Active students</h2>
              <div className="text-xs text-gray-500">Updates via WebSockets</div>
            </div>

            {cards.length === 0 ? (
              <div className="bg-white rounded-xl shadow p-6 text-sm text-gray-600">No active sessions.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {cards.map((c) => (
                  <StudentMonitoringCard key={c.session?._id || c.studentId} {...c} apiBase={apiBase} />
                ))}
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow p-6">
              <h2 className="text-lg font-semibold">Suspicious alerts</h2>
              <p className="text-sm text-gray-500 mt-1">Live alerts (severity-based).</p>
              <div className="mt-4 space-y-3 max-h-[28rem] overflow-auto">
                {alertsFeed.length === 0 ? (
                  <div className="text-sm text-gray-600">No alerts.</div>
                ) : (
                  alertsFeed.map((a, idx) => (
                    <div key={idx} className="rounded-xl border bg-red-50/40 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-xs font-mono">{a.event?.event_type}</div>
                        <div className="text-xs text-red-700 font-medium">sev {a.event?.severity ?? 0}</div>
                      </div>
                      <div className="mt-1 text-xs text-gray-700">
                        student: <span className="font-mono">{a.event?.student_id}</span>
                      </div>
                      <div className="mt-1 text-[11px] text-gray-500 font-mono">{String(a.event?.timestamp)}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow p-6">
              <h2 className="text-lg font-semibold">Live event feed</h2>
              <p className="text-sm text-gray-500 mt-1">Latest events across all students.</p>
              <div className="mt-4 space-y-3 max-h-[28rem] overflow-auto">
                {eventsFeed.length === 0 ? (
                  <div className="text-sm text-gray-600">No events yet.</div>
                ) : (
                  eventsFeed.map((e, idx) => (
                    <div key={idx} className="rounded-xl border p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-xs font-mono">{e.event?.event_type}</div>
                        <div className="text-[11px] text-gray-500 font-mono">{String(e.event?.timestamp)}</div>
                      </div>
                      <div className="mt-1 text-xs text-gray-700">
                        student: <span className="font-mono">{e.event?.student_id}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

