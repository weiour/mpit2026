import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listEvents } from '../api'
import { AppHeader } from '../components/AppHeader'
import { BottomNav } from '../components/BottomNav'
import { HeroConfetti } from '../components/HeroConfetti'
import { getSavedUser, getToken } from '../storage'
import type { EventItem } from '../types'

const featureCards = [
  'Онбординг региона для 2ГИС',
  'Быстрая анкета + чат с агентом',
  'Варианты мест, гости и план Б',
]

const howItWorks = [
  {
    title: '1. Создай основу',
    text: 'Укажи дату, бюджет, город и общее направление праздника без лишних шагов.',
  },
  {
    title: '2. Уточни в чате',
    text: 'Агент задаёт вопросы, а пользователь может отвечать кнопками или свободным текстом.',
  },
  {
    title: '3. Выбери базу',
    text: 'Места, домашние сценарии и дальнейшие действия собираются в одном рабочем пространстве.',
  },
]

function statusLabel(status?: string | null) {
  switch (status) {
    case 'ready':
      return 'готово к приглашениям'
    case 'concept_selected':
      return 'основа выбрана'
    case 'planning':
      return 'в процессе планирования'
    default:
      return 'черновик'
  }
}

function venueModeLabel(mode?: string | null) {
  switch (mode) {
    case 'outside':
      return 'вне дома'
    case 'home':
      return 'дома'
    case 'undecided':
      return 'ещё не решено'
    default:
      return 'не указан'
  }
}

