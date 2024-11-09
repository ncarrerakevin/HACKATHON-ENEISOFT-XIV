// src/components/ui/badge.jsx
import React from 'react'

export const Badge = ({ variant = 'default', className, ...props }) => {
    const variants = {
        default: 'bg-primary',
        secondary: 'bg-secondary',
        destructive: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white'
    }

    return (
        <div className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${variants[variant]} ${className}`} {...props} />
    )
}