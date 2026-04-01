import type { ChatAction } from '../types'

type Props = {
  actions?: ChatAction[]
  onAction: (action: ChatAction) => void
  disabled?: boolean
  className?: string
}

export default function AssistantMessageActions({ actions = [], onAction, disabled = false, className }: Props) {
  if (!actions.length) return null

  return (
    <div className={[
      'mt-3 flex flex-wrap gap-2',
      className,
    ].filter(Boolean).join(' ')}>
      {actions.map((action) => (
        <button
          key={action.id}
          type="button"
          disabled={disabled}
          onClick={() => onAction(action)}
          className="rounded-full border border-white/14 bg-white/10 px-3 py-2 text-xs font-semibold text-white/92 transition hover:-translate-y-0.5 hover:bg-white/16 disabled:cursor-not-allowed disabled:opacity-45"
        >
          {action.label}
        </button>
      ))}
    </div>
  )
}
