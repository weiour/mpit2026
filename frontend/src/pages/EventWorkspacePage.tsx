import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import MarkdownMessage from '../components/MarkdownMessage'
import AssistantMessageActions from '../components/AssistantMessageActions'
import { AppShell } from '../components/AppShell'
import {
  API_URL,
  getChatHistory,
  getEvent,
  getEventRecommendations,
  sendChatMessage,
  updateEvent,
} from '../api'
import { getSavedUser, getToken } from '../storage'
import type { ChatAction, ChatMessage, EventItem, RecommendationsResponse } from '../types'
import { formatEventFormat, formatEventStatus, formatVenueMode } from '../utils/eventLabels'

const homeIdeas = [
  {
    title: 'Домашний стол + доставка',
    description: 'Уютный вариант, если хочется провести праздник спокойно и без сложной подготовки.',
  },
  {
    title: 'Тематический вечер',
    description: 'Фильм, настолки, квиз или вечер по интересам — легко собрать и подстроить под компанию.',
  },
  {
    title: 'Камерный пикник дома',
    description: 'Пледы, закуски, музыка и простая программа — ощущается как пикник, но без риска из-за погоды.',
  },
] as const

const allTabs = [
  { id: 'overview', label: 'Событие' },
  { id: 'main', label: 'Основа' },
  { id: 'guests', label: 'Гости' },
  { id: 'gifts', label: 'Подарки' },
  { id: 'backup', label: 'План Б' },
] as const

type TabId = (typeof allTabs)[number]['id']

type WishlistItem = {
  id: number
  title: string
  description?: string | null
  url?: string | null
  price?: number | null
  priority?: string | null
}

type InvitationItem = {
  id: number
  guest_name?: string | null
  guest_email: string
  guest_phone?: string | null
  status: string
  sent_at?: string | null
}

type InvitationStats = {
  total_guests: number
  accepted: number
  sent: number
  pending: number
  attending_count: number
  plus_ones_count: number
}

type EventEditForm = {
  title: string
  event_date: string
  city: string
  budget: string
  guests_count: string
  notes: string
}

type BackupIdea = {
  raw: string
  title: string
  note?: string | null
}

function formatDate(value?: string | null) {
  if (!value) return 'Дата не указана'
  return value
}

function getDefaultTab(item: EventItem | null): TabId {
  return item?.selected_option ? 'overview' : 'main'
}

function parseBackupIdeas(notes?: string | null): BackupIdea[] {
  if (!notes) return []
  return notes
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('План Б:'))
    .map((line) => line.replace(/^План Б:\s*/, ''))
    .map((line) => {
      const [title, note] = line.split(/\s+[—-]\s+/, 2)
      return {
        raw: line,
        title: title?.trim() || line,
        note: note?.trim() || null,
      }
    })
}


function appendLine(text: string | null | undefined, line: string) {
  const normalized = (text || '').trim()
  if (!normalized) return line
  if (normalized.includes(line)) return normalized
  return `${normalized}\n${line}`
}

function mapIncomingTab(value: string | null, hasMainPlan: boolean): TabId {
  switch (value) {
    case 'overview':
    case 'main':
    case 'guests':
    case 'gifts':
    case 'backup':
      return value
    case 'places':
      return 'main'
    case 'chat':
      return hasMainPlan ? 'overview' : 'main'
    default:
      return hasMainPlan ? 'overview' : 'main'
  }
}

function buildQuickReplies(event: EventItem | null, activeTab: TabId) {
  if (!event) return []
  if (!event.selected_option) {
    return ['Сделай вариант подешевле', 'Предложи более уютный формат', 'Нужен план Б на плохую погоду']
  }
  if (activeTab === 'gifts') {
    return ['Подбери 3 подарка до 3000 ₽', 'Сделай идеи более оригинальными', 'Что можно добавить в вишлист?']
  }
  if (activeTab === 'guests') {
    return ['Напиши короткое приглашение', 'Как лучше позвать гостей?', 'Что уточнить у гостей заранее?']
  }
  if (activeTab === 'backup') {
    return ['Подбери ещё один план Б', 'Нужен запасной вариант на дождь', 'Как быстро сменить формат?']
  }
  return ['Как улучшить это событие?', 'Помоги сократить бюджет', 'Что ещё стоит продумать?']
}

function buildSyntheticIntro(event: EventItem | null, userRegion?: string | null) {
  if (!event) return ''
  if (!event.selected_option) {
    return `Я помогу собрать основу события. Сначала выбери **главный вариант**, и после этого событие можно будет спокойно редактировать, звать гостей и вести подарки.\n\nСейчас у нас есть:\n- **${event.title}**\n- дата: **${formatDate(event.event_date)}**\n- город: **${event.city || userRegion || 'не указан'}**\n- режим: **${formatVenueMode(event.venue_mode)}**`
  }

  return `Событие уже собрано вокруг основы **${event.selected_option}**.\n\nТеперь я могу помочь с подарками, приглашениями, бюджетом и планом Б.`
}

function getStatusBadge(status?: string | null) {
  switch (status) {
    case 'ready':
      return 'rounded-full border border-emerald-300/25 bg-emerald-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-100'
    case 'concept_selected':
      return 'rounded-full border border-blue-300/25 bg-blue-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-blue-100'
    default:
      return 'rounded-full border border-white/12 bg-white/8 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-white/82'
  }
}

