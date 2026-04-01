interface PageIntroProps {
  title: string
  subtitle?: string
}

export function PageIntro({ title, subtitle }: PageIntroProps) {
  return (
    <div className="mb-5">
      <h1 className="font-display text-[46px] uppercase leading-[0.95] tracking-tight text-white drop-shadow-[0_4px_0_rgba(255,116,103,0.75)] sm:text-[58px]">
        {title}
      </h1>
      {subtitle ? <p className="mt-2 max-w-xs text-sm font-medium text-white/75">{subtitle}</p> : null}
    </div>
  )
}
