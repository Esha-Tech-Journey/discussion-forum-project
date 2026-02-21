export function renderTextWithMentions(text, mentionClassName) {
  const content = String(text || '')
  const parts = []

  // Match mentions at start or after whitespace. Capture the whitespace so we keep it.
  const regex = /(^|\\s)@(\\w+)/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(content)) !== null) {
    const [full, prefix, username] = match
    const start = match.index
    const mentionStart = start + prefix.length

    if (mentionStart > lastIndex) {
      parts.push(content.slice(lastIndex, mentionStart))
    }

    parts.push(
      <span key={`${mentionStart}-${username}`} className={mentionClassName}>
        @{username}
      </span>
    )

    lastIndex = mentionStart + full.slice(prefix.length).length
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex))
  }

  return parts.length ? parts : content
}

