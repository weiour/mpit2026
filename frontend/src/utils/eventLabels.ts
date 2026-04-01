export function formatEventStatus(status?: string | null, variant: 'default' | 'compact' = 'default') {
  switch (status) {
    case 'ready':
      return variant === 'compact' ? 'Собрано' : 'Событие собрано'
    case 'concept_selected':
      return 'Основа выбрана'
    case 'planning':
      return variant === 'compact' ? 'В процессе' : 'В процессе планирования'
    case 'draft':
      return variant === 'compact' ? 'Черновик' : 'Черновик события'
    default:
      return 'Черновик'
  }
}

export function formatVenueMode(mode?: string | null) {
  switch (mode) {
    case 'outside':
      return 'Вне дома'
    case 'home':
      return 'Дома'
    case 'undecided':
      return 'Ещё не выбран'
    default:
      return 'Не указан'
  }
}

export function formatEventFormat(format?: string | null) {
  switch (format) {
    case 'restaurant':
      return 'Ресторан или место'
    case 'home':
      return 'Домашний формат'
    case 'mixed':
      return 'Смешанный формат'
    default:
      return 'Не определён'
  }
}
