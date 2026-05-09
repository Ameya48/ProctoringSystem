import React from 'react'

export default function StatusBadge({ status, children, className = "" }) {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'active':
        return { bg: 'bg-success', text: 'text-white', label: 'Active' }
      case 'inactive':
        return { bg: 'bg-light', text: 'text-dark', label: 'Inactive' }
      case 'warning':
        return { bg: 'bg-yellow-500', text: 'text-white', label: 'Warning' }
      case 'error':
        return { bg: 'bg-danger', text: 'text-white', label: 'Error' }
      case 'success':
        return { bg: 'bg-success', text: 'text-white', label: 'Success' }
      default:
        return { bg: 'bg-light', text: 'text-dark', label: 'Unknown' }
    }
  }
  
  const config = getStatusConfig(status)
  
  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text} ${className}`}>
      {children || config.label}
    </div>
  )
}
