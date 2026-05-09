import React from 'react'

export default function AlertBadge({ severity = 0 }) {
  const s = Number(severity) || 0
  const cls =
    s >= 80
      ? 'severity-high'
      : s >= 60
        ? 'severity-medium'
        : 'severity-low'

  return (
    <span className={`pill ${cls}`}>
      severity {s}
    </span>
  )
}

