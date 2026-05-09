import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/UI/Layout'
import ModernCard from '../components/UI/ModernCard'
import StatusBadge from '../components/UI/StatusBadge'

export default function EnhancedDashboard() {
  const [stats] = useState({
    totalSessions: 156,
    activeSessions: 23,
    suspiciousActivities: 8,
    complianceScore: 94.2
  })

  const [recentSessions] = useState([
    {
      id: '1',
      studentName: 'John Doe',
      examName: 'Computer Science Final',
      status: 'active',
      startTime: '10:30 AM',
      duration: '45 min',
      compliance: 98,
      suspiciousCount: 0
    },
    {
      id: '2',
      studentName: 'Jane Smith',
      examName: 'Mathematics Midterm',
      status: 'warning',
      startTime: '10:15 AM',
      duration: '32 min',
      compliance: 78,
      suspiciousCount: 5
    },
    {
      id: '3',
      studentName: 'Mike Johnson',
      examName: 'Physics Quiz',
      status: 'completed',
      startTime: '9:45 AM',
      duration: '60 min',
      compliance: 98,
      suspiciousCount: 0
    }
  ])

  const [alerts] = useState([
    {
      id: '1',
      type: 'warning',
      message: 'Multiple faces detected',
      student: 'Jane Smith',
      time: '2 min ago'
    },
    {
      id: '2',
      type: 'error',
      message: 'No face detected for 30 seconds',
      student: 'John Doe',
      time: '5 min ago'
    }
  ])

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark mb-2">Proctor Dashboard</h1>
          <p className="text-light text-sm">Monitor and manage exam sessions in real-time</p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Sessions</h3>
            <p className="text-3xl font-bold text-primary">{stats.totalSessions}</p>
            <p className="text-light text-sm">+12% from last month</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Active Sessions</h3>
            <p className="text-3xl font-bold text-success">{stats.activeSessions}</p>
            <p className="text-light text-sm">Currently monitoring</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Suspicious Activities</h3>
            <p className="text-3xl font-bold text-danger">{stats.suspiciousActivities}</p>
            <p className="text-light text-sm">Requires attention</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Avg Compliance Score</h3>
            <p className="text-3xl font-bold text-primary">{stats.complianceScore}%</p>
            <p className="text-light text-sm">+1.2% improvement</p>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Sessions */}
          <div className="lg:col-span-2">
            <ModernCard 
              title="Recent Sessions" 
              subtitle="Live monitoring of active exam sessions"
              actions={
                <Link 
                  to="/sessions" 
                  className="text-white bg-primary hover:bg-primary px-4 py-2 rounded-lg text-sm font-medium transition-all"
                >
                  View All
                </Link>
              }
            >
              <div className="space-y-4">
                {recentSessions.map((session) => (
                  <div key={session.id} className="bg-light rounded-lg p-4 border border-light">
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

          {/* Alerts Panel */}
          <div className="lg:col-span-1">
            <ModernCard 
              title="Security Alerts" 
              subtitle="Real-time suspicious activity detection"
            >
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div key={alert.id} className="bg-danger/10 border border-danger rounded-lg p-3">
                    <div className="flex items-start space-x-3">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        alert.type === 'error' ? 'bg-danger' : 'bg-yellow-500'
                      }`}></div>
                      <div className="flex-1">
                        <p className="text-dark text-sm font-medium">{alert.message}</p>
                        <p className="text-light text-xs mt-1">{alert.student} • {alert.time}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 pt-4 border-t border-light">
                <Link 
                  to="/alerts" 
                  className="w-full text-white bg-danger hover:bg-danger px-4 py-2 rounded-lg text-sm font-medium transition-all text-center"
                >
                  View All Alerts
                </Link>
              </div>
            </ModernCard>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <ModernCard>
            <div className="text-center">
              <div className="bg-primary rounded-lg p-4 inline-block mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <h3 className="text-dark font-semibold mb-2">Start New Session</h3>
              <p className="text-light text-sm mb-4">Create a new proctoring session</p>
              <Link 
                to="/sessions/new" 
                className="w-full text-white bg-primary hover:bg-primary px-4 py-2 rounded-lg text-sm font-medium transition-all"
              >
                Create Session
              </Link>
            </div>
          </ModernCard>

          <ModernCard>
            <div className="text-center">
              <div className="bg-success rounded-lg p-4 inline-block mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a2 2 0 012-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2h2" />
                </svg>
              </div>
              <h3 className="text-dark font-semibold mb-2">View Reports</h3>
              <p className="text-light text-sm mb-4">Access detailed analytics and reports</p>
              <Link 
                to="/reports" 
                className="w-full text-white bg-success hover:bg-success px-4 py-2 rounded-lg text-sm font-medium transition-all"
              >
                View Reports
              </Link>
            </div>
          </ModernCard>

          <ModernCard>
            <div className="text-center">
              <div className="bg-primary rounded-lg p-4 inline-block mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="text-dark font-semibold mb-2">System Settings</h3>
              <p className="text-light text-sm mb-4">Configure proctoring parameters</p>
              <Link 
                to="/settings" 
                className="w-full text-white bg-primary hover:bg-primary px-4 py-2 rounded-lg text-sm font-medium transition-all"
              >
                Settings
              </Link>
            </div>
          </ModernCard>
        </div>
      </div>
    </Layout>
  )
}
