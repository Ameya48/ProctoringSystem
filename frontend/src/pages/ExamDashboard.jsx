import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/axios'

function wsUrlFromApiBase(apiBase) {
  try {
    const u = new URL(apiBase)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    u.pathname = '/ws/sessions'
    u.search = ''
    u.hash = ''
    return u.toString()
  } catch {
    return 'ws://localhost:8000/ws/sessions'
  }
}

export default function ExamDashboard() {
  const [examId, setExamId] = useState('exam-101')
  const [me, setMe] = useState(null)
  const [activeSessions, setActiveSessions] = useState([])
  const [mySession, setMySession] = useState(null)
  const [events, setEvents] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const wsRef = useRef(null)
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const wsUrl = useMemo(() => wsUrlFromApiBase(apiBase), [apiBase])

  const refreshActive = async () => {
    const res = await api.get('/sessions/active')
    setActiveSessions(res.data)
    if (me?.role === 'student') {
      const mine = res.data.find((s) => s.student_id === me._id && s.exam_id === examId)
      setMySession(mine || null)
    }
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
    refreshActive().catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me, examId])

  useEffect(() => {
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        setEvents((prev) => [msg, ...prev].slice(0, 30))
        if (msg?.type === 'session_started' || msg?.type === 'session_ended') {
          refreshActive().catch(() => {})
        }
      } catch {
        // ignore
      }
    }
    ws.onerror = () => {
      // ignore noisy ws errors in dev
    }
    ws.onclose = () => {}

    // keepalive ping
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
        ws.close()
      } catch {
        // ignore
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsUrl])

  const startExam = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await api.post('/sessions/start', { exam_id: examId })
      setMySession(res.data)
      await refreshActive()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to start exam')
    } finally {
      setLoading(false)
    }
  }

  const endExam = async () => {
    if (!mySession?._id) return
    setError('')
    setLoading(true)
    try {
      const res = await api.post('/sessions/end', { session_id: mySession._id })
      setMySession(res.data)
      await refreshActive()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to end exam')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h1 className="text-2xl font-semibold">Exam Session Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Start/end exam sessions and see live updates.
          </p>

          {error ? <div className="mt-4 text-sm text-red-600">{error}</div> : null}

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-700">Exam ID</label>
              <input
                className="mt-1 w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring"
                value={examId}
                onChange={(e) => setExamId(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex gap-3">
              <button
                className="rounded-lg bg-black text-white px-4 py-2 font-medium disabled:opacity-50"
                onClick={startExam}
                disabled={loading || me?.role !== 'student'}
              >
                Start exam (student)
              </button>
              <button
                className="rounded-lg border px-4 py-2 font-medium disabled:opacity-50"
                onClick={endExam}
                disabled={loading || me?.role !== 'student' || !mySession || mySession.status !== 'active'}
              >
                End exam (student)
              </button>
              <div className="text-sm text-gray-600 flex items-center">
                WS: <span className="ml-2 font-mono text-xs">{wsUrl}</span>
              </div>
            </div>
          </div>

          <div className="mt-6 text-sm text-gray-700">
            <span className="font-medium">You:</span>{' '}
            {me ? `${me.full_name} (${me.role})` : 'Loading...'}
          </div>

          <div className="mt-3 text-sm">
            <span className="font-medium">My session:</span>{' '}
            {mySession ? (
              <span className="font-mono">
                {mySession._id} · {mySession.status} · {mySession.exam_id}
              </span>
            ) : (
              'None'
            )}
          </div>

          <div className="mt-4">
            <Link
              className={`text-sm underline ${mySession?._id ? '' : 'pointer-events-none opacity-50'}`}
              to={`/webcam?session_id=${encodeURIComponent(mySession?._id || '')}&exam_id=${encodeURIComponent(
                examId
              )}`}
            >
              Open Webcam Monitor
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-semibold">Active sessions</h2>
            <p className="text-sm text-gray-500 mt-1">
              Tracks active students via active sessions in MongoDB.
            </p>
            <div className="mt-4 space-y-2">
              {activeSessions.length === 0 ? (
                <div className="text-sm text-gray-600">No active sessions.</div>
              ) : (
                activeSessions.map((s) => (
                  <div key={s._id} className="rounded-lg border p-3">
                    <div className="text-sm font-mono">{s._id}</div>
                    <div className="text-xs text-gray-600 mt-1">
                      exam: <span className="font-mono">{s.exam_id}</span> · student:{' '}
                      <span className="font-mono">{s.student_id}</span>
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      status: <span className="font-medium">{s.status}</span> · started:{' '}
                      <span className="font-mono">{String(s.started_at)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-semibold">Live events</h2>
            <p className="text-sm text-gray-500 mt-1">WebSocket events from the backend.</p>
            <div className="mt-4 space-y-2">
              {events.length === 0 ? (
                <div className="text-sm text-gray-600">No events yet.</div>
              ) : (
                events.map((e, idx) => (
                  <div key={idx} className="rounded-lg border p-3">
                    <div className="text-xs font-mono">{e.type}</div>
                    <pre className="mt-2 text-xs overflow-auto whitespace-pre-wrap">
                      {JSON.stringify(e.session, null, 2)}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

