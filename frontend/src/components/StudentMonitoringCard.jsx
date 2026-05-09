import React, { useMemo } from 'react'
import AlertBadge from './AlertBadge.jsx'
import SessionStatusPill from './SessionStatusPill.jsx'

function absMediaUrl(apiBase, mediaPath) {
  if (!mediaPath) return ''
  if (mediaPath.startsWith('http://') || mediaPath.startsWith('https://')) return mediaPath
  const base = apiBase || 'http://localhost:8000'
  return `${base}${mediaPath.startsWith('/') ? '' : '/'}${mediaPath}`
}

export default function StudentMonitoringCard({
  studentId,
  session,
  latestWebcamMediaUrl,
  lastEvent,
  alertCount = 0,
  maxSeverity = 0,
  apiBase
}) {
  const thumb = useMemo(() => absMediaUrl(apiBase, latestWebcamMediaUrl), [apiBase, latestWebcamMediaUrl])

  return (
    <div className="card rounded-2xl">
      <div className="card-padding flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm text-gray-500">Student</div>
          <div className="mt-1 font-mono text-sm truncate">{studentId}</div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <SessionStatusPill status={session?.status} />
            {alertCount > 0 ? (
              <span className="inline-flex items-center rounded-full bg-red-50 text-red-700 border border-red-200 px-2 py-0-5 text-xs">
                {alertCount} alerts
              </span>
            ) : (
              <span className="inline-flex items-center rounded-full bg-gray-50 text-gray-700 border border-gray-200 px-2 py-0-5 text-xs">
                no alerts
              </span>
            )}
            <AlertBadge severity={maxSeverity} />
          </div>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div>exam</div>
          <div className="font-mono">{session?.exam_id || '-'}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-0 border-t">
        <div className="bg-gray-50">
          <div className="h-40 flex items-center justify-center text-xs text-gray-500">
            Webcam Feed Disabled
          </div>
        </div>
        <div className="p-4">
          <div className="text-sm font-semibold">Latest activity</div>
          {lastEvent ? (
            <div className="mt-2 space-y-2">
              <div className="text-xs text-gray-600">
                <span className="font-mono">{lastEvent.event_type}</span>
              </div>
              <div className="text-xs text-gray-500 font-mono break-words">{String(lastEvent.timestamp)}</div>
              <pre className="text-xs bg-gray-50 border rounded-lg p-2 overflow-auto whitespace-pre-wrap max-h-24">
                {JSON.stringify(lastEvent.details || {}, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="mt-2 text-xs text-gray-500">No events yet.</div>
          )}
        </div>
      </div>

      <div className="px-4 py-3 border-t flex items-center justify-between text-xs text-gray-600">
        <div className="font-mono truncate">session: {session?._id || '-'}</div>
        <div>started: {session?.started_at ? String(session.started_at) : '-'}</div>
      </div>
    </div>
  )
}

