import type { PropsWithChildren } from 'react'
import { AppHeader } from './AppHeader'
import { BottomNav } from './BottomNav'

type Props = PropsWithChildren<{
  hideFooter?: boolean
  hideHeader?: boolean
}>

export function AppShell({ children, hideFooter, hideHeader }: Props) {
  return (
    <main className="min-h-screen">
      <section className="party-board min-h-screen">
        {!hideHeader && <AppHeader />}
        <div className="board-content mx-auto w-full max-w-6xl px-4 pb-36 pt-2 sm:px-6 lg:px-8">
          {children}
        </div>
        {!hideFooter && <BottomNav />}
      </section>
    </main>
  )
}
