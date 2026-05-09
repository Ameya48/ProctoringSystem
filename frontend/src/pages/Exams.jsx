import React, { useState } from 'react'
import Layout from '../components/UI/Layout'
import ModernCard from '../components/UI/ModernCard'
import StatusBadge from '../components/UI/StatusBadge'

export default function Exams() {
  const [exams, setExams] = useState([
    {
      id: '1',
      title: 'Computer Science Final Exam',
      course: 'CS101',
      instructor: 'Dr. Smith',
      status: 'active',
      startTime: '10:30 AM',
      endTime: '12:30 PM',
      enrolledStudents: 45,
      activeStudents: 23,
      duration: '2 hours',
      type: 'Final',
      proctoringLevel: 'Strict'
    },
    {
      id: '2',
      title: 'Mathematics Midterm',
      course: 'MATH201',
      instructor: 'Prof. Johnson',
      status: 'upcoming',
      startTime: '2:00 PM',
      endTime: '4:00 PM',
      enrolledStudents: 32,
      activeStudents: 0,
      duration: '2 hours',
      type: 'Midterm',
      proctoringLevel: 'Moderate'
    },
    {
      id: '3',
      title: 'Physics Quiz',
      course: 'PHY101',
      instructor: 'Dr. Brown',
      status: 'completed',
      startTime: '9:00 AM',
      endTime: '10:00 AM',
      enrolledStudents: 28,
      activeStudents: 0,
      duration: '1 hour',
      type: 'Quiz',
      proctoringLevel: 'Basic'
    }
  ])

  const [filterStatus, setFilterStatus] = useState('all')

  const filteredExams = exams.filter(exam => {
    return filterStatus === 'all' || exam.status === filterStatus
  })

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-success'
      case 'upcoming': return 'text-yellow-500'
      case 'completed': return 'text-light'
      default: return 'text-light'
    }
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark mb-2">Exams</h1>
          <p className="text-light text-sm">Manage and monitor exam sessions</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Exams</h3>
            <p className="text-3xl font-bold text-primary">{exams.length}</p>
            <p className="text-light text-sm">All exams</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Active Exams</h3>
            <p className="text-3xl font-bold text-success">{exams.filter(e => e.status === 'active').length}</p>
            <p className="text-light text-sm">In progress</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Students</h3>
            <p className="text-3xl font-bold text-primary">{exams.reduce((sum, e) => sum + e.enrolledStudents, 0)}</p>
            <p className="text-light text-sm">Enrolled students</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Active Now</h3>
            <p className="text-3xl font-bold text-yellow-500">{exams.reduce((sum, e) => sum + e.activeStudents, 0)}</p>
            <p className="text-light text-sm">Currently taking exams</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-light mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex space-x-4">
              <button
                onClick={() => setFilterStatus('all')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  filterStatus === 'all' 
                    ? 'bg-primary text-white' 
                    : 'bg-light text-dark hover:bg-light'
                }`}
              >
                All Exams
              </button>
              <button
                onClick={() => setFilterStatus('active')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  filterStatus === 'active' 
                    ? 'bg-success text-white' 
                    : 'bg-light text-dark hover:bg-light'
                }`}
              >
                Active
              </button>
              <button
                onClick={() => setFilterStatus('upcoming')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  filterStatus === 'upcoming' 
                    ? 'bg-yellow-500 text-white' 
                    : 'bg-light text-dark hover:bg-light'
                }`}
              >
                Upcoming
              </button>
              <button
                onClick={() => setFilterStatus('completed')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  filterStatus === 'completed' 
                    ? 'bg-light text-dark' 
                    : 'bg-light text-dark hover:bg-light'
                }`}
              >
                Completed
              </button>
            </div>
            <button className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-primary transition-all">
              Create Exam
            </button>
          </div>
        </div>

        {/* Exams Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredExams.map((exam) => (
            <ModernCard key={exam.id} className="hover:shadow-xl transition-all">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-dark">{exam.title}</h3>
                  <p className="text-light text-sm">{exam.course} • {exam.type}</p>
                </div>
                
                <div className="flex items-center justify-between">
                  <StatusBadge status={exam.status} />
                  <span className={`text-sm font-medium ${getStatusColor(exam.status)}`}>
                    {exam.status.charAt(0).toUpperCase() + exam.status.slice(1)}
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-light text-sm">Instructor</span>
                    <span className="text-dark text-sm">{exam.instructor}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-light text-sm">Duration</span>
                    <span className="text-dark text-sm">{exam.duration}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-light text-sm">Proctoring</span>
                    <span className="text-dark text-sm">{exam.proctoringLevel}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-light text-sm">Time</span>
                    <span className="text-dark text-sm">{exam.startTime} - {exam.endTime}</span>
                  </div>
                </div>

                <div className="bg-light rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-dark font-medium">{exam.activeStudents}/{exam.enrolledStudents}</p>
                      <p className="text-light text-xs">Students Active</p>
                    </div>
                    <div className="w-16 bg-light rounded-full h-2">
                      <div 
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${(exam.activeStudents / exam.enrolledStudents) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button className="flex-1 bg-primary text-white px-3 py-2 rounded-lg hover:bg-primary transition-all text-sm">
                    {exam.status === 'active' ? 'Monitor' : exam.status === 'upcoming' ? 'Start' : 'View Results'}
                  </button>
                  <button className="flex-1 bg-light text-dark px-3 py-2 rounded-lg hover:bg-light transition-all text-sm">
                    Edit
                  </button>
                </div>
              </div>
            </ModernCard>
          ))}
        </div>
      </div>
    </Layout>
  )
}