export function EventWorkspacePage() {
  const { eventId } = useParams<{ eventId: string }>()
  const token = getToken()
  const user = getSavedUser()
  const [searchParams, setSearchParams] = useSearchParams()
  const [event, setEvent] = useState<EventItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null)
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)
  const [recommendationsError, setRecommendationsError] = useState('')
  const [savingOverview, setSavingOverview] = useState(false)
  const [savingGuests, setSavingGuests] = useState(false)
  const [wishlistItems, setWishlistItems] = useState<WishlistItem[]>([])
  const [showAddGiftForm, setShowAddGiftForm] = useState(false)
  const [newGift, setNewGift] = useState({ title: '', description: '', url: '', price: '', priority: 'medium' })
  const [wishlistLoading, setWishlistLoading] = useState(false)
  const [invitations, setInvitations] = useState<InvitationItem[]>([])
  const [invitationsLoading, setInvitationsLoading] = useState(false)
  const [invitationsError, setInvitationsError] = useState('')
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [newGuestName, setNewGuestName] = useState('')
  const [newGuestEmail, setNewGuestEmail] = useState('')
  const [newGuestPhone, setNewGuestPhone] = useState('')
  const [isBirthdayPerson, setIsBirthdayPerson] = useState(false)
  const [inviteMessage, setInviteMessage] = useState('')
  const [guestDraft, setGuestDraft] = useState('')
  const [sendingInvites, setSendingInvites] = useState(false)
  const [inviteStats, setInviteStats] = useState<InvitationStats | null>(null)
  const [editForm, setEditForm] = useState<EventEditForm>({
    title: '',
    event_date: '',
    city: '',
    budget: '',
    guests_count: '',
    notes: '',
  })

  const chatViewportRef = useRef<HTMLDivElement | null>(null)
  const assistantOpen = searchParams.get('assistant') === 'open'
  const hasMainPlan = Boolean(event?.selected_option)
  const visibleTabs = hasMainPlan ? allTabs.filter((tab) => tab.id !== 'main') : allTabs.filter((tab) => tab.id !== 'guests' && tab.id !== 'gifts')
  const activeTab = mapIncomingTab(searchParams.get('tab'), hasMainPlan)
  const quickReplies = useMemo(() => buildQuickReplies(event, activeTab), [event, activeTab])
  const backupIdeas = useMemo(() => parseBackupIdeas(editForm.notes), [editForm.notes])
  const syntheticIntro = useMemo(() => buildSyntheticIntro(event, user?.region), [event, user?.region])

  function applyEventState(data: EventItem, options?: { syncGuestDraft?: boolean }) {
    setEvent(data)
    setEditForm({
      title: data.title || '',
      event_date: data.event_date || '',
      city: data.city || user?.region || '',
      budget: data.budget != null ? String(data.budget) : '',
      guests_count: data.guests_count != null ? String(data.guests_count) : '',
      notes: data.notes || '',
    })
    if (options?.syncGuestDraft) {
      setGuestDraft((data.guest_emails || []).join('\n'))
    }
  }

  async function refreshEventState(options?: { syncGuestDraft?: boolean; refreshWishlist?: boolean; refreshInvitations?: boolean }) {
    if (!token || !eventId) return
    try {
      const data = await getEvent(token, Number(eventId))
      applyEventState(data, { syncGuestDraft: options?.syncGuestDraft })
      if (options?.refreshWishlist) {
        await loadWishlist()
      }
      if (options?.refreshInvitations) {
        await loadInvitations()
        await loadInvitationStats()
      }
    } catch (err) {
      console.error('Failed to refresh event state:', err)
    }
  }

  function updateQuery(next: { tab?: TabId; assistant?: boolean }) {
    const params = new URLSearchParams(searchParams)
    if (next.tab) params.set('tab', next.tab)
    if (next.assistant === undefined) {
      // keep current state
    } else if (next.assistant) {
      params.set('assistant', 'open')
    } else {
      params.delete('assistant')
    }
    setSearchParams(params)
  }

  function openAssistant(prompt?: string, tab?: TabId) {
    if (prompt) setDraft(prompt)
    updateQuery({ tab, assistant: true })
  }

  function closeAssistant() {
    updateQuery({ assistant: false })
  }

  useEffect(() => {
    if (!token || !eventId) return
    let active = true
    setLoading(true)
    getEvent(token, Number(eventId))
      .then((data) => {
        if (!active) return
        applyEventState(data, { syncGuestDraft: true })

        const requestedTab = searchParams.get('tab')
        if (!requestedTab) {
          const params = new URLSearchParams(searchParams)
          params.set('tab', getDefaultTab(data))
          setSearchParams(params)
        }
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'Не удалось загрузить событие')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [token, eventId])

  useEffect(() => {
    if (!assistantOpen || !token || !eventId) return
    let active = true
    getChatHistory(token, Number(eventId))
      .then((data) => {
        if (active) setMessages(data)
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'Не удалось загрузить чат')
      })
    return () => {
      active = false
    }
  }, [assistantOpen, token, eventId])

  useEffect(() => {
    if (!assistantOpen) return
    const el = chatViewportRef.current
    if (!el) return
    requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight
    })
  }, [assistantOpen, messages.length, sending])

  useEffect(() => {
    if (!assistantOpen && !showInviteForm) {
      document.body.style.overflow = ''
      return
    }

    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [assistantOpen, showInviteForm])

  useEffect(() => {
    if (!token || !eventId || activeTab !== 'main' || !event || event.venue_mode === 'home') return
    if (recommendations || recommendationsLoading) return
    void loadRecommendations()
  }, [token, eventId, activeTab, event, recommendations, recommendationsLoading])

  useEffect(() => {
    if (!token || !eventId || activeTab !== 'gifts' || !hasMainPlan) return
    if (wishlistItems.length > 0 || wishlistLoading) return
    void loadWishlist()
  }, [token, eventId, activeTab, hasMainPlan, wishlistItems.length, wishlistLoading])

  useEffect(() => {
    if (!token || !eventId || activeTab !== 'guests' || !hasMainPlan) return
    void loadInvitations()
    void loadInvitationStats()
  }, [token, eventId, activeTab, hasMainPlan])

  async function loadRecommendations() {
    if (!token || !eventId || !event) return
    setRecommendationsLoading(true)
    setRecommendationsError('')
    try {
      const data = await getEventRecommendations(token, Number(eventId), {
        city: event.city || user?.region || undefined,
        limit: 5,
      })
      setRecommendations(data)
    } catch (err) {
      setRecommendationsError(err instanceof Error ? err.message : 'Не удалось получить варианты')
    } finally {
      setRecommendationsLoading(false)
    }
  }

  async function loadWishlist() {
    if (!token || !eventId) return
    setWishlistLoading(true)
    try {
      const response = await fetch(`${API_URL}/events/${eventId}/wishlist`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const items = (await response.json()) as WishlistItem[]
        setWishlistItems(items)
      }
    } catch (err) {
      console.error('Failed to load wishlist:', err)
    } finally {
      setWishlistLoading(false)
    }
  }

  async function addWishlistItem() {
    if (!token || !eventId || !newGift.title.trim()) return
    try {
      const response = await fetch(`${API_URL}/events/${eventId}/wishlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...newGift,
          price: newGift.price ? parseInt(newGift.price, 10) : null,
        }),
      })
      if (response.ok) {
        const item = (await response.json()) as WishlistItem
        setWishlistItems((prev) => [...prev, item])
        setNewGift({ title: '', description: '', url: '', price: '', priority: 'medium' })
        setShowAddGiftForm(false)
      }
    } catch (err) {
      console.error('Failed to add wishlist item:', err)
    }
  }

  async function deleteWishlistItem(itemId: number) {
    if (!token || !eventId) return
    try {
      const response = await fetch(`${API_URL}/wishlist/${itemId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        setWishlistItems((prev) => prev.filter((item) => item.id !== itemId))
      }
    } catch (err) {
      console.error('Failed to delete wishlist item:', err)
    }
  }

  async function handleSendMessage(message?: string) {
    const text = (message ?? draft).trim()
    if (!token || !eventId || !text) return
    setSending(true)
    setDraft('')
    setError('')
    try {
      const response = await sendChatMessage(token, Number(eventId), text)
      setMessages((prev) => [...prev, response.user_message, response.assistant_message])
      await refreshEventState({
        refreshWishlist: activeTab === 'gifts' || /подар|вишлист|wishlist/i.test(text),
        refreshInvitations: activeTab === 'guests',
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить сообщение')
      setDraft(text)
    } finally {
      setSending(false)
    }
  }

  async function handleChatAction(action: ChatAction) {
    if (action.kind === 'open_tab' && action.target_tab) {
      const nextTab = mapIncomingTab(action.target_tab, Boolean(event?.selected_option))
      if (action.target_tab === 'chat') {
        openAssistant(undefined, nextTab)
        return
      }
      updateQuery({ tab: nextTab })
      return
    }
    if (action.kind === 'send_prompt' && action.prompt) {
      await handleSendMessage(action.prompt)
    }
  }

  async function applySelection(selected: { title: string; kind: string; mode?: string; note?: string }, asBackup = false) {
    if (!token || !eventId || !event) return
    const backupLine = selected.note
      ? `План Б: ${selected.title} — ${selected.note}`
      : `План Б: ${selected.title}`

    const payload = asBackup
      ? {
          notes: appendLine(editForm.notes, backupLine),
        }
      : {
          selected_option: selected.title,
          selected_option_kind: selected.kind,
          venue_mode: selected.mode || event.venue_mode || null,
          status: 'ready',
          notes: selected.note
            ? appendLine(editForm.notes, `Основа события: ${selected.title} — ${selected.note}`)
            : editForm.notes || null,
        }

    const updated = await updateEvent(token, Number(eventId), payload)
    applyEventState(updated)

    if (asBackup) {
      updateQuery({ tab: 'backup' })
    } else {
      updateQuery({ tab: 'overview' })
    }
  }

  async function makeBackupMain(idea: BackupIdea) {
    if (!token || !eventId || !event) return
    try {
      const nextNotes = event.selected_option && event.selected_option !== idea.title
        ? appendLine(editForm.notes, `План Б: ${event.selected_option}`)
        : editForm.notes || null

      const updated = await updateEvent(token, Number(eventId), {
        selected_option: idea.title,
        selected_option_kind: 'backup_plan',
        status: 'ready',
        notes: nextNotes,
      })
      applyEventState(updated)
      updateQuery({ tab: 'overview' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сделать план Б основным')
    }
  }

  async function saveOverview() {
    if (!token || !eventId || !event) return
    setSavingOverview(true)
    try {
      const updated = await updateEvent(token, Number(eventId), {
        title: editForm.title.trim() || event.title,
        event_date: editForm.event_date || null,
        city: editForm.city.trim() || null,
        budget: editForm.budget ? Number(editForm.budget) : null,
        guests_count: editForm.guests_count ? Number(editForm.guests_count) : null,
        notes: editForm.notes.trim() || null,
        status: event.selected_option ? event.status || 'ready' : 'draft',
      })
      applyEventState(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить событие')
    } finally {
      setSavingOverview(false)
    }
  }

  async function saveGuests() {
    if (!token || !eventId || !event) return
    setSavingGuests(true)
    try {
      const emails = guestDraft
        .split(/[\n,]/g)
        .map((item) => item.trim())
        .filter(Boolean)
      const updated = await updateEvent(token, Number(eventId), {
        guest_emails: emails,
        status: event.selected_option ? 'ready' : event.status || 'draft',
      })
      applyEventState(updated, { syncGuestDraft: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить гостей')
    } finally {
      setSavingGuests(false)
    }
  }

  async function loadInvitations() {
    if (!token || !eventId) return
    setInvitationsLoading(true)
    setInvitationsError('')
    try {
      const response = await fetch(`${API_URL}/events/${eventId}/invitations`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = (await response.json()) as InvitationItem[]
        setInvitations(data)
      } else {
        const responseText = await response.text()
        setInvitationsError(responseText)
      }
    } catch (err) {
      console.error('Failed to load invitations:', err)
      setInvitationsError('Не удалось загрузить список гостей')
    } finally {
      setInvitationsLoading(false)
    }
  }

  async function loadInvitationStats() {
    if (!token || !eventId) return
    try {
      const response = await fetch(`${API_URL}/events/${eventId}/invitations/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        const data = (await response.json()) as InvitationStats
        setInviteStats(data)
      }
    } catch (err) {
      console.error('Failed to load invitation stats:', err)
    }
  }

  async function sendInvitations() {
    if (!token || !eventId) return
    setSendingInvites(true)
    setInvitationsError('')
    try {
      const guestList: Array<{ email: string; name?: string; phone?: string; is_birthday_person?: boolean }> = guestDraft
        .split(/[\n,]/g)
        .map((item) => item.trim())
        .filter(Boolean)
        .map((email) => ({ email }))

      if (guestList.length === 0 && !newGuestEmail.trim()) {
        setInvitationsError('Добавьте хотя бы одного гостя')
        return
      }

      if (newGuestEmail.trim()) {
        guestList.push({
          email: newGuestEmail.trim(),
          name: newGuestName.trim() || undefined,
          phone: newGuestPhone.trim() || undefined,
          is_birthday_person: isBirthdayPerson,
        })
      }

      const response = await fetch(`${API_URL}/events/${eventId}/invitations/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          guests: guestList,
          message_template: inviteMessage.trim() || undefined,
          send_via: 'email',
          ai_personalization: true,
        }),
      })

      if (response.ok) {
        setGuestDraft('')
        setNewGuestName('')
        setNewGuestEmail('')
        setNewGuestPhone('')
        setIsBirthdayPerson(false)
        setInviteMessage('')
        setShowInviteForm(false)
        await loadInvitations()
        await loadInvitationStats()
      } else {
        const responseText = await response.text()
        setInvitationsError(responseText)
      }
    } catch (err) {
      console.error('Failed to send invitations:', err)
      setInvitationsError('Не удалось отправить приглашения')
    } finally {
      setSendingInvites(false)
    }
  }

  async function resendInvitation(invitationId: number) {
    if (!token || !eventId) return
    try {
      const response = await fetch(`${API_URL}/events/${eventId}/invitations/${invitationId}/resend`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        await loadInvitations()
      }
    } catch (err) {
      console.error('Failed to resend invitation:', err)
    }
  }

  async function deleteInvitation(invitationId: number) {
    if (!token || !eventId) return
    if (!window.confirm('Удалить этого гостя?')) return
    try {
      const response = await fetch(`${API_URL}/events/${eventId}/invitations/${invitationId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.ok) {
        await loadInvitations()
        await loadInvitationStats()
      }
    } catch (err) {
      console.error('Failed to delete invitation:', err)
    }
  }

  function getInvitationStatus(status: string) {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-500/20 text-yellow-100',
      sent: 'bg-blue-500/20 text-blue-100',
      delivered: 'bg-blue-500/20 text-blue-100',
      opened: 'bg-purple-500/20 text-purple-100',
      accepted: 'bg-emerald-500/20 text-emerald-100',
      declined: 'bg-red-500/20 text-red-100',
      bounced: 'bg-red-500/20 text-red-100',
    }
    const labels: Record<string, string> = {
      pending: 'Ожидает',
      sent: 'Отправлено',
      delivered: 'Доставлено',
      opened: 'Открыто',
      accepted: 'Подтвердил',
      declined: 'Отклонил',
      bounced: 'Ошибка',
    }

    return (
      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${styles[status] || 'bg-white/10 text-white/80'}`}>
        {labels[status] || status}
      </span>
    )
  }

  if (loading) {
    return (
      <AppShell>
        <div className="panel p-8 text-white/85">Загружаем рабочее пространство...</div>
      </AppShell>
    )
  }

  if (!event) {
    return (
      <AppShell>
        <div className="panel p-8 text-white/85">Событие не найдено.</div>
      </AppShell>
    )
  }

  const pageLead = hasMainPlan
    ? 'Основа уже выбрана. Теперь можно спокойно редактировать событие, звать гостей и собирать подарки.'
    : 'Сейчас это черновик. Сначала выбери основной вариант, и только после этого событие станет рабочим.'

  return (
    <AppShell hideFooter={assistantOpen || showInviteForm} hideHeader={assistantOpen || showInviteForm}>
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="panel p-6 sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <div className="flex flex-wrap items-center gap-3">
                <span className={getStatusBadge(event.status)}>{formatEventStatus(event.status, 'compact')}</span>
                {event.selected_option ? (
                  <span className="rounded-full border border-white/12 bg-white/8 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-white/82">
                    Основа: {event.selected_option}
                  </span>
                ) : null}
              </div>
              <h1 className="mt-4 text-3xl font-black tracking-tight text-white sm:text-4xl">{event.title}</h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-white/82 sm:text-base">{pageLead}</p>
            </div>

            <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
              <button
                type="button"
                onClick={() => openAssistant(undefined, activeTab)}
                className="primary-btn w-full justify-center px-5 py-3 sm:w-auto"
              >
                Спросить Otmech.AI
              </button>
              <button
                type="button"
                onClick={() => {
                  updateQuery({ tab: 'main' })
                  openAssistant('Хочу поменять основной вариант события и подобрать новый план Б.', 'main')
                }}
                className="secondary-btn w-full justify-center px-5 py-3 sm:w-auto"
              >
                Ред. событие
              </button>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-white/88">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/58">Дата</div>
              <div className="mt-2 text-base font-semibold text-white">{formatDate(event.event_date)}</div>
            </div>
            <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-white/88">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/58">Город</div>
              <div className="mt-2 text-base font-semibold text-white">{event.city || user?.region || 'Не указан'}</div>
            </div>
            <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-white/88">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/58">Бюджет</div>
              <div className="mt-2 text-base font-semibold text-white">{event.budget ? `${event.budget.toLocaleString('ru-RU')} ₽` : 'Не указан'}</div>
            </div>
            <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-white/88">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/58">Формат</div>
              <div className="mt-2 text-base font-semibold text-white">{formatEventFormat(event.format)}</div>
            </div>
          </div>
        </section>

        <div className="flex flex-wrap gap-2">
          {visibleTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => updateQuery({ tab: tab.id })}
              className={[
                'rounded-full px-4 py-2 text-sm font-semibold transition',
                activeTab === tab.id ? 'bg-brand-orange text-white' : 'bg-blue-500/60 text-white/85 hover:bg-white/14',
              ].join(' ')}
            >
              {tab.label}
            </button>
          ))}
          {!visibleTabs.some((tab) => tab.id === activeTab) && activeTab === 'main' ? (
            <button type="button" className="rounded-full bg-white/12 px-4 py-2 text-sm font-semibold text-white">
              Основа
            </button>
          ) : null}
        </div>

        {error ? <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div> : null}

        {activeTab === 'overview' && hasMainPlan ? (
          <section className="grid gap-6 lg:grid-cols-[0.98fr_1.02fr]">
            <article className="panel p-6 sm:p-8">
              <div className="text-sm uppercase tracking-[0.24em] text-white/70">Текущая основа</div>
              <h2 className="mt-3 text-3xl font-bold text-white">{event.selected_option}</h2>
              <p className="mt-3 text-sm leading-7 text-white/84">
                Это текущий основной вариант события. Если захочешь заменить его, нажми <strong>«Ред. событие»</strong> — помощник
                сразу начнёт пересборку сценария.
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-[20px] border border-white/10 bg-white/6 p-4 text-white/84">Режим: <span className="text-white">{formatVenueMode(event.venue_mode)}</span></div>
                <div className="rounded-[20px] border border-white/10 bg-white/6 p-4 text-white/84">Статус: <span className="text-white">{formatEventStatus(event.status)}</span></div>
              </div>

              {event.venue_mode === 'outside' && event.selected_option && event.city && (
                <div className="mt-5 rounded-[20px] border border-white/10 bg-white/6 p-4">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/55 mb-3">Забронировать / Найти на карте</div>
                  <div className="flex flex-wrap gap-2">
                    <a
                      href={`https://2gis.ru/search/${encodeURIComponent(event.city + ' ' + event.selected_option)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 rounded-[14px] bg-[#00b4f0] px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
                    >
                      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                      </svg>
                      2GIS
                    </a>
                    <a
                      href={`https://yandex.ru/maps/?text=${encodeURIComponent(event.city + ' ' + event.selected_option)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 rounded-[14px] bg-[#fc3f1d] px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
                    >
                      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                      </svg>
                      Яндекс Карты
                    </a>
                  </div>
                </div>
              )}
            </article>

            <article className="panel p-6 sm:p-8">
              <div className="text-sm uppercase tracking-[0.24em] text-white/70">Редактирование события</div>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <label className="block sm:col-span-2">
                  <span className="mb-2 block text-sm text-white/80">Название</span>
                  <input className="field" value={editForm.title} onChange={(e) => setEditForm((prev) => ({ ...prev, title: e.target.value }))} />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-white/80">Дата</span>
                  <input className="field" type="date" value={editForm.event_date} onChange={(e) => setEditForm((prev) => ({ ...prev, event_date: e.target.value }))} />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-white/80">Город</span>
                  <input className="field" value={editForm.city} onChange={(e) => setEditForm((prev) => ({ ...prev, city: e.target.value }))} />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-white/80">Бюджет</span>
                  <input className="field" type="number" value={editForm.budget} onChange={(e) => setEditForm((prev) => ({ ...prev, budget: e.target.value }))} />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-white/80">Сколько гостей</span>
                  <input className="field" type="number" value={editForm.guests_count} onChange={(e) => setEditForm((prev) => ({ ...prev, guests_count: e.target.value }))} />
                </label>
                <label className="block sm:col-span-2">
                  <span className="mb-2 block text-sm text-white/80">Заметки и ограничения</span>
                  <textarea
                    className="field min-h-[180px] resize-none"
                    value={editForm.notes}
                    onChange={(e) => setEditForm((prev) => ({ ...prev, notes: e.target.value }))}
                    placeholder="Что важно учесть по формату, бюджету, погоде или предпочтениям гостей"
                  />
                </label>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button type="button" onClick={saveOverview} className="primary-btn px-6 py-3" disabled={savingOverview}>
                  {savingOverview ? 'Сохраняем...' : 'Сохранить'}
                </button>
                <button
                  type="button"
                  onClick={() => openAssistant('Хочу пересобрать это событие под новые условия.', 'main')}
                  className="secondary-btn px-6 py-3"
                >
                  Пересобрать с помощником
                </button>
              </div>
            </article>
          </section>
        ) : null}

        {activeTab === 'main' ? (
          <section className="space-y-4">
            <article className="panel p-6 sm:p-8">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="max-w-3xl">
                  <div className="text-sm uppercase tracking-[0.24em] text-white/70">Выбор основы</div>
                  <h2 className="mt-3 text-3xl font-bold text-white">
                    {hasMainPlan ? 'Сменить основную идею события' : 'Выбери основной вариант события'}
                  </h2>
                  <p className="mt-3 text-sm leading-7 text-white/84">
                    Как только выберешь основу, событие станет рабочим: можно будет спокойно редактировать детали, звать гостей и вести подарки.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => openAssistant('Помоги подобрать новую основу события и один запасной вариант.', 'main')}
                  className="primary-btn px-5 py-3"
                >
                  Уточнить с помощником
                </button>
              </div>
            </article>

            {event.venue_mode === 'home' ? (
              <div className="grid gap-4 xl:grid-cols-3">
                {homeIdeas.map((item) => (
                  <article key={item.title} className="panel flex h-full flex-col p-6">
                    <h3 className="text-2xl font-bold text-white">{item.title}</h3>
                    <p className="mt-3 flex-1 text-sm leading-7 text-white/86">{item.description}</p>
                    <div className="mt-5 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => void applySelection({ title: item.title, kind: 'home_plan', mode: 'home', note: item.description })}
                        className="primary-btn px-5 py-3"
                      >
                        Сделать основой
                      </button>
                      <button
                        type="button"
                        onClick={() => void applySelection({ title: item.title, kind: 'home_plan', mode: 'home', note: item.description }, true)}
                        className="secondary-btn px-5 py-3"
                      >
                        В план Б
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : recommendationsLoading ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="panel h-56 animate-pulse bg-white/5" />
                ))}
              </div>
            ) : recommendations ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {recommendations.items.map((item) => (
                  <article key={item.id} className="panel flex h-full flex-col p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-xs uppercase tracking-[0.18em] text-white/55">{item.source}</div>
                        <h3 className="mt-2 text-2xl font-bold text-white">{item.name}</h3>
                        <p className="mt-2 text-sm text-white/72">{item.address || 'Адрес уточняется'}</p>
                      </div>
                      <div className="rounded-[18px] border border-white/10 bg-white/6 px-3 py-2 text-sm text-white/82">
                        {item.rating != null ? `★ ${item.rating.toFixed(1)}` : 'Без рейтинга'}
                      </div>
                    </div>

                    <p className="mt-4 flex-1 text-sm leading-7 text-white/84">{item.reason}</p>

                    {item.tags.length ? (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {item.tags.map((tag) => (
                          <span key={`${item.id}-${tag}`} className="chip">
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    <div className="mt-5 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => void applySelection({ title: item.name, kind: 'venue', mode: 'outside', note: item.reason })}
                        className="primary-btn px-5 py-3"
                      >
                        Сделать основой
                      </button>
                      <button
                        type="button"
                        onClick={() => void applySelection({ title: item.name, kind: 'venue', mode: 'outside', note: item.reason }, true)}
                        className="secondary-btn px-5 py-3"
                      >
                        В план Б
                      </button>
                      {item.two_gis_url ? (
                        <a href={item.two_gis_url} target="_blank" rel="noreferrer" className="secondary-btn px-5 py-3">
                          Открыть в 2ГИС
                        </a>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <article className="panel p-6 text-white/82">
                {recommendationsError || 'Пока нет готовых вариантов. Можно попробовать уточнить город или попросить помощника предложить сценарий.'}
              </article>
            )}
          </section>
        ) : null}

        {activeTab === 'guests' && hasMainPlan ? (
          <section className="space-y-4">
            <article className="panel p-6 sm:p-8">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="text-sm uppercase tracking-[0.24em] text-white/70">Гости</div>
                  <h2 className="mt-3 text-3xl font-bold text-white">Приглашения и список гостей</h2>
                  <p className="mt-3 text-sm leading-7 text-white/84">После выбора основы можно звать гостей. Здесь оставил только нужные вещи: список, отправку и статусы.</p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={() => setShowInviteForm(true)} className="primary-btn px-5 py-3">
                    Добавить гостей
                  </button>
                  <button
                    type="button"
                    onClick={() => openAssistant('Напиши короткое приглашение для этого события.', 'guests')}
                    className="secondary-btn px-5 py-3"
                  >
                    Помощь с текстом
                  </button>
                </div>
              </div>
            </article>

            {invitationsError ? <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">{invitationsError}</div> : null}

            {inviteStats ? (
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-center text-white">
                  <div className="text-3xl font-black">{inviteStats.total_guests}</div>
                  <div className="mt-1 text-sm text-white/72">Всего гостей</div>
                </div>
                <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-center text-white">
                  <div className="text-3xl font-black text-brand-orange">{inviteStats.accepted}</div>
                  <div className="mt-1 text-sm text-white/72">Подтвердили</div>
                </div>
                <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-center text-white">
                  <div className="text-3xl font-black">{inviteStats.sent}</div>
                  <div className="mt-1 text-sm text-white/72">Отправлено</div>
                </div>
                <div className="rounded-[22px] border border-white/10 bg-white/6 p-4 text-center text-white">
                  <div className="text-3xl font-black">{inviteStats.pending}</div>
                  <div className="mt-1 text-sm text-white/72">Ожидают</div>
                </div>
              </div>
            ) : null}

            {invitationsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="panel h-24 animate-pulse bg-white/5" />
                ))}
              </div>
            ) : invitations.length > 0 ? (
              <div className="space-y-3">
                {invitations.map((inv) => (
                  <article key={inv.id} className="panel p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <h3 className="text-lg font-semibold text-white">{inv.guest_name || inv.guest_email.split('@')[0]}</h3>
                          {getInvitationStatus(inv.status)}
                        </div>
                        <p className="mt-2 text-sm text-white/74">{inv.guest_email}</p>
                        {inv.guest_phone ? <p className="mt-1 text-sm text-white/62">{inv.guest_phone}</p> : null}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {['pending', 'sent', 'delivered', 'bounced'].includes(inv.status) ? (
                          <button type="button" onClick={() => resendInvitation(inv.id)} className="secondary-btn px-4 py-2 text-sm">
                            Отправить повторно
                          </button>
                        ) : null}
                        <button type="button" onClick={() => deleteInvitation(inv.id)} className="secondary-btn px-4 py-2 text-sm">
                          Удалить
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <article className="panel p-8 text-center text-white/72">
                Список гостей пока пуст. После выбора основы можно сразу начать приглашать людей.
              </article>
            )}
          </section>
        ) : null}

        {activeTab === 'gifts' && hasMainPlan ? (
          <section className="space-y-4">
            <article className="panel p-6 sm:p-8">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="text-sm uppercase tracking-[0.24em] text-white/70">Подарки</div>
                  <h2 className="mt-3 text-3xl font-bold text-white">Вишлист и идеи</h2>
                  <p className="mt-3 text-sm leading-7 text-white/84">Здесь оставил только полезное: список подарков и быстрый доступ к помощнику для новых идей.</p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={() => setShowAddGiftForm((prev) => !prev)} className="primary-btn px-5 py-3">
                    {showAddGiftForm ? 'Скрыть форму' : 'Добавить подарок'}
                  </button>
                  <button
                    type="button"
                    onClick={() => openAssistant('Подбери 3 идеи подарка под это событие.', 'gifts')}
                    className="secondary-btn px-5 py-3"
                  >
                    Подобрать с помощником
                  </button>
                </div>
              </div>
            </article>

            {showAddGiftForm ? (
              <article className="panel p-6 sm:p-8">
                <div className="grid gap-4 md:grid-cols-2">
                  <input type="text" placeholder="Название подарка" className="field md:col-span-2" value={newGift.title} onChange={(e) => setNewGift((prev) => ({ ...prev, title: e.target.value }))} />
                  <input type="text" placeholder="Описание" className="field md:col-span-2" value={newGift.description} onChange={(e) => setNewGift((prev) => ({ ...prev, description: e.target.value }))} />
                  <input type="url" placeholder="Ссылка" className="field" value={newGift.url} onChange={(e) => setNewGift((prev) => ({ ...prev, url: e.target.value }))} />
                  <input type="number" placeholder="Цена" className="field" value={newGift.price} onChange={(e) => setNewGift((prev) => ({ ...prev, price: e.target.value }))} />
                </div>
                <div className="mt-4 flex gap-3">
                  <button type="button" onClick={addWishlistItem} className="primary-btn px-5 py-3" disabled={!newGift.title.trim()}>
                    Сохранить подарок
                  </button>
                </div>
              </article>
            ) : null}

            {wishlistLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="panel h-24 animate-pulse bg-white/5" />
                ))}
              </div>
            ) : wishlistItems.length > 0 ? (
              <div className="space-y-3">
                {wishlistItems.map((item) => (
                  <article key={item.id} className="panel p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                        {item.description ? <p className="mt-2 text-sm leading-6 text-white/76">{item.description}</p> : null}
                        <div className="mt-3 flex flex-wrap gap-3 text-sm text-white/65">
                          {item.price != null ? <span>{item.price.toLocaleString('ru-RU')} ₽</span> : null}
                          {item.priority ? <span>Приоритет: {item.priority}</span> : null}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {item.url ? (
                          <a href={item.url} target="_blank" rel="noreferrer" className="secondary-btn px-4 py-2 text-sm">
                            Открыть
                          </a>
                        ) : null}
                        <button type="button" onClick={() => deleteWishlistItem(item.id)} className="secondary-btn px-4 py-2 text-sm">
                          Удалить
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <article className="panel p-8 text-center text-white/72">
                Пока список подарков пуст. Можно добавить идеи вручную или попросить помощника предложить несколько вариантов.
              </article>
            )}
          </section>
        ) : null}

        {activeTab === 'backup' ? (
          <section className="space-y-4">
            <article className="panel p-6 sm:p-8">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="text-sm uppercase tracking-[0.24em] text-white/70">План Б</div>
                  <h2 className="mt-3 text-3xl font-bold text-white">Запасные варианты</h2>
                  <p className="mt-3 text-sm leading-7 text-white/84">Здесь держим только запасные сценарии. Их можно набрасывать через помощника или сохранять из подбора основы.</p>
                </div>
                <button
                  type="button"
                  onClick={() => openAssistant('Подбери один хороший план Б для этого события.', 'backup')}
                  className="primary-btn px-5 py-3"
                >
                  Подобрать план Б
                </button>
              </div>
            </article>

            {backupIdeas.length > 0 ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {backupIdeas.map((idea) => (
                  <article key={idea.raw} className="panel p-6">
                    <div className="text-sm uppercase tracking-[0.18em] text-white/55">Запасной вариант</div>
                    <h3 className="mt-3 text-xl font-semibold text-white">{idea.title}</h3>
                    {idea.note ? <p className="mt-3 text-base leading-7 text-white/78">{idea.note}</p> : null}
                    <div className="mt-5 flex flex-wrap gap-3">
                      <button type="button" onClick={() => void makeBackupMain(idea)} className="primary-btn px-5 py-3">
                        Сделать основой
                      </button>
                      <button
                        type="button"
                        onClick={() => openAssistant(`Сделай вариант "${idea.title}" основным и подскажи, что лучше поменять дальше.`, 'overview')}
                        className="secondary-btn px-5 py-3"
                      >
                        Обсудить с помощником
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <article className="panel p-8 text-center text-white/72">
                План Б пока не сохранён. Выбери запасной вариант из подбора основы или попроси помощника предложить что-то на случай дождя, отказа площадки или сокращения бюджета.
              </article>
            )}
          </section>
        ) : null}
      </div>

      {showInviteForm ? (
        <div className="fixed inset-0 z-40 flex justify-end bg-slate-950/62 backdrop-blur-sm">
          <button type="button" className="h-full flex-1 cursor-default" onClick={() => setShowInviteForm(false)} aria-label="Закрыть окно гостей" />
          <div className="flex h-full w-full max-w-xl flex-col border-l border-white/10 bg-[#102552]/95 p-4 shadow-2xl sm:p-5">
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <div className="text-sm uppercase tracking-[0.24em] text-white/68">Гости</div>
                <h2 className="mt-1 text-2xl font-bold text-white">Добавить гостей</h2>
                <p className="mt-1 text-sm text-white/72">Отдельное окно, чтобы не перегружать саму вкладку.</p>
              </div>
              <button type="button" onClick={() => setShowInviteForm(false)} className="secondary-btn px-4 py-2 text-sm">
                Закрыть
              </button>
            </div>

            <div className="mt-4 flex-1 overflow-y-auto pr-1">
              <div className="grid gap-4 md:grid-cols-2">
                <input type="email" placeholder="Email гостя *" className="field" value={newGuestEmail} onChange={(e) => setNewGuestEmail(e.target.value)} />
                <input type="text" placeholder="Имя гостя" className="field" value={newGuestName} onChange={(e) => setNewGuestName(e.target.value)} />
                <input type="tel" placeholder="Телефон (необязательно)" className="field md:col-span-2" value={newGuestPhone} onChange={(e) => setNewGuestPhone(e.target.value)} />
                <label className="flex items-center gap-2 cursor-pointer md:col-span-2">
                  <input
                    type="checkbox"
                    checked={isBirthdayPerson}
                    onChange={(e) => setIsBirthdayPerson(e.target.checked)}
                    className="w-4 h-4 rounded border-white/20 bg-white/10 text-brand-orange focus:ring-brand-orange"
                  />
                  <span className="text-sm text-slate-300">🎂 Этот гость - именинник</span>
                </label>
                <textarea
                  placeholder="Дополнительные email — по одному в строку"
                  className="field min-h-[130px] resize-none md:col-span-2"
                  value={guestDraft}
                  onChange={(e) => setGuestDraft(e.target.value)}
                />
                <textarea
                  placeholder="Шаблон приглашения (необязательно)"
                  className="field min-h-[140px] resize-none md:col-span-2"
                  value={inviteMessage}
                  onChange={(e) => setInviteMessage(e.target.value)}
                />
              </div>
            </div>

            <div className="mt-4 border-t border-white/10 pt-4">
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={sendInvitations}
                  className="primary-btn px-5 py-3"
                  disabled={sendingInvites || (!newGuestEmail.trim() && !guestDraft.trim())}
                >
                  {sendingInvites ? 'Отправляем...' : 'Отправить приглашения'}
                </button>
                <button type="button" onClick={saveGuests} className="secondary-btn px-5 py-3" disabled={savingGuests}>
                  {savingGuests ? 'Сохраняем...' : 'Сохранить список'}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {assistantOpen ? (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/62 backdrop-blur-sm">
          <button type="button" className="hidden h-full flex-1 cursor-default md:block" onClick={closeAssistant} aria-label="Закрыть" />
          <div className="flex h-full w-full max-w-2xl flex-col border-l border-white/10 bg-[#102552]/95 p-4 shadow-2xl sm:p-5">
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <div className="text-sm uppercase tracking-[0.24em] text-white/68">Otmech.AI</div>
                <h2 className="mt-1 text-2xl font-bold text-white">Помощник события</h2>
                <p className="mt-1 text-sm text-white/72">{hasMainPlan ? 'Можно менять детали, подарки и план Б.' : 'Сейчас помогаю собрать основу события.'}</p>
              </div>
              <button type="button" onClick={closeAssistant} className="secondary-btn px-4 py-2 text-sm">
                Закрыть
              </button>
            </div>

            <div ref={chatViewportRef} className="mt-4 flex-1 space-y-4 overflow-y-auto pr-1">
              {syntheticIntro && messages.length === 0 ? (
                <div className="max-w-[92%] rounded-[28px] rounded-bl-md bg-white/10 p-4 text-white">
                  <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.18em] text-white/60">Otmech.AI</div>
                  <MarkdownMessage content={syntheticIntro} />
                </div>
              ) : null}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={message.role === 'user'
                    ? 'ml-auto max-w-[92%] rounded-[28px] rounded-br-md bg-gradient-to-br from-brand-orange to-orange-400 p-4 text-white'
                    : 'max-w-[92%] rounded-[28px] rounded-bl-md bg-white/10 p-4 text-white'}
                >
                  <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.18em] text-white/60">
                    {message.role === 'user' ? 'Вы' : 'Otmech.AI'}
                  </div>
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap break-words text-[15px] leading-6 text-white">{message.content}</p>
                  ) : (
                    <>
                      <MarkdownMessage content={message.content} />
                      <AssistantMessageActions actions={message.actions} onAction={handleChatAction} disabled={sending} />
                    </>
                  )}
                </div>
              ))}
            </div>

            <div className="mt-4 border-t border-white/10 pt-4">
              <div className="flex gap-2 overflow-x-auto pb-1">
                {quickReplies.map((reply) => (
                  <button key={reply} type="button" onClick={() => void handleSendMessage(reply)} className="chip whitespace-nowrap">
                    {reply}
                  </button>
                ))}
              </div>

              <div className="mt-4 rounded-[24px] border border-white/10 bg-white/8 p-3">
                <div className="flex items-end gap-3">
                  <textarea
                    className="field min-h-[88px] flex-1 resize-none border-0 bg-transparent px-2 py-2 text-[15px] leading-6 placeholder:text-sm"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder={hasMainPlan ? 'Напиши, что изменить или подобрать…' : 'Опиши, какой основной вариант ты хочешь…'}
                  />
                  <button
                    type="button"
                    onClick={() => void handleSendMessage()}
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand-orange text-white transition hover:-translate-y-0.5 hover:brightness-110 disabled:opacity-40"
                    disabled={sending}
                    aria-label="Отправить сообщение"
                  >
                    {sending ? (
                      <span className="text-sm font-bold text-white">...</span>
                    ) : (
                      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <path d="M5 19L19 5" />
                        <path d="M8 5h11v11" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
  )
}
