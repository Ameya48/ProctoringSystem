import React from 'react'

export default function ModernCard({ children, className = "", title, subtitle, actions }) {
  return (
    <div className={`bg-white rounded-xl shadow-lg border border-light ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-light">
          {title && (
            <h3 className="text-lg font-semibold text-dark">{title}</h3>
          )}
          {subtitle && (
            <p className="text-light text-sm mt-1">{subtitle}</p>
          )}
        </div>
      )}
      
      <div className="px-6 py-4">
        {children}
      </div>
      
      {actions && (
        <div className="px-6 py-4 border-t border-light bg-light">
          <div className="flex justify-end space-x-3">
            {actions}
          </div>
        </div>
      )}
    </div>
  )
}
