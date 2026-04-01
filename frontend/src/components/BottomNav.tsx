import { Link, useLocation } from 'react-router-dom'
import type { SVGProps } from 'react'
import { getToken } from '../storage'

type NavItem = {
  to: string
  active: boolean
  label: string
  icon: 'home' | 'events' | 'profile'
}

function HomeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10.75L12 3l9 7.75" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.25 9.75V20a.75.75 0 00.75.75h4.5V14.5a.75.75 0 01.75-.75h1.5a.75.75 0 01.75.75v6.25H18a.75.75 0 00.75-.75V9.75" />
    </svg>
  )
}

function EventsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.25 2.75v3.5M15.75 2.75v3.5M3.75 9.25h16.5" />
      <rect x="3.75" y="5.75" width="16.5" height="14.5" rx="2.25" strokeWidth={2} />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01" />
    </svg>
  )
}

function ProfileIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" xmlns="http://www.w3.org/2000/svg" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.75 6.75a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0Z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 19.25a7.5 7.5 0 0115 0" />
    </svg>
  )
}

function NavIcon({ name }: { name: NavItem['icon'] }) {
  const className = 'h-5 w-5'
  switch (name) {
    case 'home':
      return <HomeIcon className={className} aria-hidden="true" />
    case 'events':
      return <EventsIcon className={className} aria-hidden="true" />
    case 'profile':
      return <ProfileIcon className={className} aria-hidden="true" />
    default:
      return null
  }
}

export function BottomNav() {
  const { pathname } = useLocation()
  const isAuthed = Boolean(getToken())
  if (!isAuthed) return null

  const items: NavItem[] = [
    {
      to: '/',
      active: pathname === '/',
      label: 'Главная',
      icon: 'home',
    },
    {
      to: '/events',
      active: pathname === '/events' || /^\/events\/\d+/.test(pathname) || pathname === '/events/new',
      label: 'События',
      icon: 'events',
    },
    {
      to: '/profile',
      active: pathname.includes('/profile') || pathname.includes('/settings') || pathname.includes('/onboarding'),
      label: 'Профиль',
      icon: 'profile',
    },
  ]

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-40 flex justify-center px-4">
      <nav className="bottom-dock pointer-events-auto" aria-label="Основная навигация">
        {items.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={item.active ? 'bottom-dock__item bottom-dock__item--active' : 'bottom-dock__item bottom-dock__item--idle'}
            aria-current={item.active ? 'page' : undefined}
          >
            <span className="bottom-dock__icon">
              <NavIcon name={item.icon} />
            </span>
            {item.active ? <span className="bottom-dock__label">{item.label}</span> : <span className="sr-only">{item.label}</span>}
          </Link>
        ))}
      </nav>
    </div>
  )
}
