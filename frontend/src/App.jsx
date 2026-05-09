import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Dashboard from './pages/Dashboard.jsx'
import EnhancedDashboard from './pages/EnhancedDashboard.jsx'
import ExamDashboard from './pages/ExamDashboard.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import WebcamPage from './pages/Webcam.jsx'
import ScreenMonitorPage from './pages/ScreenMonitor.jsx'
import ProctorEventsPage from './pages/ProctorEvents.jsx'
import ProctorDashboard from './pages/ProctorDashboard.jsx'
import PlaybackPage from './pages/Playback.jsx'
import LiveMonitoring from './pages/LiveMonitoring.jsx'
import Students from './pages/Students.jsx'
import Exams from './pages/Exams.jsx'
import Reports from './pages/Reports.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <EnhancedDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/classic"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/exam"
        element={
          <ProtectedRoute>
            <ExamDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/webcam"
        element={
          <ProtectedRoute>
            <WebcamPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/screen"
        element={
          <ProtectedRoute>
            <ScreenMonitorPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/proctor/events"
        element={
          <ProtectedRoute>
            <ProctorEventsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/proctor/dashboard"
        element={
          <ProtectedRoute>
            <ProctorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/playback"
        element={
          <ProtectedRoute>
            <PlaybackPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/monitoring"
        element={
          <ProtectedRoute>
            <LiveMonitoring />
          </ProtectedRoute>
        }
      />
      <Route
        path="/students"
        element={
          <ProtectedRoute>
            <Students />
          </ProtectedRoute>
        }
      />
      <Route
        path="/exams"
        element={
          <ProtectedRoute>
            <Exams />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <Reports />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

