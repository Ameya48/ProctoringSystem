import React, { useState, useEffect } from 'react'
import Layout from '../components/UI/Layout'
import ModernCard from '../components/UI/ModernCard'
import StatusBadge from '../components/UI/StatusBadge'

export default function LiveMonitoring() {
  const [activeSessions, setActiveSessions] = useState([
    {
      id: '1',
      studentName: 'John Doe',
      examName: 'Computer Science Final',
      status: 'active',
      startTime: '10:30 AM',
      duration: '45 min',
      compliance: 92,
      suspiciousCount: 2,
      webcam: true,
      screen: true,
      audio: true
    },
    {
      id: '2',
      studentName: 'Jane Smith',
      examName: 'Mathematics Midterm',
      status: 'warning',
      startTime: '10:15 AM',
      duration: '32 min',
      compliance: 78,
      suspiciousCount: 5,
      webcam: true,
      screen: false,
      audio: true
    },
    {
      id: '3',
      studentName: 'Mike Johnson',
      examName: 'Physics Quiz',
      status: 'active',
      startTime: '9:45 AM',
      duration: '60 min',
      compliance: 98,
      suspiciousCount: 0,
      webcam: true,
      screen: true,
      audio: false
    }
  ])

  const [selectedSession, setSelectedSession] = useState(null)

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark mb-2">Live Monitoring</h1>
          <p className="text-light text-sm">Real-time monitoring of active exam sessions</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Active Sessions</h3>
            <p className="text-3xl font-bold text-primary">{activeSessions.filter(s => s.status === 'active').length}</p>
            <p className="text-light text-sm">Currently monitoring</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Warning Sessions</h3>
            <p className="text-3xl font-bold text-yellow-500">{activeSessions.filter(s => s.status === 'warning').length}</p>
            <p className="text-light text-sm">Need attention</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Alerts</h3>
            <p className="text-3xl font-bold text-danger">{activeSessions.reduce((sum, s) => sum + s.suspiciousCount, 0)}</p>
            <p className="text-light text-sm">Suspicious activities</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Avg Compliance</h3>
            <p className="text-3xl font-bold text-success">{Math.round(activeSessions.reduce((sum, s) => sum + s.compliance, 0) / activeSessions.length)}%</p>
            <p className="text-light text-sm">System average</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sessions List */}
          <div className="lg:col-span-2">
            <ModernCard title="Active Sessions" subtitle="Click to view details">
              <div className="space-y-4">
                {activeSessions.map((session) => (
                  <div 
                    key={session.id} 
                    className={`bg-light rounded-lg p-4 border cursor-pointer transition-all hover:shadow-md ${
                      selectedSession?.id === session.id ? 'border-primary' : 'border-light'
                    }`}
                    onClick={() => setSelectedSession(session)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h4 className="text-dark font-medium">{session.studentName}</h4>
                          <StatusBadge status={session.status} />
                        </div>
                        <p className="text-light text-sm mt-1">{session.examName}</p>
                        <div className="flex items-center space-x-4 mt-2 text-sm text-light">
                          <span>Started: {session.startTime}</span>
                          <span>Duration: {session.duration}</span>
                        </div>
                        <div className="flex items-center space-x-4 mt-2">
                          <span className={`text-xs ${session.webcam ? 'text-success' : 'text-danger'}`}>
                            📹 Webcam {session.webcam ? 'Active' : 'Inactive'}
                          </span>
                          <span className={`text-xs ${session.screen ? 'text-success' : 'text-danger'}`}>
                            🖥️ Screen {session.screen ? 'Active' : 'Inactive'}
                          </span>
                          <span className={`text-xs ${session.audio ? 'text-success' : 'text-danger'}`}>
                            🎤 Audio {session.audio ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4 text-right">
                        <div className="text-2xl font-bold text-primary">{session.compliance}%</div>
                        <p className="text-xs text-light mt-1">Compliance</p>
                        {session.suspiciousCount > 0 && (
                          <p className="text-xs text-danger mt-2">{session.suspiciousCount} alerts</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ModernCard>
          </div>

          {/* Session Details */}
          <div className="lg:col-span-1">
            {selectedSession ? (
              <ModernCard title="Session Details" subtitle={`${selectedSession.studentName} - ${selectedSession.examName}`}>
                <div className="space-y-4">
                  <div className="bg-light rounded-lg p-4">
                    <h4 className="text-dark font-semibold mb-3">Monitoring Status</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-light text-sm">Webcam</span>
                        <span className={`text-sm ${selectedSession.webcam ? 'text-success' : 'text-danger'}`}>
                          {selectedSession.webcam ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-light text-sm">Screen Share</span>
                        <span className={`text-sm ${selectedSession.screen ? 'text-success' : 'text-danger'}`}>
                          {selectedSession.screen ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-light text-sm">Audio</span>
                        <span className={`text-sm ${selectedSession.audio ? 'text-success' : 'text-danger'}`}>
                          {selectedSession.audio ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-light rounded-lg p-4">
                    <h4 className="text-dark font-semibold mb-3">Session Info</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-light text-sm">Start Time</span>
                        <span className="text-sm text-dark">{selectedSession.startTime}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-light text-sm">Duration</span>
                        <span className="text-sm text-dark">{selectedSession.duration}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-light text-sm">Compliance</span>
                        <span className="text-sm text-dark">{selectedSession.compliance}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-light text-sm">Alerts</span>
                        <span className="text-sm text-danger">{selectedSession.suspiciousCount}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <button className="w-full bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary transition-all">
                      View Webcam Feed
                    </button>
                    <button className="w-full bg-success text-white px-4 py-2 rounded-lg hover:bg-success transition-all">
                      View Screen Share
                    </button>
                    <button className="w-full bg-danger text-white px-4 py-2 rounded-lg hover:bg-danger transition-all">
                      Pause Session
                    </button>
                  </div>
                </div>
              </ModernCard>
            ) : (
              <ModernCard title="Session Details" subtitle="Select a session to view details">
                <div className="text-center py-8">
                  <div className="bg-light rounded-lg p-6">
                    <svg className="w-12 h-12 text-light mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <p className="text-light text-sm">Select a session from the list to view detailed monitoring information</p>
                  </div>
                </div>
              </ModernCard>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
