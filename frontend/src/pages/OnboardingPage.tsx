import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { updateMe } from '../api'
import { AppShell } from '../components/AppShell'
import { getSavedUser, getToken, saveUser } from '../storage'

const suggestions = ['Москва', 'Санкт-Петербург', 'Казань', 'Новосибирск', 'Екатеринбург']

export function OnboardingPage() {
  const navigate = useNavigate()
  const token = getToken()
  const savedUser = getSavedUser()
  const [region, setRegion] = useState(savedUser?.region || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const user = await updateMe(token, { region: region.trim() || null })
      saveUser(user)
      navigate('/events/new', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить регион')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell>
      <div className="mx-auto grid max-w-5xl gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="panel p-6 sm:p-8">
          <div className="text-sm uppercase tracking-[0.2em] text-slate-300">Шаг 1</div>
          <h1 className="mt-3 text-4xl font-black tracking-tight text-white">Укажи основной регион</h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-slate-300">
            Это нужно, чтобы агент подбирал места и идеи в твоём городе через 2ГИС. Регион можно поменять позже в профиле или в карточке конкретного события.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            {suggestions.map((item) => (
              <button key={item} type="button" onClick={() => setRegion(item)} className="chip">
                {item}
              </button>
            ))}
          </div>
        </section>

        <section className="panel p-6 sm:p-8">
          <label className="block">
            <span className="mb-2 block text-sm text-slate-300">Город или регион</span>
            <input className="field" value={region} onChange={(e) => setRegion(e.target.value)} placeholder="Например, Москва" />
          </label>
          {error ? <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div> : null}
          <div className="mt-6 flex flex-wrap gap-3">
            <button type="button" onClick={handleSave} className="primary-btn px-6 py-3" disabled={loading}>
              {loading ? 'Сохраняем...' : 'Продолжить'}
            </button>
            <button type="button" onClick={() => navigate('/events/new')} className="secondary-btn px-6 py-3">
              Пропустить пока
            </button>
          </div>
        </section>
      </div>
    </AppShell>
  )
}
