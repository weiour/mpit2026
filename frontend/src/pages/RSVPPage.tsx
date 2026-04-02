import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

interface WishlistItem {
  id: number
  title: string
  description?: string
  url?: string
  price?: number
  priority?: string
  reserved_by_me?: boolean
  reserved_by_other?: boolean
  reserved_by_name?: string | null
}

interface InvitationData {
  id: number
  event_title: string
  event_date?: string
  event_city?: string
  event_format?: string
  event_notes?: string
  guest_email: string
  guest_name?: string
  is_birthday_person: boolean
  token: string
  status: string
  wishlist: WishlistItem[]
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
  const [reservingItemId, setReservingItemId] = useState<number | null>(null)
  
  // Birthday person state for adding gifts
  const [showAddGiftForm, setShowAddGiftForm] = useState(false)
  const [newGiftTitle, setNewGiftTitle] = useState('')
  const [newGiftDescription, setNewGiftDescription] = useState('')
  const [newGiftUrl, setNewGiftUrl] = useState('')
  const [newGiftPrice, setNewGiftPrice] = useState('')
  const [addingGift, setAddingGift] = useState(false)

  async function reserveItem(itemId: number) {
    if (!token) return
    setReservingItemId(itemId)
    try {
      const response = await fetch(`http://localhost:8000/invitations/rsvp/${token}/wishlist/${itemId}/reserve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (response.ok) {
        // Refresh invitation data
        const updated = await fetch(`http://localhost:8000/invitations/rsvp/${token}`).then(r => r.json())
        setInvitation(updated)
      }
    } catch (err) {
      console.error('Failed to reserve item:', err)
    } finally {
      setReservingItemId(null)
    }
  }

