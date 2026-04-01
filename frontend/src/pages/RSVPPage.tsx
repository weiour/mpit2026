import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

interface InvitationData {
  id: number
  event_title: string
  event_date?: string
  event_city?: string
  event_format?: string
  event_notes?: string
  guest_email: string
  guest_name?: string
  token: string
  status: string
}

export function RSVPPage() {
  const { token } = useParams<{ token: string }>()
  const [invitation, setInvitation] = useState<InvitationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitted, setSubmitted] = useState(false)
  
  // Form state
  const [attending, setAttending] = useState<boolean | null>(null)
  const [plusOnes, setPlusOnes] = useState(0)
  const [dietaryRestrictions, setDietaryRestrictions] = useState('')
  const [musicPreferences, setMusicPreferences] = useState('')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!token) return
    
    fetch(`http://localhost:8000/invitations/rsvp/${token}`)
      .then(res => {
        if (!res.ok) throw new Error('Приглашение не найдено')
        return res.json()
      })
      .then(data => {
        setInvitation(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [token])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (attending === null) return
    
    setSubmitting(true)
    try {
      const response = await fetch(`http://localhost:8000/invitations/rsvp/${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          attending,
          plus_ones: plusOnes,
          notes,
          dietary_restrictions: dietaryRestrictions,
          music_preferences: musicPreferences
        })
      })
      
      if (!response.ok) throw new Error('Не удалось отправить ответ')
      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-slate-300">Загрузка...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="panel p-8 text-center max-w-md">
          <div className="text-red-400 text-xl mb-4">⚠️</div>
          <h1 className="text-xl font-bold text-white mb-2">Ошибка</h1>
          <p className="text-slate-300">{error}</p>
        </div>
      </div>
    )
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="panel p-8 text-center max-w-md">
          <div className="text-green-400 text-4xl mb-4">✓</div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {attending ? 'Отлично!' : 'Поняли'}
          </h1>
          <p className="text-slate-300">
            {attending 
              ? 'Вы подтвердили участие. Ждём вас на мероприятии!' 
              : 'Вы отклонили приглашение. Спасибо за ответ!'}
          </p>
        </div>
      </div>
    )
  }

  if (!invitation) return null

  const guestName = invitation.guest_name || invitation.guest_email.split('@')[0]

  return (
    <div className="min-h-screen bg-slate-900 py-12 px-4">
      <div className="max-w-lg mx-auto">
        <div className="panel p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="text-sm uppercase tracking-[0.24em] text-slate-400 mb-2">
              Приглашение на мероприятие
            </div>
            <h1 className="text-3xl font-bold text-white mb-4">
              {invitation.event_title}
            </h1>
            {invitation.event_date && (
              <p className="text-lg text-slate-300 mb-1">
                📅 {invitation.event_date}
              </p>
            )}
            {invitation.event_city && (
              <p className="text-slate-400">
                📍 {invitation.event_city}
              </p>
            )}
          </div>

          {/* Greeting */}
          <div className="mb-8 p-4 rounded-2xl bg-white/5">
            <p className="text-slate-300">
              Привет, <span className="text-white font-semibold">{guestName}</span>!
            </p>
            <p className="text-slate-400 text-sm mt-2">
              Вас приглашают на мероприятие. Пожалуйста, подтвердите ваше участие.
            </p>
          </div>

          {/* Event Details */}
          {invitation.event_notes && (
            <div className="mb-6">
              <h3 className="text-sm uppercase tracking-[0.18em] text-white mb-2">
                О мероприятии
              </h3>
              <p className="text-slate-300 text-sm leading-relaxed">
                {invitation.event_notes}
              </p>
            </div>
          )}

          {/* RSVP Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Attending buttons */}
            <div>
              <label className="block text-sm text-slate-300 mb-3">
                Вы придёте? <span className="text-red-400">*</span>
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setAttending(true)}
                  className={`p-4 rounded-2xl border-2 transition-all ${
                    attending === true
                      ? 'border-green-500 bg-green-500/20 text-green-400'
                      : 'border-white/10 bg-white/5 text-slate-300 hover:border-white/20'
                  }`}
                >
                  <div className="text-2xl mb-2">✓</div>
                  Да, приду
                </button>
                <button
                  type="button"
                  onClick={() => setAttending(false)}
                  className={`p-4 rounded-2xl border-2 transition-all ${
                    attending === false
                      ? 'border-red-500 bg-red-500/20 text-red-400'
                      : 'border-white/10 bg-white/5 text-slate-300 hover:border-white/20'
                  }`}
                >
                  <div className="text-2xl mb-2">✕</div>
                  Не смогу
                </button>
              </div>
            </div>

            {/* Additional fields (only if attending) */}
            {attending === true && (
              <>
                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Сколько гостей с вами? (включая вас)
                  </label>
                  <select
                    value={plusOnes}
                    onChange={(e) => setPlusOnes(Number(e.target.value))}
                    className="field"
                  >
                    <option value={0}>Только я</option>
                    <option value={1}>Я + 1 гость</option>
                    <option value={2}>Я + 2 гостя</option>
                    <option value={3}>Я + 3 гостя</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Особенности питания (аллергии, предпочтения)
                  </label>
                  <textarea
                    value={dietaryRestrictions}
                    onChange={(e) => setDietaryRestrictions(e.target.value)}
                    placeholder="Например: вегетарианец, аллергия на орехи..."
                    className="field min-h-[80px] resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Музыкальные предпочтения
                  </label>
                  <input
                    type="text"
                    value={musicPreferences}
                    onChange={(e) => setMusicPreferences(e.target.value)}
                    placeholder="Какую музыку любите?"
                    className="field"
                  />
                </div>
              </>
            )}

            {/* Notes */}
            <div>
              <label className="block text-sm text-slate-300 mb-2">
                Комментарий (необязательно)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Ваши пожелания или вопросы..."
                className="field min-h-[80px] resize-none"
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={attending === null || submitting}
              className="primary-btn w-full px-6 py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Отправка...' : attending === true ? 'Подтвердить участие' : 'Отправить ответ'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
