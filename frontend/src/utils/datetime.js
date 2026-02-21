export function parseServerDate(dateString) {
  if (!dateString) {
    return new Date()
  }

  const value = String(dateString)
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(value)
  return new Date(hasTimezone ? value : `${value}Z`)
}

