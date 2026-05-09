import React from 'react'

export default function MetricCard({ title, value, change, icon, trend = 'up', color = 'blue' }) {
  const trendColors = {
    up: 'text-success',
    down: 'text-danger',
    neutral: 'text-light'
  }

  return (
    <div className={`bg-white rounded-xl shadow-lg border border-light p-6`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-light text-sm font-medium">{title}</p>
          <p className="text-dark text-3xl font-bold mt-2">{value}</p>
          {change && (
            <div className={`flex items-center mt-2 text-sm ${trendColors[trend]}`}>
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {trend === 'up' ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0L13-1m-8 8v8" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0L13 9m-8 8v8" />
                )}
              </svg>
              {change}
            </div>
          )}
        </div>
        
        {icon && (
          <div className="bg-light rounded-lg p-3">
            <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {icon}
            </svg>
          </div>
        )}
      </div>
    </div>
  )
}
