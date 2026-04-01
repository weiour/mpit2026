import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listEvents } from '../api'
import { AppShell } from '../components/AppShell'
import { getToken } from '../storage'
import type { EventItem } from '../types'
import { formatEventStatus, formatVenueMode } from '../utils/eventLabels'

export function MyEventsPage() {
  const navigate = useNavigate()
  const token = getToken()
  const [items, setItems] = useState<EventItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    let active = true
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
  }, [token])

  const nextAction = useMemo(() => {
    const activePlanning = items.find((item) => item.status === 'draft' || item.status === 'planning' || item.status === 'concept_selected')
    return activePlanning || items[0] || null
  }, [items])

  const stats = useMemo(() => {
    return {
      total: items.length,
      active: items.filter((item) => item.status === 'draft' || item.status === 'planning' || item.status === 'concept_selected').length,
      ready: items.filter((item) => item.status === 'ready').length,
    }
  }, [items])

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="grid gap-6 xl:grid-cols-[1.18fr_0.82fr]">
          <div className="panel p-6 sm:p-8">
            <div className="text-sm uppercase tracking-[0.24em] text-white/70">Мои события</div>
            <h1 className="mt-3 text-4xl font-black tracking-tight text-white sm:text-5xl">Все события в одном месте</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-white/88">
              На компьютере карточки теперь собраны отдельной сеткой ниже, а сверху остались только основные действия и краткая сводка.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button onClick={() => navigate('/events/new')} className="primary-btn w-full px-5 py-4 text-lg sm:w-auto">
                Новое событие
              </button>
              {nextAction ? (
                <button onClick={() => navigate(`/events/${nextAction.id}`)} className="secondary-btn w-full px-6 py-4 sm:w-auto">
                  Продолжить последнее
                </button>
              ) : null}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
            <div className="panel p-5">
              <div className="text-sm uppercase tracking-[0.2em] text-white/70">Всего</div>
              <div className="mt-3 text-4xl font-black text-white">{stats.total}</div>
              <div className="mt-1 text-sm text-white/80">событий создано</div>
            </div>
            <div className="panel p-5">
              <div className="text-sm uppercase tracking-[0.2em] text-white/70">В работе</div>
              <div className="mt-3 text-4xl font-black text-white">{stats.active}</div>
              <div className="mt-1 text-sm text-white/80">нужно продолжить</div>
            </div>
            <div className="panel p-5">
              <div className="text-sm uppercase tracking-[0.2em] text-white/70">Готово</div>
              <div className="mt-3 text-4xl font-black text-white">{stats.ready}</div>
              <div className="mt-1 text-sm text-white/80">можно звать гостей</div>
            </div>
          </div>
        </section>

        {error ? <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div> : null}

        {loading ? (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="panel h-56 animate-pulse bg-white/5" />
            ))}
          </section>
        ) : items.length === 0 ? (
          <div className="panel p-8 text-center text-white/85">
            Здесь будут все события. Первое можно создать прямо сейчас.
          </div>
        ) : (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => navigate(`/events/${item.id}`)}
                className="panel flex h-full flex-col p-6 text-left transition hover:-translate-y-1 hover:bg-white/[0.09]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-2xl font-bold text-white">{item.title}</div>
                    <div className="mt-1 text-sm text-white/80">{item.event_date || 'Дата пока не указана'}</div>
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.16em] text-white/90">
                    {formatEventStatus(item.status, 'compact')}
                  </span>
                </div>

                <div className="mt-5 grid gap-3 text-sm text-white/86 sm:grid-cols-2">
                  <div>Город: {item.city || 'Не указан'}</div>
                  <div>Гостей: {item.guests_count || '—'}</div>
                  <div>Режим: {formatVenueMode(item.venue_mode)}</div>
                  <div>Основа: {item.selected_option || 'Не выбрана'}</div>
                </div>

                <div className="mt-5 flex items-center justify-between gap-3 pt-4 text-sm text-white/82">
                  <span>{item.budget ? `${item.budget.toLocaleString('ru-RU')} ₽` : 'Бюджет не указан'}</span>
                  <span className="font-semibold text-brand-orange">Открыть →</span>
                </div>
              </button>
            ))}
          </section>
        )}
      </div>
    </AppShell>
  )
}
