import type { CSSProperties } from 'react'

type Piece = {
  left: number
  size: number
  duration: number
  delay: number
  rotate: number
  drift: number
  kind: 'square' | 'star' | 'squiggle'
  color: string
  opacity?: number
}

const basePieces: Piece[] = [
  { left: 4, size: 13, duration: 6.2, delay: 0.3, rotate: 18, drift: 18, kind: 'square', color: '#ffffff', opacity: 0.92 },
  { left: 8, size: 20, duration: 7.6, delay: 1.4, rotate: -24, drift: 26, kind: 'star', color: '#ffd84f', opacity: 0.95 },
  { left: 12, size: 17, duration: 6.8, delay: 2.5, rotate: 36, drift: 22, kind: 'squiggle', color: '#ff9ecb', opacity: 0.9 },
  { left: 16, size: 12, duration: 5.9, delay: 0.9, rotate: -14, drift: 16, kind: 'square', color: '#8fdcff', opacity: 0.74 },
  { left: 20, size: 17, duration: 7.4, delay: 1.9, rotate: 28, drift: 24, kind: 'star', color: '#ffffff', opacity: 0.72 },
  { left: 24, size: 13, duration: 6.4, delay: 3.2, rotate: -30, drift: 20, kind: 'square', color: '#ffb36b', opacity: 0.76 },
  { left: 28, size: 16, duration: 8.0, delay: 0.5, rotate: 14, drift: 28, kind: 'squiggle', color: '#ffe680', opacity: 0.72 },
  { left: 32, size: 12, duration: 5.7, delay: 2.1, rotate: -18, drift: 16, kind: 'square', color: '#ff7fd1', opacity: 0.8 },
  { left: 36, size: 20, duration: 7.1, delay: 1.1, rotate: 20, drift: 24, kind: 'star', color: '#fff2a5', opacity: 0.94 },
  { left: 40, size: 14, duration: 6.3, delay: 3.4, rotate: -26, drift: 18, kind: 'squiggle', color: '#ffffff', opacity: 0.7 },
  { left: 44, size: 11, duration: 5.8, delay: 0.7, rotate: 38, drift: 15, kind: 'square', color: '#ffd84f', opacity: 0.82 },
  { left: 48, size: 22, duration: 7.9, delay: 2.8, rotate: -12, drift: 30, kind: 'star', color: '#ffb1d8', opacity: 0.94 },
  { left: 52, size: 15, duration: 6.5, delay: 1.6, rotate: 24, drift: 21, kind: 'square', color: '#89d7ff', opacity: 0.78 },
  { left: 56, size: 17, duration: 7.3, delay: 3.6, rotate: -32, drift: 25, kind: 'squiggle', color: '#ffe680', opacity: 0.74 },
  { left: 60, size: 12, duration: 5.6, delay: 0.2, rotate: 16, drift: 16, kind: 'square', color: '#ffffff', opacity: 0.8 },
  { left: 64, size: 20, duration: 6.9, delay: 2.2, rotate: -20, drift: 24, kind: 'star', color: '#ff8fc6', opacity: 0.95 },
  { left: 68, size: 14, duration: 6.1, delay: 1.3, rotate: 30, drift: 18, kind: 'square', color: '#ffd84f', opacity: 0.8 },
  { left: 72, size: 17, duration: 7.7, delay: 3.0, rotate: -10, drift: 28, kind: 'squiggle', color: '#9edfff', opacity: 0.74 },
  { left: 76, size: 13, duration: 5.9, delay: 0.8, rotate: 22, drift: 17, kind: 'square', color: '#ffb36b', opacity: 0.82 },
  { left: 80, size: 18, duration: 7.0, delay: 2.4, rotate: -28, drift: 23, kind: 'star', color: '#ffffff', opacity: 0.76 },
  { left: 84, size: 15, duration: 6.6, delay: 1.8, rotate: 12, drift: 20, kind: 'squiggle', color: '#ff9ecb', opacity: 0.72 },
  { left: 88, size: 11, duration: 5.5, delay: 3.1, rotate: -16, drift: 15, kind: 'square', color: '#8fdcff', opacity: 0.78 },
  { left: 92, size: 20, duration: 7.2, delay: 1.0, rotate: 34, drift: 25, kind: 'star', color: '#ffe680', opacity: 0.95 },
  { left: 96, size: 14, duration: 6.0, delay: 2.7, rotate: -24, drift: 19, kind: 'squiggle', color: '#ffffff', opacity: 0.7 },
]

const pieces: Piece[] = [
  ...basePieces,
  ...basePieces.map((piece, index) => ({
    ...piece,
    left: Math.max(2, Math.min(98, piece.left - 2 + (index % 5))),
    size: Math.max(10, piece.size - (index % 3 === 0 ? 2 : 0)),
    duration: piece.duration + 0.9,
    delay: piece.delay + 1.2,
    rotate: piece.rotate + 12,
    drift: piece.drift + 6,
    opacity: Math.min(0.98, (piece.opacity ?? 0.8) + 0.08),
  })),
]

export function HeroConfetti() {
  return (
    <div className="hero-confetti" aria-hidden="true">
      {pieces.map((piece, index) => {
        const style = {
          left: `${piece.left}%`,
          width: `${piece.size}px`,
          height: `${piece.size}px`,
          color: piece.color,
          opacity: piece.opacity ?? 0.84,
          animationDuration: `${piece.duration}s`,
          animationDelay: `-${piece.delay}s`,
          ['--hero-rotate' as string]: `${piece.rotate}deg`,
          ['--hero-drift' as string]: `${piece.drift}px`,
        } satisfies CSSProperties

        if (piece.kind === 'star') {
          return (
            <span key={index} className="hero-confetti__piece hero-confetti__piece--star" style={style}>
              ✦
            </span>
          )
        }

        if (piece.kind === 'squiggle') {
          return (
            <span key={index} className="hero-confetti__piece hero-confetti__piece--squiggle" style={style}>
              ∿
            </span>
          )
        }

        return <span key={index} className="hero-confetti__piece hero-confetti__piece--square" style={style} />
      })}
    </div>
  )
}
