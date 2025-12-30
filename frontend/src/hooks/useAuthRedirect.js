import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export const useAuthRedirect = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const handleUnauthorized = () => {
      navigate('/login')
    }

    // Global fetch interceptor to catch 401 responses
    const originalFetch = window.fetch
    window.fetch = async (...args) => {
      const response = await originalFetch(...args)
      
      if (response.status === 401) {
        handleUnauthorized()
      }
      
      return response
    }

    // Cleanup function to restore original fetch
    return () => {
      window.fetch = originalFetch
    }
  }, [navigate])
}