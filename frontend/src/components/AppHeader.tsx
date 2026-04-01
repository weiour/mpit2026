import { useEffect, useRef, useState, type SVGProps } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { clearSession, getSavedUser, getToken } from '../storage'

function BellIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path
        fillRule="evenodd"
        d="M12 2.25a4.5 4.5 0 0 0-4.5 4.5v1.33c0 .866-.295 1.707-.837 2.383L5.19 12.3c-.74.922-1.134 2.07-1.134 3.252 0 .62.503 1.123 1.123 1.123h13.642c.62 0 1.123-.503 1.123-1.123 0-1.182-.394-2.33-1.134-3.252l-1.473-1.837A3.75 3.75 0 0 1 16.5 8.08V6.75A4.5 4.5 0 0 0 12 2.25ZM9.75 18.75a2.25 2.25 0 1 0 4.5 0h-4.5Z"
        clipRule="evenodd"
      />
    </svg>
  )
}

export function AppHeader() {
  const user = getSavedUser()
  const token = getToken()
  const isAuthed = Boolean(token && user)

  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!menuRef.current) return
      if (!menuRef.current.contains(event.target as Node)) setOpen(false)
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  function handleLogout() {
    clearSession()
    setOpen(false)
    navigate('/auth', { replace: true })
  }

  return (
    <header className="relative z-50 mb-2 w-full border-b border-white/10">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 pb-4 pt-4 sm:px-8">
        <Link to='/' className="russo-title brand-shadow text-[28px] font-black uppercase tracking-tight text-white">
          Отмеч<span className="text-brand-orange">.</span>AI
        </Link>

        {!isAuthed ? (
          <button
            type="button"
            onClick={() => navigate('/auth')}
            className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/20"
          >
            Войти
          </button>
        ) : (
          <div className="relative" ref={menuRef}>
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-orange text-white shadow-[0_8px_18px_rgba(247,150,91,0.18)] transition hover:brightness-110"
                title="Уведомления"
                aria-label="Уведомления"
              >
                <BellIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
