import React from 'react'
import { Link, useNavigate } from 'react-router-dom'

export default function Layout({ children }) {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-dark">
      {/* Navigation Header */}
      <header className="bg-white border-b border-light">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-8">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </div>
                <span className="ml-3 text-xl font-bold text-dark">ProctorGuard</span>
              </div>
            </div>
            
            <nav className="hidden md:flex space-x-8">
              <Link 
                to="/dashboard" 
                className="text-light hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-all"
              >
                Dashboard
              </Link>
              <Link 
                to="/sessions" 
                className="text-light hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-all"
              >
                Sessions
              </Link>
              <Link 
                to="/monitoring" 
                className="text-light hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-all"
              >
                Live Monitoring
              </Link>
              <Link 
                to="/reports" 
                className="text-light hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-all"
              >
                Reports
              </Link>
              <Link 
                to="/students" 
                className="text-light hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-all"
              >
                Students
              </Link>
              <Link 
                to="/exams" 
                className="text-light hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-all"
              >
                Exams
              </Link>
            </nav>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success rounded-full"></div>
                <span className="text-light text-sm">Online</span>
              </div>
              <Link 
                to="/profile" 
                className="text-light hover:text-primary p-2 rounded-full transition-all"
                title="Profile"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </Link>
              <Link 
                to="/settings" 
                className="text-light hover:text-primary p-2 rounded-full transition-all"
                title="Settings"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </Link>
              <button
                onClick={handleLogout}
                className="text-danger hover:text-danger p-2 rounded-full transition-all"
                title="Logout"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 bg-light">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-light">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="text-light text-sm">
              &copy; 2024 ProctorGuard. All rights reserved.
            </div>
            <div className="flex space-x-6 text-light text-sm">
              <Link to="/help" className="hover:text-primary transition-all">Help</Link>
              <Link to="/privacy" className="hover:text-primary transition-all">Privacy</Link>
              <Link to="/terms" className="hover:text-primary transition-all">Terms</Link>
              <a href="#" className="text-light hover:text-primary transition-all">
                Support
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
