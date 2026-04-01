interface MobileStepBarProps {
  current: number
  total?: number
  onBack?: () => void
  onNext?: () => void
  nextDisabled?: boolean
  nextLabel?: string
}

export function MobileStepBar({
  current,
  total = 5,
  onBack,
  onNext,
  nextDisabled,
  nextLabel,
}: MobileStepBarProps) {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 px-4 pb-20 sm:pb-6">
      <div className="mx-auto flex w-full max-w-md items-center justify-between rounded-[24px] bg-[#0d2d5a]/95 px-5 py-4 text-white shadow-2xl backdrop-blur-md">
        <button
          type="button"
          onClick={onBack}
          disabled={!onBack}
          className="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-2xl transition disabled:opacity-35"
        >
          ←
        </button>

        <div className="text-center">
          <div className="text-base font-bold">
            Шаг {current} из {total}
          </div>
          {nextLabel ? <div className="text-sm text-white/70">{nextLabel}</div> : null}
        </div>

        <button
          type="button"
          onClick={onNext}
          disabled={nextDisabled || !onNext}
          className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-orange text-2xl text-white transition disabled:opacity-35"
        >
          →
        </button>
      </div>
    </div>
  )
}