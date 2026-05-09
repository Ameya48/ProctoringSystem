import React, { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import WebcamMonitor from '../components/WebcamMonitor.jsx'
import api from '../api/axios'

export default function WebcamPage() {
  const [params] = useSearchParams()
  const sessionId = params.get('session_id') || ''
  const examId = params.get('exam_id') || ''
  const [recording, setRecording] = useState(null)
  const [recError, setRecError] = useState('')
  const [recStatus, setRecStatus] = useState('idle') // idle | recording | uploading

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const startedAtRef = useRef(null)

  const startRecording = async () => {
    setRecError('')
    if (!sessionId) {
      setRecError('Session id is required to record.')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp8')
        ? 'video/webm;codecs=vp8'
        : 'video/webm'
      const mr = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mr
      chunksRef.current = []
      startedAtRef.current = Date.now()

      const init = await api.post('/recordings/init', { session_id: sessionId, exam_id: examId, mime_type: mimeType })
      setRecording({ recording_id: init.data.recording_id, mime_type: mimeType })

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data)
      }
      mr.onstop = async () => {
        try {
          setRecStatus('uploading')
          await uploadRecording(init.data.recording_id, chunksRef.current, mimeType)
        } catch (e) {
          setRecError(e?.response?.data?.detail || e?.message || 'Upload failed')
        } finally {
          setRecStatus('idle')
          // stop tracks
          try {
            stream.getTracks().forEach((t) => t.stop())
          } catch {}
        }
      }

      setRecStatus('recording')
      // timeslice -> collect chunks incrementally (still uploaded after stop in this MVP)
      mr.start(1000)
    } catch (e) {
      setRecError(e?.message || 'Failed to start recording')
      setRecStatus('idle')
    }
  }

  const stopRecording = () => {
    try {
      mediaRecorderRef.current?.stop()
    } catch {
      // ignore
    }
  }

  const uploadRecording = async (recordingId, blobs, mimeType) => {
    // Efficient large upload: slice final Blob into chunks and upload sequentially with offset.
    const full = new Blob(blobs, { type: mimeType || 'video/webm' })
    const chunkSize = 1024 * 1024 // 1MB
    let offset = 0

    while (offset < full.size) {
      const slice = full.slice(offset, offset + chunkSize)
      const form = new FormData()
      form.append('offset', String(offset))
      form.append('chunk', slice, `chunk-${offset}.bin`)
      await api.post(`/recordings/${recordingId}/chunk`, form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      offset += slice.size
    }

    const durationSeconds = startedAtRef.current ? (Date.now() - startedAtRef.current) / 1000 : undefined
    await api.post('/recordings/complete', {
      recording_id: recordingId,
      duration_seconds: durationSeconds
    })
  }

  useEffect(() => {
    return () => {
      try {
        mediaRecorderRef.current?.stop()
      } catch {}
    }
  }, [])

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h1 className="text-2xl font-semibold">Webcam Monitor</h1>
          <p className="text-sm text-gray-500 mt-1">
            Streams webcam frames to the backend via WebSocket and saves periodic screenshots.
          </p>
          <div className="mt-4 text-sm text-gray-700">
            <div>
              <span className="font-medium">session_id:</span> <span className="font-mono">{sessionId || '-'}</span>
            </div>
            <div>
              <span className="font-medium">exam_id:</span> <span className="font-mono">{examId || '-'}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold">Webcam Recording (MVP)</h2>
          <p className="text-sm text-gray-500 mt-1">Records locally and uploads in chunks to backend storage.</p>
          {recError ? <div className="mt-3 text-sm text-red-600">{recError}</div> : null}
          <div className="mt-4 flex items-center gap-3">
            <button
              className="rounded-lg bg-black text-white px-4 py-2 text-sm font-medium disabled:opacity-50"
              onClick={startRecording}
              disabled={!sessionId || recStatus !== 'idle'}
            >
              Start recording
            </button>
            <button
              className="rounded-lg border px-4 py-2 text-sm font-medium disabled:opacity-50"
              onClick={stopRecording}
              disabled={recStatus !== 'recording'}
            >
              Stop
            </button>
            <div className="text-sm text-gray-600">
              status: <span className="font-medium">{recStatus}</span>
            </div>
            {recording?.recording_id ? (
              <div className="text-xs text-gray-500 font-mono">id: {recording.recording_id}</div>
            ) : null}
          </div>
        </div>

        <WebcamMonitor sessionId={sessionId} examId={examId} />
      </div>
    </div>
  )
}

