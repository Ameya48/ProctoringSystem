import React from 'react'

export default function SessionStatusPill({ status }) {
  const s = status || 'unknown'
  const cls =
    s === 'active'
      ? 'pill-active'
      : s === 'ended'
        ? 'pill-inactive'
        : 'pill-pending'

  return (
    <span className={`pill ${cls}`}>
      {s}
    </span>
  )
}

