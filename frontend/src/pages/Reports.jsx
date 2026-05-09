import React, { useState } from 'react'
import Layout from '../components/UI/Layout'
import ModernCard from '../components/UI/ModernCard'

export default function Reports() {
  const [dateRange, setDateRange] = useState('7days')
  const [reportType, setReportType] = useState('overview')

  const reportData = {
    overview: {
      totalExams: 156,
      totalStudents: 892,
      avgCompliance: 91.2,
      totalAlerts: 234,
      completionRate: 87.5
    },
    compliance: {
      excellent: 45,
      good: 67,
      average: 23,
      poor: 12
    },
    alerts: {
      multipleFaces: 89,
      noFace: 67,
      lookingAway: 45,
      suspiciousMovement: 33
    }
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark mb-2">Reports & Analytics</h1>
          <p className="text-light text-sm">Comprehensive insights and analytics</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-light mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex space-x-4">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-4 py-2 border border-light rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="24hours">Last 24 Hours</option>
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="90days">Last 90 Days</option>
              </select>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="px-4 py-2 border border-light rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="overview">Overview</option>
                <option value="compliance">Compliance</option>
                <option value="alerts">Alerts</option>
                <option value="performance">Performance</option>
              </select>
            </div>
            <div className="flex space-x-2">
              <button className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary transition-all">
                Export PDF
              </button>
              <button className="bg-success text-white px-4 py-2 rounded-lg hover:bg-success transition-all">
                Export Excel
              </button>
            </div>
          </div>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Exams</h3>
            <p className="text-3xl font-bold text-primary">{reportData.overview.totalExams}</p>
            <p className="text-success text-sm">+12% from last period</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Students</h3>
            <p className="text-3xl font-bold text-primary">{reportData.overview.totalStudents}</p>
            <p className="text-success text-sm">+8% from last period</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Avg Compliance</h3>
            <p className="text-3xl font-bold text-success">{reportData.overview.avgCompliance}%</p>
            <p className="text-success text-sm">+2.1% improvement</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Alerts</h3>
            <p className="text-3xl font-bold text-danger">{reportData.overview.totalAlerts}</p>
            <p className="text-danger text-sm">+5% from last period</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Completion Rate</h3>
            <p className="text-3xl font-bold text-primary">{reportData.overview.completionRate}%</p>
            <p className="text-success text-sm">+3.2% improvement</p>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Compliance Distribution */}
          <ModernCard title="Compliance Distribution" subtitle="Student compliance levels">
            <div className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">Excellent (90-100%)</span>
                  <span className="text-primary font-bold">{reportData.compliance.excellent}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-success h-3 rounded-full" style={{ width: '35%' }}></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">Good (80-89%)</span>
                  <span className="text-primary font-bold">{reportData.compliance.good}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-primary h-3 rounded-full" style={{ width: '52%' }}></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">Average (70-79%)</span>
                  <span className="text-primary font-bold">{reportData.compliance.average}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-yellow-500 h-3 rounded-full" style={{ width: '18%' }}></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">Poor (Below 70%)</span>
                  <span className="text-primary font-bold">{reportData.compliance.poor}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-danger h-3 rounded-full" style={{ width: '9%' }}></div>
                </div>
              </div>
            </div>
          </ModernCard>

          {/* Alert Types */}
          <ModernCard title="Alert Types" subtitle="Most common violations">
            <div className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">Multiple Faces Detected</span>
                  <span className="text-danger font-bold">{reportData.alerts.multipleFaces}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-danger h-3 rounded-full" style={{ width: '38%' }}></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">No Face Detected</span>
                  <span className="text-danger font-bold">{reportData.alerts.noFace}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-yellow-500 h-3 rounded-full" style={{ width: '29%' }}></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">Looking Away</span>
                  <span className="text-danger font-bold">{reportData.alerts.lookingAway}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-yellow-500 h-3 rounded-full" style={{ width: '19%' }}></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-dark font-medium">Suspicious Movement</span>
                  <span className="text-danger font-bold">{reportData.alerts.suspiciousMovement}</span>
                </div>
                <div className="w-full bg-light rounded-full h-3">
                  <div className="bg-light h-3 rounded-full" style={{ width: '14%' }}></div>
                </div>
              </div>
            </div>
          </ModernCard>
        </div>

        {/* Recent Activity */}
        <ModernCard title="Recent Activity" subtitle="Latest system events">
          <div className="space-y-4">
            <div className="bg-light rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-dark font-medium">Computer Science Final Exam Completed</p>
                  <p className="text-light text-sm">45 students completed • 92% average compliance</p>
                </div>
                <span className="text-light text-sm">2 hours ago</span>
              </div>
            </div>
            
            <div className="bg-light rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-dark font-medium">High Alert Activity Detected</p>
                  <p className="text-light text-sm">12 alerts in Mathematics Midterm</p>
                </div>
                <span className="text-light text-sm">3 hours ago</span>
              </div>
            </div>
            
            <div className="bg-light rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-dark font-medium">New Student Registration</p>
                  <p className="text-light text-sm">23 new students registered this week</p>
                </div>
                <span className="text-light text-sm">1 day ago</span>
              </div>
            </div>
          </div>
        </ModernCard>
      </div>
    </Layout>
  )
}
