import React, { useState } from 'react'
import Layout from '../components/UI/Layout'
import ModernCard from '../components/UI/ModernCard'
import StatusBadge from '../components/UI/StatusBadge'

export default function Students() {
  const [students, setStudents] = useState([
    {
      id: '1',
      name: 'John Doe',
      email: 'john.doe@university.edu',
      studentId: 'STU001',
      status: 'active',
      enrolledExams: 3,
      completedExams: 12,
      complianceScore: 92,
      lastActive: '2 hours ago'
    },
    {
      id: '2',
      name: 'Jane Smith',
      email: 'jane.smith@university.edu',
      studentId: 'STU002',
      status: 'active',
      enrolledExams: 2,
      completedExams: 8,
      complianceScore: 78,
      lastActive: '1 day ago'
    },
    {
      id: '3',
      name: 'Mike Johnson',
      email: 'mike.johnson@university.edu',
      studentId: 'STU003',
      status: 'inactive',
      enrolledExams: 0,
      completedExams: 15,
      complianceScore: 98,
      lastActive: '3 days ago'
    }
  ])

  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const filteredStudents = students.filter(student => {
    const matchesSearch = student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         student.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         student.studentId.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterStatus === 'all' || student.status === filterStatus
    return matchesSearch && matchesFilter
  })

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark mb-2">Students</h1>
          <p className="text-light text-sm">Manage and monitor student accounts</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Students</h3>
            <p className="text-3xl font-bold text-primary">{students.length}</p>
            <p className="text-light text-sm">Registered users</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Active Students</h3>
            <p className="text-3xl font-bold text-success">{students.filter(s => s.status === 'active').length}</p>
            <p className="text-light text-sm">Currently active</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Avg Compliance</h3>
            <p className="text-3xl font-bold text-primary">{Math.round(students.reduce((sum, s) => sum + s.complianceScore, 0) / students.length)}%</p>
            <p className="text-light text-sm">System average</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-light">
            <h3 className="text-lg font-semibold text-dark mb-2">Total Exams</h3>
            <p className="text-3xl font-bold text-primary">{students.reduce((sum, s) => sum + s.completedExams, 0)}</p>
            <p className="text-light text-sm">Completed exams</p>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-light mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search students..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-light rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border border-light rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <button className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-primary transition-all">
              Add Student
            </button>
          </div>
        </div>

        {/* Students Table */}
        <ModernCard title="Student List" subtitle={`${filteredStudents.length} students found`}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-light">
                  <th className="text-left py-3 px-4 text-dark font-semibold">Student</th>
                  <th className="text-left py-3 px-4 text-dark font-semibold">Student ID</th>
                  <th className="text-left py-3 px-4 text-dark font-semibold">Status</th>
                  <th className="text-left py-3 px-4 text-dark font-semibold">Exams</th>
                  <th className="text-left py-3 px-4 text-dark font-semibold">Compliance</th>
                  <th className="text-left py-3 px-4 text-dark font-semibold">Last Active</th>
                  <th className="text-left py-3 px-4 text-dark font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.map((student) => (
                  <tr key={student.id} className="border-b border-light hover:bg-light transition-all">
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-dark font-medium">{student.name}</p>
                        <p className="text-light text-sm">{student.email}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-dark">{student.studentId}</span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={student.status} />
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-dark">{student.completedExams} completed</p>
                        <p className="text-light text-sm">{student.enrolledExams} enrolled</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center">
                        <span className="text-dark font-medium">{student.complianceScore}%</span>
                        <div className="ml-2 w-20 bg-light rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              student.complianceScore >= 90 ? 'bg-success' : 
                              student.complianceScore >= 70 ? 'bg-yellow-500' : 'bg-danger'
                            }`}
                            style={{ width: `${student.complianceScore}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-light text-sm">{student.lastActive}</span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex space-x-2">
                        <button className="text-primary hover:text-primary text-sm">
                          View
                        </button>
                        <button className="text-light hover:text-primary text-sm">
                          Edit
                        </button>
                        <button className="text-danger hover:text-danger text-sm">
                          Suspend
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ModernCard>
      </div>
    </Layout>
  )
}
