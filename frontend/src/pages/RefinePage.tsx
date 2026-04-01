import { useNavigate, useParams } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader'
import { MobileStepBar } from '../components/MobileStepBar'

export function RefinePage() {
  const { eventId } = useParams()
  const navigate = useNavigate()

  return (
    <main className="min-h-screen">
      <section className="party-board min-h-screen">
          <AppHeader />
          <div className="board-content mx-auto w-full max-w-6xl px-4 pb-44 sm:px-6 lg:px-8">
            <h1 className="russo-title brand-shadow text-[48px] leading-none sm:text-[70px]">УТОЧНЕНИЕ</h1>
            <p className="mt-3 text-lg text-white/78">Финальный шаг текущего MVP</p>

            <div className="mt-6 grid gap-4 lg:grid-cols-3">
              <div className="app-card"><strong className="text-xl">Что изменить?</strong><p className="mt-3 leading-7 text-white/80">Можно доработать формат, гостей, бюджет и атмосферу праздника.</p></div>
              <div className="app-card"><strong className="text-xl">Что добавить?</strong><p className="mt-3 leading-7 text-white/80">Например: музыку, фотозону, торт, подарочные идеи или персональные поздравления.</p></div>
              <div className="app-card"><strong className="text-xl">Что дальше?</strong><p className="mt-3 leading-7 text-white/80">Дальше сюда можно добавить чек-лист, задачи, гостей и приглашения.</p></div>
            </div>
          </div>
          <MobileStepBar current={5} nextLabel="Завершено" onBack={() => navigate(`/event/${eventId}/variants`)} onNext={() => navigate('/')} />
      </section>
    </main>
  )
}
