import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useParams } from 'react-router-dom'
import { getMe } from './api'
import { ProtectedRoute } from './components/ProtectedRoute'
import { clearSession, getSavedUser, getToken, saveUser } from './storage'
import { AuthPage } from './pages/AuthPage'
import { CreateEventPage } from './pages/CreateEventPage'
import { EventWorkspacePage } from './pages/EventWorkspacePage'
import { MyEventsPage } from './pages/MyEventsPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { ProfilePage } from './pages/ProfilePage'
import { RSVPPage } from './pages/RSVPPage'
import { SettingsPage } from './pages/SettingsPage'
import { WelcomePage } from './pages/WelcomePage'

function LegacyEventRedirect({ tab, assistant = false }: { tab?: string; assistant?: boolean }) {
  const { eventId } = useParams()
  const suffix = new URLSearchParams(assistant ? { assistant: 'open', ...(tab ? { tab } : {}) } : tab ? { tab } : {}).toString()
  return <Navigate to={`/events/${eventId}${suffix ? `?${suffix}` : ''}`} replace />
}

function App() {
  const [authReady, setAuthReady] = useState(false)
  const [isAuthed, setIsAuthed] = useState(false)

  useEffect(() => {
    let active = true

    async function bootstrapAuth() {
      const token = getToken()
      if (!token) {
        if (active) {
          setIsAuthed(false)
          setAuthReady(true)
        }
        return
      }

      const savedUser = getSavedUser()
      if (savedUser) {
        if (active) {
          setIsAuthed(true)
          setAuthReady(true)
        }
        return
      }

      try {
        const me = await getMe(token)
        saveUser(me)
        if (active) {
          setIsAuthed(true)
          setAuthReady(true)
        }
      } catch {
        clearSession()
        if (active) {
          setIsAuthed(false)
          setAuthReady(true)
        }
      }
    }

    void bootstrapAuth()

    function handleStorage() {
      const token = getToken()
      const user = getSavedUser()
      setIsAuthed(Boolean(token && user))
      setAuthReady(true)
    }

    window.addEventListener('storage', handleStorage)
    return () => {
      active = false
      window.removeEventListener('storage', handleStorage)
    }
  }, [])

  return (
    <Routes>
      <Route path="/" element={<WelcomePage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/invitations/rsvp/:token" element={<RSVPPage />} />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute allow={isAuthed} loading={!authReady}>
            <OnboardingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/events"
        element={
          <ProtectedRoute allow={isAuthed} loading={!authReady}>
            <MyEventsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/events/new"
        element={
          <ProtectedRoute allow={isAuthed} loading={!authReady}>
            <CreateEventPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/events/:eventId"
        element={
          <ProtectedRoute allow={isAuthed} loading={!authReady}>
            <EventWorkspacePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute allow={isAuthed} loading={!authReady}>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute allow={isAuthed} loading={!authReady}>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route path="/create-event" element={<Navigate to="/events/new" replace />} />
      <Route path="/my-events" element={<Navigate to="/events" replace />} />
      <Route path="/event/:eventId/chat" element={<LegacyEventRedirect assistant />} />
      <Route path="/event/:eventId/variants" element={<LegacyEventRedirect tab="main" />} />
      <Route path="/event/:eventId/refine" element={<LegacyEventRedirect tab="backup" assistant />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
