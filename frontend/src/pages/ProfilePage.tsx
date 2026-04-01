import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { updateMe } from '../api'
import { AppShell } from '../components/AppShell'
import { clearSession, getSavedUser, getToken, saveUser } from '../storage'

export function ProfilePage() {
  const navigate = useNavigate()
  const token = getToken()
  const user = getSavedUser()
  const [name, setName] = useState(user?.name || '')
  const [region, setRegion] = useState(user?.region || '')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function handleSave(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const updated = await updateMe(token, { name, region })
      saveUser(updated)
      setMessage('Профиль обновлён')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить изменения')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell>
      <div className="mx-auto grid max-w-5xl gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="panel p-6 sm:p-8">
          <div className="text-sm uppercase tracking-[0.24em] text-slate-300">Профиль</div>
          <h1 className="mt-3 text-4xl font-black tracking-tight text-white">Личные настройки для работы агента</h1>
          <p className="mt-4 text-base leading-7 text-slate-300">
            Здесь хранится имя и основной регион. Регион используется как базовая точка для рекомендаций мест, но в самом событии его можно переопределить.
          </p>
          <div className="mt-6 rounded-[28px] border border-white/10 bg-white/5 p-5 text-sm leading-7 text-slate-300">
            Email: <span className="text-white">{user?.email}</span>
          </div>
        </section>

        <section className="panel p-6 sm:p-8">
          <form className="space-y-4" onSubmit={handleSave}>
            <label className="block">
              <span className="mb-2 block text-sm text-slate-300">Имя</span>
              <input className="field" value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-slate-300">Основной регион</span>
              <input className="field" value={region} onChange={(e) => setRegion(e.target.value)} placeholder="Например, Москва" />
            </label>

            {message ? <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">{message}</div> : null}
            {error ? <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div> : null}

            <div className="flex grid gap-3">
              <button className="primary-btn w-full px-6 py-3" type="submit" disabled={loading}>{loading ? 'Сохраняем...' : 'Сохранить'}</button>
              <button
                type="button"
                onClick={() => {
                  clearSession()
                  navigate('/auth', { replace: true })
                }}
                className="secondary-btn px-6 py-3"
              >
                Выйти из аккаунта
              </button>
            </div>
          </form>
        </section>
      </div>
    </AppShell>
  )
}
