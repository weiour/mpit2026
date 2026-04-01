export type ParsedAgentMessage = {
  body: string
  actions: string[]
}

export function parseAgentMessage(content: string): ParsedAgentMessage {
  const normalized = content.replace(/\r\n/g, '\n').trim()
  const actionBlock = normalized.match(/(?:^|\n)Действия\s*:\s*([\s\S]*)$/i)

  if (!actionBlock) {
    return { body: normalized, actions: [] }
  }

  const block = actionBlock[1] ?? ''
  const matches = Array.from(block.matchAll(/\[([^\]\n]{1,40})\]/g))
  const actions = Array.from(
    new Set(
      matches
        .map((match) => match[1]?.replace(/\s+/g, ' ').trim())
        .filter((value): value is string => Boolean(value)),
    ),
  ).slice(0, 4)

  const body = normalized.slice(0, actionBlock.index).trim()

  return {
    body,
    actions,
  }
}
