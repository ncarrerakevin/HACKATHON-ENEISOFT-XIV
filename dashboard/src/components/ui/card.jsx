// src/components/ui/card.jsx
import React from 'react'

export const Card = ({ className, ...props }) => (
    <div className={`bg-white rounded-lg border shadow-sm ${className}`} {...props} />
)

export const CardHeader = ({ className, ...props }) => (
    <div className={`flex flex-col space-y-1.5 p-6 ${className}`} {...props} />
)

export const CardTitle = ({ className, ...props }) => (
    <h3 className={`text-lg font-semibold ${className}`} {...props} />
)

export const CardContent = ({ className, ...props }) => (
    <div className={`p-6 pt-0 ${className}`} {...props} />
)