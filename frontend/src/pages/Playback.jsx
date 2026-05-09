import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/axios'

function absUrl(apiBase, path) {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const base = apiBase || 'http://localhost:8000'
  return `${base}${path.startsWith('/') ? '' : '/'}${path}`
}

export default function PlaybackPage() {
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const [params] = useSearchParams()
  const recordingId = params.get('recording_id') || ''

  const videoRef = useRef(null)
  const [error, setError] = useState('')
  const [recording, setRecording] = useState(null)
  const [list, setList] = useState([])

  useEffect(() => {
    setError('')
    ;(async () => {
      try {
        if (recordingId) {
          const res = await api.get(`/recordings/${recordingId}`)
          setRecording(res.data)
        } else {
          setRecording(null)
        }
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load recording')
      }
    })()
  }, [recordingId])

  useEffect(() => {
    ;(async () => {
      try {
        // students get mine; proctors can switch to /recordings/all if desired later
        const res = await api.get('/recordings/mine')
        setList(res.data || [])
      } catch {
        setList([])
      }
    })()
  }, [])

  const mediaUrl = useMemo(() => absUrl(apiBase, recording?.media_url), [apiBase, recording?.media_url])

  const jump = (sec) => {
    const v = videoRef.current
    if (!v) return
    v.currentTime = Math.max(0, Number(sec) || 0)
    v.play().catch(() => {})
  }

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl shadow p-6">
          <h1 className="text-2xl font-semibold">Recording Playback</h1>
          <p className="text-sm text-gray-500 mt-1">Play uploaded webcam recordings and jump to flagged timestamps.</p>
          {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-2xl shadow p-6">
              <div className="text-sm text-gray-600">Video playback disabled.</div>

              {recording ? (
                <div className="mt-4 text-xs text-gray-600 flex flex-wrap gap-4">
                  <div>
                    <span className="font-medium">id:</span> <span className="font-mono">{recording._id}</span>
                  </div>
                  <div>
                    <span className="font-medium">session:</span>{' '}
                    <span className="font-mono">{recording.session_id}</span>
                  </div>
                  <div>
                    <span className="font-medium">size:</span> {recording.size_bytes} bytes
                  </div>
                  <div>
                    <span className="font-medium">status:</span> {recording.status}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="bg-white rounded-2xl shadow p-6">
              <h2 className="text-lg font-semibold">Flagged timestamps</h2>
              <p className="text-sm text-gray-500 mt-1">
                Generated from suspicious events during the recording window.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {(recording?.flagged_seconds || []).length === 0 ? (
                  <div className="text-sm text-gray-600">No flags.</div>
                ) : (
                  recording.flagged_seconds.map((sec, idx) => (
                    <button
                      key={`${sec}-${idx}`}
                      className="rounded-full border bg-gray-50 px-3 py-1 text-xs font-mono hover:bg-gray-100"
                      onClick={() => jump(sec)}
                    >
                      {sec}s
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-white rounded-2xl shadow p-6">
              <h2 className="text-lg font-semibold">My recordings</h2>
              <p className="text-sm text-gray-500 mt-1">Open a recording by appending `?recording_id=...`.</p>
              <div className="mt-4 space-y-2 max-h-[32rem] overflow-auto">
                {list.length === 0 ? (
                  <div className="text-sm text-gray-600">No recordings yet.</div>
                ) : (
                  list.map((r) => (
                    <a
                      key={r._id}
                      className={`block rounded-xl border p-3 hover:bg-gray-50 ${
                        r._id === recordingId ? 'border-black' : ''
                      }`}
                      href={`/playback?recording_id=${encodeURIComponent(r._id)}`}
                    >
                      <div className="text-xs text-gray-500">recording</div>
                      <div className="text-sm font-mono">{r._id}</div>
                      <div className="mt-1 text-xs text-gray-600">
                        session: <span className="font-mono">{r.session_id}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-600">
                        flags: <span className="font-mono">{(r.flagged_seconds || []).length}</span> · status:{' '}
                        <span className="font-medium">{r.status}</span>
                      </div>
                    </a>
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

