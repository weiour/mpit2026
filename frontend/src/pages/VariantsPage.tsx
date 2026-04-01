import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getEventRecommendations } from '../api'
import { AppHeader } from '../components/AppHeader'
import { MobileStepBar } from '../components/MobileStepBar'
import { getToken } from '../storage'
import type { RecommendationsResponse } from '../types'

export function VariantsPage() {
  const { eventId } = useParams()
  const navigate = useNavigate()
  const token = getToken()
  const [data, setData] = useState<RecommendationsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [city, setCity] = useState('')

  async function loadRecommendations(cityOverride?: string) {
    if (!token || !eventId) return
    setLoading(true)
    setError('')
    try {
      const response = await getEventRecommendations(token, Number(eventId), {
        city: cityOverride,
        limit: 6,
      })
      setData(response)
      if (response.meta.city && !cityOverride) {
        setCity(response.meta.city)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось получить рекомендации')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadRecommendations()
  }, [token, eventId])

  const needsCity = useMemo(
    () => data?.meta.missing_fields.includes('city') || data?.meta.provider === '2gis_not_configured',
    [data],
  )

  return (
    <main className="min-h-screen">
      <section className="party-board min-h-screen">
          <AppHeader />
          <div className="board-content mx-auto w-full max-w-6xl px-4 pb-44 sm:px-6 lg:px-8">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h1 className="russo-title brand-shadow text-[48px] leading-none sm:text-[70px]">
                  МЕСТА
                </h1>
                <p className="mt-3 max-w-3xl text-lg text-white/78">
                  Удобный список рекомендованных площадок под твой формат, пожелания и бюджет.
                </p>
              </div>

              <div className="app-card w-full max-w-xl">
                <div className="mb-3 text-sm font-semibold text-white/75">Город или район</div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <input
                    className="field flex-1"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="Например, Москва или Казань, центр"
                  />
                  <button
                    type="button"
                    className="primary-btn whitespace-nowrap"
                    onClick={() => void loadRecommendations(city)}
                    disabled={loading}
                  >
                    {loading ? 'Подбираем...' : 'Обновить подбор'}
                  </button>
                </div>
              </div>
            </div>

            {error ? (
              <div className="mt-4 rounded-[18px] bg-red-500/15 px-4 py-3 text-sm text-red-100">
                {error}
              </div>
            ) : null}

            {data ? (
              <div className="mt-6 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
                <div className="space-y-4">
                  {data.items.length === 0 ? (
                    <div className="app-card">
                      <div className="text-2xl font-bold">Пока нет готовых карточек мест</div>
                      <p className="mt-3 leading-7 text-white/80">
                        {needsCity
                          ? 'Укажи город или район выше — тогда агент сможет искать реальные заведения.'
                          : 'Подбор не вернул подходящих мест. Попробуй уточнить формат, бюджет или добавить больше пожеланий в чат.'}
                      </p>
                    </div>
                  ) : (
                    data.items.map((item, index) => (
                      <article key={item.id} className="app-card flex flex-col gap-4">
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                          <div>
                            <div className="text-sm font-bold uppercase tracking-[0.18em] text-white/55">
                              Вариант {index + 1}
                            </div>
                            <strong className="mt-1 block text-2xl leading-tight">{item.name}</strong>
                            <p className="mt-2 text-white/75">{item.address || 'Адрес уточняется'}</p>
                          </div>
                          <div className="rounded-[22px] bg-black/25 px-4 py-3 text-sm text-white/85">
                            <div>{item.rating != null ? `Рейтинг: ${item.rating.toFixed(1)}` : 'Рейтинг не указан'}</div>
                            <div>
                              {item.review_count != null
                                ? `Отзывов: ${item.review_count}`
                                : 'Число отзывов не указано'}
                            </div>
                          </div>
                        </div>

                        {item.tags.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {item.tags.map((tag) => (
                              <span key={`${item.id}-${tag}`} className="chip">
                                {tag}
                              </span>
                            ))}
                          </div>
                        ) : null}

                        <div className="rounded-[22px] bg-white/8 p-4 text-white/90">
                          <div className="text-sm font-bold uppercase tracking-[0.14em] text-white/60">
                            Почему подходит
                          </div>
                          <p className="mt-2 leading-7">{item.reason}</p>
                          {item.price_note ? <p className="mt-2 text-sm text-white/65">{item.price_note}</p> : null}
                          {item.source_query ? (
                            <p className="mt-2 text-sm text-white/55">Поиск: {item.source_query}</p>
                          ) : null}
                        </div>

                        <div className="mt-auto flex flex-wrap gap-3">
                          {item.two_gis_url ? (
                            <a
                              href={item.two_gis_url}
                              target="_blank"
                              rel="noreferrer"
                              className="primary-btn"
                            >
                              Открыть в 2ГИС
                            </a>
                          ) : null}
                          {item.yandex_maps_url ? (
                            <a
                              href={item.yandex_maps_url}
                              target="_blank"
                              rel="noreferrer"
                              className="secondary-btn"
                            >
                              Открыть в Яндекс Картах
                            </a>
                          ) : null}
                          <button
                            type="button"
                            className="secondary-btn"
                            onClick={() => navigate(`/event/${eventId}/refine`)}
                          >
                            Уточнить подбор
                          </button>
                        </div>
                      </article>
                    ))
                  )}
                </div>

                <aside className="space-y-4">
                  <div className="glass-panel p-6">
                    <div className="text-sm font-bold uppercase tracking-[0.14em] text-white/55">
                      Как агент искал места
                    </div>
                    <p className="mt-3 leading-7 text-white/88">{data.meta.generated_summary}</p>
                    <div className="mt-4 rounded-[20px] bg-black/25 p-4 text-sm text-white/85">
                      <div>Город: {data.meta.city || 'не определён'}</div>
                      <div>Источник: {data.meta.provider}</div>
                    </div>
                  </div>

                  <div className="app-card">
                    <div className="text-sm font-bold uppercase tracking-[0.14em] text-white/55">
                      Поисковые запросы
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {data.meta.search_queries.map((query) => (
                        <span key={query} className="chip">
                          {query}
                        </span>
                      ))}
                    </div>
                  </div>

                  {data.meta.warnings.length > 0 ? (
                    <div className="app-card border border-yellow-300/25 bg-yellow-400/10">
                      <div className="text-sm font-bold uppercase tracking-[0.14em] text-yellow-100/80">
                        Что ещё важно
                      </div>
                      <div className="mt-3 space-y-2 text-sm leading-6 text-yellow-50/90">
                        {data.meta.warnings.map((warning) => (
                          <p key={warning}>{warning}</p>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </aside>
              </div>
            ) : (
              <div className="mt-6 app-card text-white/80">
                {loading ? 'Подбираем места...' : 'Готовим рекомендации...'}
              </div>
            )}
          </div>
          <MobileStepBar
            current={4}
            nextLabel="К уточнению"
            onBack={() => navigate(`/event/${eventId}/chat`)}
            onNext={() => navigate(`/event/${eventId}/refine`)}
          />
      </section>
    </main>
  )
}
