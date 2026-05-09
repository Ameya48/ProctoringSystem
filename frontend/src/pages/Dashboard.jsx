import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'

export default function Dashboard() {
  const navigate = useNavigate()
  const [me, setMe] = useState(null)
  const [error, setError] = useState('')

  const logout = () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const res = await api.get('/auth/me')
        if (mounted) setMe(res.data)
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load profile')
      }
    })()
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-xl shadow p-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">
              Basic authenticated page (role-aware).
            </p>
          </div>
          <button className="rounded-lg border px-3 py-2 text-sm" onClick={logout}>
            Logout
          </button>
        </div>

        <div className="mt-6 bg-white rounded-xl shadow p-6">
          {error ? <div className="text-sm text-red-600">{error}</div> : null}
          {!me && !error ? <div className="text-sm text-gray-600">Loading...</div> : null}
          {me ? (
            <div className="space-y-2">
              <div className="text-sm">
                <span className="font-medium">Name:</span> {me.full_name}
              </div>
              <div className="text-sm">
                <span className="font-medium">Email:</span> {me.email}
              </div>
              <div className="text-sm">
                <span className="font-medium">Role:</span>{' '}
                <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5">
                  {me.role}
                </span>
              </div>
              <div className="pt-2">
                <Link className="underline text-sm" to="/exam">
                  Go to Exam Session Dashboard
                </Link>
              </div>
              <div className="pt-2 flex flex-col gap-2">
                <Link className="underline text-sm" to="/screen">
                  Screen Monitoring (student)
                </Link>
                <Link className="underline text-sm" to="/proctor/events">
                  Proctor Live Events
                </Link>
                <Link className="underline text-sm" to="/proctor/dashboard">
                  Proctor Dashboard
                </Link>
                <Link className="underline text-sm" to="/playback">
                  Recordings Playback
                </Link>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

