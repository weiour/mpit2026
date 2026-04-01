import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getChatHistory, sendChatMessage } from '../api'
import { AppHeader } from '../components/AppHeader'
import AssistantMessageActions from '../components/AssistantMessageActions'
import { getToken } from '../storage'
import type { ChatAction, ChatMessage } from '../types'
import { BottomNav } from '../components/BottomNav'
import MarkdownMessage from '../components/MarkdownMessage'

const quickPrompts = [
  'Предложи 3 варианта дня рождения',
  'Что ещё нужно уточнить?',
  'Подбери формат и локацию',
  'Подбери места под мой бюджет',
]

export function EventChatPage() {
  const { eventId } = useParams()
  const navigate = useNavigate()
  const token = getToken()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('Предложи 3 варианта дня рождения')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!token || !eventId) return
    getChatHistory(token, Number(eventId))
      .then(setMessages)
      .catch((err: Error) => setError(err.message))
  }, [token, eventId])

  const hasAssistantReply = useMemo(
    () => messages.some((item) => item.role === 'assistant'),
    [messages],
  )

  useEffect(() => {
    const el = messagesRef.current
    if (!el) return
    requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight
    })
  }, [messages.length, loading])

  async function submitMessage(rawText: string) {
    const text = rawText.trim()
    if (!token || !eventId || !text) return
    setLoading(true)
    setError('')
    try {
      const response = await sendChatMessage(token, Number(eventId), text)
      setMessages((prev) => [...prev, response.user_message, response.assistant_message])
      setInput('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось получить ответ')
    } finally {
      setLoading(false)
    }
  }

  async function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await submitMessage(input)
  }

  async function handleAction(action: ChatAction) {
    if (!eventId) return
    if (action.kind === 'open_tab' && action.target_tab) {
      navigate(`/event/${eventId}?tab=${action.target_tab}`)
      return
    }
    if (action.kind === 'send_prompt' && action.prompt) {
      await submitMessage(action.prompt)
    }
  }

  return (
    <main className="min-h-screen">
      <section className="party-board min-h-screen">
        <AppHeader />
        <div className="board-content mx-auto w-full max-w-6xl px-4 pb-44 sm:px-6 lg:px-8">
          <div className="desktop-two-col">
            <div>
              <h1 className="russo-title brand-shadow text-[48px] leading-none sm:text-[70px]">
                ЧАТ
              </h1>

              {error ? (
                <div className="mt-4 rounded-[18px] bg-red-500/15 px-4 py-3 text-sm text-red-100">
                  {error}
                </div>
              ) : null}

              <div className="mt-5 flex flex-wrap gap-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="chip"
                    onClick={() => setInput(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              {hasAssistantReply ? (
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={() => navigate(`/event/${eventId}/variants`)}
                  >
                    Смотреть рекомендованные места
                  </button>
                </div>
              ) : null}

              <div className="mt-6 app-card h-[min(72vh,760px)] min-h-[420px] space-y-4 overflow-y-auto xl:min-h-[520px] shadow-none" ref={messagesRef}>
                {messages.length === 0 ? (
                  <div className="app-note max-w-xl">
                    Отправь первое сообщение, и агент начнёт предлагать идеи для праздника.
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.id}
                      className={[
                        'max-w-[86%] rounded-[24px] px-4 py-3 text-[15px] leading-6',
                        message.role === 'assistant'
                          ? 'border border-white/10 bg-white/12 text-white break-words'
                          : 'ml-auto border border-[#4a3d2a]/55 bg-[#332a1f] text-white break-words',
                      ].join(' ')}
                    >
                      <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.18em] text-white/65">
                        {message.role === 'assistant' ? 'Otmech.AI' : 'Вы'}
                      </div>
                      <div className="rounded-3xl text-white">
                        {message.role === 'assistant' ? (
                          <>
                            <MarkdownMessage content={message.content} />
                            <AssistantMessageActions
                              actions={message.actions}
                              onAction={handleAction}
                              disabled={loading}
                            />
                          </>
                        ) : (
                          <p className="whitespace-pre-wrap break-words text-[15px] leading-6 text-white">{message.content}</p>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <form className="mt-4" onSubmit={handleSend}>
                <div className="rounded-[28px] border border-white/10 bg-brand-darkBtn/95 p-3 shadow-none">
                  <div className="flex items-end gap-3">
                    <textarea
                      className="min-h-[90px] flex-1 resize-none bg-transparent px-2 py-2 text-[15px] leading-6 text-white outline-none placeholder:text-sm placeholder:text-white/45"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Напиши, что уточнить или изменить"
                    />
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#ff8a5b] text-white transition hover:-translate-y-0.5 hover:brightness-110 disabled:opacity-40"
                      aria-label="Отправить сообщение"
                    >
                      {loading ? (
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
              </form>
            </div>

            <aside className="hidden xl:block">
              <div className="glass-panel p-6 shadow-none">
                <div className="app-note mb-6 bg-black/25">
                  Здесь агент помогает собрать сценарий праздника и уточнить важные детали.
                </div>
                <img src="/assets/CATP.png" alt="Кот" className="w-[240px]" />
                <div className="mt-5 rounded-[22px] bg-black/30 p-5 text-white/90">
                  <p className="text-lg font-bold">Подсказка</p>
                  <p className="mt-2 leading-7 text-white/75">
                    Напиши город, бюджет, количество гостей и атмосферу — тогда подбор мест будет точнее.
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </div>
        <BottomNav />
      </section>
    </main>
  )
}
