import React, { useEffect } from 'react'

// Add API endpoint checks
const checkPythonBackend = async () => {
  try {
    const res = await fetch('/api/python/health')
    return res.ok ? 'healthy' : 'degraded'
  } catch {
    return 'down'
  }
}

// Update useEffect
useEffect(() => {
  const checkServices = async () => {
    const services = [
      { 
        name: 'Python Backend', 
        check: async () => {
          try {
            const res = await fetch('/api/python/health')
            return res.ok ? 'healthy' : 'degraded'
          } catch {
            return 'down'
          }
        }
      },
      // Add other service checks
    ]

    const results = await Promise.all(
      services.map(async (service) => ({
        service: service.name,
        status: await service.check(),
        lastChecked: new Date()
      }))
    )

    setStatuses(results)
  }
  // ...
}, []) 