export function WelcomePage() {
  const navigate = useNavigate()
  const token = getToken()
  const user = getSavedUser()
  const isAuthed = Boolean(token && user)
  const [items, setItems] = useState<EventItem[]>([])
  const [loading, setLoading] = useState(isAuthed)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthed || !token) {
      setItems([])
      setLoading(false)
      return
    }

    let active = true
    setLoading(true)
    setError('')

    listEvents(token)
      .then((data) => {
        if (active) setItems(data)
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'Не удалось загрузить события')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [isAuthed, token])

  const nextAction = useMemo(() => {
    const activePlanning = items.find((item) => item.status === 'planning' || item.status === 'concept_selected')
    return activePlanning || items[0] || null
  }, [items])

  const regionReady = Boolean(user?.region?.trim())

  return (
    <main className="min-h-screen">
      <section className="party-board min-h-screen">
        <AppHeader />

        <div className="board-content mx-auto w-full max-w-6xl px-4 pb-40 sm:px-6 lg:px-8">
          {!isAuthed ? (
            <div className="pt-2">
              <div className="content-width">
                <p className="text-xl font-bold text-brand-orange">Собери друзей — отметим!</p>

                <h1 className="russo-title brand-shadow mt-4 text-[52px] leading-[0.92] sm:text-[72px] lg:text-[84px]">
                  ОТМЕЧ.AI
                </h1>


              </div>

              <div className="content-width mt-8 relative">
                <div className="hero-banner relative overflow-visible rounded-[16px] px-5 pb-20 pt-8 shadow-panel sm:px-7 sm:pb-20 sm:pt-9 lg:min-h-[360px]">
                  <HeroConfetti />

                  <div className="relative z-30 max-w-[260px] pr-[110px] sm:max-w-[340px] sm:pr-[180px] lg:max-w-[420px] lg:pr-[240px]">
                    <h2 className="text-[34px] font-extrabold italic leading-[0.92] text-white sm:text-[52px]">
                      Праздник
                      <br />
                      начинается
                      <br />
                      здесь!
                    </h2>

                    <p className="mt-5 max-w-xs text-sm leading-6 text-white/80 sm:max-w-sm sm:text-base sm:leading-7">
                      Один старт — и дальше агент поможет собрать идею, уточнить детали, предложить варианты и удержать весь сценарий в одном месте.
                    </p>
                  </div>

                  <img
                    src="/assets/CATP.png"
                    alt="cat"
                    className="pointer-events-none absolute bottom-[-26px] right-[-12px] z-20 w-[250px] object-contain sm:bottom-[-32px] sm:right-[-10px] sm:w-[305px] lg:bottom-[-42px] lg:right-[-8px] lg:w-[360px]"
                  />
                </div>

                <div className="absolute inset-x-4 -bottom-5 z-30 sm:inset-x-7 sm:-bottom-6">
                  <button
                    onClick={() => navigate('/auth')}
                    className="primary-btn w-full px-5 py-4 text-lg sm:max-w-[360px]"
                  >
                    Начать подготовку
                  </button>
                </div>
              </div>

              <div className="content-width mt-16 grid gap-4 lg:grid-cols-2 lg:items-stretch">
                <div className="app-card h-full">
                  <p className="text-sm font-bold uppercase tracking-wide text-white/60">Как это работает</p>

                  <div className="mt-4 grid gap-4 md:grid-cols-3">
                    {howItWorks.map((item) => (
                      <div key={item.title} className="h-full rounded-[22px] bg-black/20 p-4">
                        <div className="text-lg font-bold text-white">{item.title}</div>
                        <p className="mt-3 text-sm leading-6 text-white/78">{item.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="pt-2">
              <div className="content-width"> 
                <div className="mt-4 grid gap-6 xl:grid-cols-[1.08fr_0.92fr] xl:items-start">
                  <div className="relative">
                    <div className="hero-banner relative overflow-hidden rounded-[16px] px-5 pb-20 pt-8 shadow-panel sm:px-7 sm:pb-20 sm:pt-9 lg:min-h-[360px] xl:min-h-[410px]">
                      <HeroConfetti />

                      <div className="relative z-30 max-w-[260px] pr-[110px] sm:max-w-[340px] sm:pr-[180px] lg:max-w-[420px] lg:pr-[240px] xl:max-w-[470px] xl:pr-[280px]">
                        <div className="text-sm font-bold uppercase tracking-[0.22em] text-white/70">
                          Привет, {user?.name || 'организатор'}
                        </div>
                        <h1 className="mt-4 text-[34px] font-extrabold italic leading-[0.92] text-white sm:text-[52px] xl:text-[64px]">
                          Продолжай
                          <br />
                          праздник
                          <br />
                          здесь!
                        </h1>
                        <p className="mt-5 max-w-xs text-sm leading-6 text-white/80 sm:max-w-sm sm:text-base sm:leading-7 xl:max-w-md">
                          Вернись к последнему событию, начни новое или сначала укажи основной регион, чтобы подбор мест через 2ГИС был точнее.
                        </p>
                      </div>

                      <img
                        src="/assets/CATP.png"
                        alt="cat"
                        className="pointer-events-none absolute bottom-[-26px] right-[-12px] z-20 w-[250px] object-contain sm:bottom-[-32px] sm:right-[-10px] sm:w-[305px] lg:bottom-[-42px] lg:right-[-8px] lg:w-[360px] xl:bottom-[-28px] xl:right-[4px] xl:w-[405px]"
                      />
                    </div>

                    <div className="absolute inset-x-4 -bottom-5 z-30 sm:inset-x-7 sm:-bottom-6">
                      <button
                        onClick={() => navigate(nextAction ? `/events/${nextAction.id}` : '/events/new')}
                        className="primary-btn w-full px-5 py-4 text-lg sm:max-w-[360px]"
                      >
                        {nextAction ? 'Продолжить последнее событие' : 'Создать первое событие'}
                      </button>
                    </div>
                  </div>

                  <div className="grid gap-4 xl:pt-3">
                    <div className="app-card p-5 xl:min-h-[250px]">
                      <p className="text-sm font-bold uppercase tracking-wide text-white/60">Следующий шаг</p>
                      {!regionReady ? (
                        <div className="mt-4 rounded-[22px] bg-black/20 p-4">
                          <div className="text-lg font-bold text-white">Нужно указать основной регион</div>
                          <p className="mt-2 text-sm leading-6 text-white/78">
                            Без этого подбор мест всё равно работает, но результаты хуже понимают твою базовую точку.
                          </p>
                          <button
                            onClick={() => navigate('/onboarding')}
                            className="primary-btn mt-4 px-4 py-3 text-sm"
                          >
                            Заполнить регион
                          </button>
                        </div>
                      ) : nextAction ? (
                        <div className="mt-4 rounded-[22px] bg-black/20 p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="text-lg font-bold text-white">{nextAction.title}</div>
                              <p className="mt-2 text-sm leading-6 text-white/78">
                                {nextAction.event_date || 'Дата пока не указана'} · {statusLabel(nextAction.status)}
                              </p>
                            </div>
                            <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] text-white/80">
                              {venueModeLabel(nextAction.venue_mode)}
                            </span>
                          </div>
                          <div className="mt-4 grid gap-2 text-sm text-white/78 sm:grid-cols-2">
                            <div>Город: {nextAction.city || user?.region || 'не указан'}</div>
                            <div>Гостей: {nextAction.guests_count || '—'}</div>
                            <div>Основа: {nextAction.selected_option || 'ещё не выбрана'}</div>
                            <div>Формат: {nextAction.format || 'уточняется'}</div>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-4 rounded-[22px] bg-black/20 p-4">
                          <div className="text-lg font-bold text-white">Можно начинать</div>
                          <p className="mt-2 text-sm leading-6 text-white/78">
                            Событий пока нет. Создай первое и дальше агент сам проведёт по анкете, чату и выбору базы.
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="app-card p-5 xl:min-h-[136px]">
                      <p className="text-sm font-bold uppercase tracking-wide text-white/60">Что уже умеет агент</p>
                      <div className="mt-4 space-y-3 text-sm leading-6 text-white/78">
                        <p>• собирать основу события из короткой анкеты</p>
                        <p>• уточнять детали в формате живого чата</p>
                        <p>• предлагать места и альтернативы</p>
                      </div>
                    </div>
                  </div>
                </div>

                {error ? (
                  <div className="mt-4 rounded-[18px] border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                    {error}
                  </div>
                ) : null}

                {loading ? (
                  <div className="mt-8 grid gap-4 lg:grid-cols-3">
                    {Array.from({ length: 3 }).map((_, index) => (
                      <div key={index} className="app-card h-[180px] animate-pulse bg-white/5" />
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </div>

        <BottomNav />
      </section>
    </main>
  )
}
