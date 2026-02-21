import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Search, X } from 'lucide-react'
import styles from './SearchBar.module.css'

export default function SearchBar({ onSearch, autoFocus = false }) {
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)
  const debounceRef = useRef(null)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    // Initialize with URL query param if present
    const urlQuery = searchParams.get('q')
    if (urlQuery) {
      setQuery(urlQuery)
    }
  }, [searchParams])

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus()
    }
  }, [autoFocus])

  const handleInputChange = (value) => {
    setQuery(value)

    // Clear existing debounce timer
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    // Debounce search with 300ms delay
    if (value.trim()) {
      debounceRef.current = setTimeout(() => {
        if (onSearch) {
          onSearch(value)
        }
      }, 300)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const handleClear = () => {
    setQuery('')
    navigate('/search')
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  return (
    <form className={styles.searchBar} onSubmit={handleSubmit}>
      <Search size={20} className={styles.icon} />
      <input
        ref={inputRef}
        type="text"
        placeholder="Search for tags, threads..."
        value={query}
        onChange={(e) => handleInputChange(e.target.value)}
        className={styles.input}
      />
      {query && (
        <button
          type="button"
          onClick={handleClear}
          className={styles.clearButton}
          aria-label="Clear search"
        >
          <X size={18} />
        </button>
      )}
    </form>
  )
}