  async function releaseItem(itemId: number) {
    if (!token) return
    setReservingItemId(itemId)
    try {
      const response = await fetch(`http://localhost:8000/invitations/rsvp/${token}/wishlist/${itemId}/release`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (response.ok) {
        // Refresh invitation data
        const updated = await fetch(`http://localhost:8000/invitations/rsvp/${token}`).then(r => r.json())
        setInvitation(updated)
      }
    } catch (err) {
      console.error('Failed to release item:', err)
    } finally {
      setReservingItemId(null)
    }
  }

  async function addGift(e: React.FormEvent) {
    e.preventDefault()
    if (!token || !newGiftTitle.trim()) return
    
    setAddingGift(true)
    try {
      const response = await fetch(`http://localhost:8000/invitations/rsvp/${token}/wishlist/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newGiftTitle,
          description: newGiftDescription,
          url: newGiftUrl,
          price: newGiftPrice ? parseInt(newGiftPrice) : null,
          priority: 'medium'
        })
      })
      if (response.ok) {
        // Clear form and refresh
        setNewGiftTitle('')
        setNewGiftDescription('')
        setNewGiftUrl('')
        setNewGiftPrice('')
        setShowAddGiftForm(false)
        const updated = await fetch(`http://localhost:8000/invitations/rsvp/${token}`).then(r => r.json())
        setInvitation(updated)
      }
    } catch (err) {
      console.error('Failed to add gift:', err)
    } finally {
      setAddingGift(false)
    }
  }

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

          {/* Wishlist */}
          {invitation.wishlist && (
            <div className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-5">
              {invitation.is_birthday_person ? (
                // Birthday person view - can add gifts
                <>
                  <h3 className="text-sm uppercase tracking-[0.18em] text-white mb-4 flex items-center gap-2">
                    <span className="text-lg">🎁</span>
                    Ваш вишлист
                  </h3>
                  <p className="text-slate-400 text-sm mb-4">
                    Добавьте подарки, которые вы хотели бы получить. Гости увидят их и смогут забронировать.
                  </p>
                  
                  {/* Current wishlist */}
                  {invitation.wishlist.length > 0 && (
                    <div className="space-y-3 mb-4">
                      {invitation.wishlist.map((item) => (
                        <div
                          key={item.id}
                          className="rounded-xl border border-white/10 bg-white/5 p-4"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <h4 className="font-semibold text-white text-sm">{item.title}</h4>
                              {item.description && (
                                <p className="text-slate-400 text-xs mt-1">{item.description}</p>
                              )}
                              <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                {item.price !== undefined && item.price !== null && (
                                  <span className="text-slate-300 font-medium">{item.price.toLocaleString('ru-RU')} ₽</span>
                                )}
                                {item.reserved_by_other && (
                                  <span className="text-emerald-400">✓ Кто-то забронировал</span>
                                )}
                              </div>
                            </div>
                            {item.url && (
                              <a
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                                className="shrink-0 rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white hover:bg-white/20 transition"
                              >
                                Смотреть →
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Add gift button/form */}
                  {!showAddGiftForm ? (
                    <button
                      onClick={() => setShowAddGiftForm(true)}
                      className="w-full rounded-xl border border-dashed border-white/20 bg-white/5 p-4 text-slate-400 hover:text-white hover:border-white/40 transition"
                    >
                      + Добавить подарок
                    </button>
                  ) : (
                    <form onSubmit={addGift} className="space-y-3 rounded-xl border border-white/20 bg-white/10 p-4">
                      <h4 className="text-white font-medium text-sm">Новый подарок</h4>
                      <input
                        type="text"
                        value={newGiftTitle}
                        onChange={(e) => setNewGiftTitle(e.target.value)}
                        placeholder="Название подарка *"
                        className="field w-full text-sm"
                        required
                      />
                      <textarea
                        value={newGiftDescription}
                        onChange={(e) => setNewGiftDescription(e.target.value)}
                        placeholder="Описание (необязательно)"
                        className="field w-full text-sm min-h-[60px] resize-none"
                      />
                      <input
                        type="url"
                        value={newGiftUrl}
                        onChange={(e) => setNewGiftUrl(e.target.value)}
                        placeholder="Ссылка на товар (необязательно)"
                        className="field w-full text-sm"
                      />
                      <input
                        type="number"
                        value={newGiftPrice}
                        onChange={(e) => setNewGiftPrice(e.target.value)}
                        placeholder="Цена в ₽ (необязательно)"
                        className="field w-full text-sm"
                      />
                      <div className="flex gap-2">
                        <button
                          type="submit"
                          disabled={addingGift || !newGiftTitle.trim()}
                          className="flex-1 rounded-lg bg-brand-orange px-4 py-2 text-sm text-white hover:brightness-110 transition disabled:opacity-50"
                        >
                          {addingGift ? 'Добавление...' : 'Добавить'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowAddGiftForm(false)}
                          className="rounded-lg border border-white/20 px-4 py-2 text-sm text-slate-300 hover:bg-white/10 transition"
                        >
                          Отмена
                        </button>
                      </div>
                    </form>
                  )}
                </>
              ) : (
                // Regular guest view - can reserve gifts
                invitation.wishlist.length > 0 && (
                  <>
                    <h3 className="text-sm uppercase tracking-[0.18em] text-white mb-4 flex items-center gap-2">
                      <span className="text-lg">🎁</span>
                      Вишлист именинника
                    </h3>
                    <p className="text-slate-400 text-sm mb-4">
                      Если вы хотите сделать подарок, вот идеи от именинника. Вы можете забронировать подарок, чтобы другие гости знали, что этот подарок уже будет от вас:
                    </p>
                    <div className="space-y-3">
                      {invitation.wishlist.map((item) => (
                        <div
                          key={item.id}
                          className={`rounded-xl border p-4 transition ${
                            item.reserved_by_me
                              ? 'border-emerald-500/30 bg-emerald-500/10'
                              : item.reserved_by_other
                              ? 'border-amber-500/30 bg-amber-500/10 opacity-70'
                              : 'border-white/10 bg-white/5 hover:border-white/20'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h4 className={`font-semibold text-sm ${item.reserved_by_other ? 'text-slate-400' : 'text-white'}`}>
                                  {item.title}
                                </h4>
                                {item.reserved_by_me && (
                                  <span className="text-xs text-emerald-400 font-medium">✓ Вы забронировали</span>
                                )}
                                {item.reserved_by_other && (
                                  <span className="text-xs text-amber-400 font-medium">
                                    🔒 Забронировано{item.reserved_by_name ? ` ${item.reserved_by_name}` : ''}
                                  </span>
                                )}
                              </div>
                              {item.description && (
                                <p className={`text-xs mt-1 line-clamp-2 ${item.reserved_by_other ? 'text-slate-500' : 'text-slate-400'}`}>
                                  {item.description}
                                </p>
                              )}
                              <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                {item.price !== undefined && item.price !== null && (
                                  <span className={item.reserved_by_other ? 'text-slate-500' : 'text-slate-300 font-medium'}>
                                    {item.price.toLocaleString('ru-RU')} ₽
                                  </span>
                                )}
                                {item.priority === 'high' && !item.reserved_by_other && (
                                  <span className="text-amber-400">★ Приоритетно</span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {item.url && !item.reserved_by_other && (
                                <a
                                  href={item.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="shrink-0 rounded-lg bg-white/10 px-3 py-1.5 text-xs text-white hover:bg-white/20 transition"
                                >
                                  Смотреть →
                                </a>
                              )}
                              {item.reserved_by_me ? (
                                <button
                                  onClick={() => releaseItem(item.id)}
                                  disabled={reservingItemId === item.id}
                                  className="shrink-0 rounded-lg border border-emerald-500/30 px-3 py-1.5 text-xs text-emerald-400 hover:bg-emerald-500/20 transition disabled:opacity-50"
                                >
                                  {reservingItemId === item.id ? '...' : 'Отменить'}
                                </button>
                              ) : !item.reserved_by_other ? (
                                <button
                                  onClick={() => reserveItem(item.id)}
                                  disabled={reservingItemId === item.id}
                                  className="shrink-0 rounded-lg bg-brand-orange px-3 py-1.5 text-xs text-white hover:brightness-110 transition disabled:opacity-50"
                                >
                                  {reservingItemId === item.id ? '...' : 'Забронировать'}
                                </button>
                              ) : null}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )
              )}
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
