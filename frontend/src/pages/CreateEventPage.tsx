import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createEvent } from '../api'
import { AppShell } from '../components/AppShell'
import { getSavedUser, getToken } from '../storage'

const venueModes = [
  { value: 'outside', label: 'Хочу вне дома', note: 'Ищем кафе, рестораны, лофты, парки и другие места.' },
  { value: 'home', label: 'Скорее дома', note: 'Подберём домашний сценарий, доставку и активности.' },
  { value: 'undecided', label: 'Пока не решил(а)', note: 'Агент поможет определиться в чате.' },
]

export function CreateEventPage() {
  const navigate = useNavigate()
  const token = getToken()
  const user = getSavedUser()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    title: 'День рождения',
    event_date: '',
    budget: '50000',
    guests_count: '8',
    city: user?.region || '',
    venue_mode: 'undecided',
    notes: '',
  })

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return

    setLoading(true)
    setError('')

    try {
      const created = await createEvent(token, {
        title: form.title || 'День рождения',
        event_date: form.event_date || null,
        budget: form.budget ? Number(form.budget) : null,
        guests_count: form.guests_count ? Number(form.guests_count) : null,
        city: form.city || user?.region || null,
        venue_mode: form.venue_mode,
        format: form.venue_mode === 'outside' ? 'restaurant' : form.venue_mode === 'home' ? 'home' : 'mixed',
        notes: form.notes || null,
        status: 'draft',
      })
      navigate(`/events/${created.id}?tab=main`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать событие')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="mt-2 text-4xl font-black tracking-tight text-white sm:text-5xl">Собери черновик события за пару минут</h1>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-[1.12fr_0.88fr]">
          <section className="panel p-6 sm:p-8">
            <div className="grid gap-5 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="mb-2 block text-sm text-slate-300">Название события</span>
                <input className="field" value={form.title} onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))} placeholder="День рождения" />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-slate-300">Дата</span>
                <input className="field" type="date" value={form.event_date} onChange={(e) => setForm((prev) => ({ ...prev, event_date: e.target.value }))} />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-slate-300">Город</span>
                <input className="field" value={form.city} onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value }))} placeholder="Например, Москва" />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-slate-300">Общий бюджет</span>
                <input className="field" type="number" value={form.budget} onChange={(e) => setForm((prev) => ({ ...prev, budget: e.target.value }))} />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-slate-300">Сколько человек</span>
                <input className="field" type="number" value={form.guests_count} onChange={(e) => setForm((prev) => ({ ...prev, guests_count: e.target.value }))} />
              </label>
              <label className="block sm:col-span-2">
                <span className="mb-2 block text-sm text-slate-300">Что уже известно</span>
                <textarea className="field min-h-[150px] resize-none" value={form.notes} onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))} placeholder="Например: хочу что-то уютное, не слишком дорогое, можно с пикником или небольшим рестораном." />
              </label>
            </div>
          </section>

          <section className="panel p-6 sm:p-8">
            <div className="text-sm uppercase tracking-[0.24em] text-slate-300">Какое направление взять за основу?</div>
            <div className="mt-4 grid gap-3">
              {venueModes.map((item) => {
                const active = form.venue_mode === item.value
                return (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => setForm((prev) => ({ ...prev, venue_mode: item.value }))}
                    className={[
                      'rounded-3xl border p-4 text-left transition',
                      active ? 'border-orange-300 bg-orange-400/10' : 'border-white/10 bg-white/5 hover:bg-white/8',
                    ].join(' ')}
                  >
                    <div className="font-semibold text-white">{item.label}</div>
                    <div className="mt-2 text-sm leading-6 text-slate-300">{item.note}</div>
                  </button>
                )
              })}
            </div>

            {error ? <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div> : null}

            <button className="primary-btn mt-6 w-full justify-center px-6 py-3 text-base" type="submit" disabled={loading}>
              {loading ? 'Создаём событие...' : 'Перейти к выбору основы'}
            </button>
          </section>
        </form>
      </div>
    </AppShell>
  )
}
