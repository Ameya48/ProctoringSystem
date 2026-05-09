import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'

export default function Register() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('student')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.post('/auth/register', {
        email,
        full_name: fullName,
        role,
        password
      })
      localStorage.setItem('access_token', res.data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-full flex items-center justify-center p-6 bg-gray-50">
      <div className="w-full max-w-md bg-white rounded-xl shadow p-6">
        <h1 className="text-2xl font-semibold">Register</h1>
        <p className="text-sm text-gray-500 mt-1">Create a student or proctor account.</p>

        {error ? <div className="mt-4 text-sm text-red-600">{error}</div> : null}

        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="form-label">Full name</label>
            <input
              className="mt-1 w-full form-input-rounded focus-ring"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              type="text"
              required
            />
          </div>
          <div>
            <label className="form-label">Email</label>
            <input
              className="mt-1 w-full form-input-rounded focus-ring"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              required
            />
          </div>
          <div>
            <label className="form-label">Role</label>
            <select
              className="mt-1 w-full form-input-rounded focus-ring"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="student">Student</option>
              <option value="proctor">Proctor</option>
            </select>
          </div>
          <div>
            <label className="form-label">Password</label>
            <input
              className="mt-1 w-full form-input-rounded focus-ring"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              required
              minLength={6}
            />
          </div>
          <button
            className="w-full rounded-lg bg-black text-white py-2 font-medium disabled-opacity-50"
            disabled={loading}
            type="submit"
          >
            {loading ? 'Creating...' : 'Create account'}
          </button>
        </form>

        <div className="mt-4 text-sm text-gray-600">
          Already registered? <Link className="underline" to="/login">Login</Link>
        </div>
      </div>
    </div>
  )
}

