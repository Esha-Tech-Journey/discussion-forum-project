import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { Search as SearchIcon, Filter, Tag } from 'lucide-react'
import MainLayout from '../layouts/MainLayout'
import { ThreadCard } from '../components/thread'
import { Pagination, SearchBar } from '../components/common'
import { searchService } from '../services'
import styles from './SearchPage.module.css'

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [filters, setFilters] = useState({
    searchIn: 'all', // all, title, content, tags
    sortBy: 'relevance' // relevance, recent, popular
  })
  const [showFilters, setShowFilters] = useState(false)

  const query = searchParams.get('q') || ''

  useEffect(() => {
    if (query) {
      performSearch()
    }
  }, [query, page, filters])

  const performSearch = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await searchService.searchThreads(
        query,
        page,
        20,
        filters.searchIn,
        filters.sortBy
      )

      // Backend returns { results: [], total: number }
      setResults(response.data.results || [])
      setTotalPages(Math.ceil((response.data.total || 0) / 20))
    } catch (err) {
      setError('Failed to search. Please try again.')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPage(1)
  }

  const highlightMatch = (text, searchTerm) => {
    if (!text || !searchTerm) return text

    const parts = text.split(new RegExp(`(${searchTerm})`, 'gi'))
    return (
      <>
        {parts.map((part, i) =>
          part.toLowerCase() === searchTerm.toLowerCase() ? (
            <mark key={i} className={styles.highlight}>{part}</mark>
          ) : (
            part
          )
        )}
      </>
    )
  }

  return (
    <MainLayout>
      <div className={styles.container}>
        <div className={styles.searchSection}>
          <SearchBar autoFocus={!query} />
        </div>

        {query && (
          <>
            <div className={styles.header}>
              <div>
                <h1>Search Results</h1>
                <p className={styles.subtitle}>
                  Searching for: <strong>&quot;{query}&quot;</strong>
                </p>
              </div>
              <button
                className={styles.filterToggle}
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter size={18} />
                Filters
              </button>
            </div>

            {showFilters && (
              <div className={styles.filters}>
                <div className={styles.filterGroup}>
                  <label>Search in:</label>
                  <div className={styles.filterButtons}>
                    {[
                      { value: 'all', label: 'All' },
                      { value: 'title', label: 'Title' },
                      { value: 'content', label: 'Content' },
                      { value: 'tags', label: 'Tags' }
                    ].map(option => (
                      <button
                        key={option.value}
                        className={`${styles.filterButton} ${filters.searchIn === option.value ? styles.active : ''}`}
                        onClick={() => handleFilterChange('searchIn', option.value)}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className={styles.filterGroup}>
                  <label>Sort by:</label>
                  <div className={styles.filterButtons}>
                    {[
                      { value: 'relevance', label: 'Relevance' },
                      { value: 'recent', label: 'Most Recent' },
                      { value: 'popular', label: 'Most Popular' }
                    ].map(option => (
                      <button
                        key={option.value}
                        className={`${styles.filterButton} ${filters.sortBy === option.value ? styles.active : ''}`}
                        onClick={() => handleFilterChange('sortBy', option.value)}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className={styles.error}>
                {error}
                <button onClick={performSearch} className={styles.retryButton}>
                  Retry
                </button>
              </div>
            )}

            {loading ? (
              <div className={styles.loading}>
                <div className={styles.spinner}></div>
                <p>Searching...</p>
              </div>
            ) : results.length === 0 ? (
              <div className={styles.empty}>
                <SearchIcon size={48} />
                <p>No results found for &quot;{query}&quot;</p>
                <p className={styles.emptyHint}>
                  Try different keywords or filters
                </p>
              </div>
            ) : (
              <>
                <p className={styles.resultsCount}>
                  Found {results.length} {results.length === 1 ? 'result' : 'results'}
                </p>
                <div className={styles.results}>
                  {results.map(thread => (
                    <div key={thread.id} className={styles.resultCard}>
                      <ThreadCard thread={thread} />
                      {thread.description && (
                        <p className={styles.excerpt}>
                          {highlightMatch(
                            thread.description.slice(0, 200) + (thread.description.length > 200 ? '...' : ''),
                            query
                          )}
                        </p>
                      )}
                      {thread.tags && thread.tags.length > 0 && (
                        <div className={styles.tags}>
                          <Tag size={14} />
                          {thread.tags.map(tag => (
                            <Link
                              key={typeof tag === 'string' ? tag : tag.id}
                              to={`/threads?tag=${typeof tag === 'string' ? tag : tag.name}`}
                              className={styles.tag}
                            >
                              #{typeof tag === 'string' ? tag : tag.name}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {totalPages > 1 && (
                  <Pagination
                    currentPage={page}
                    totalPages={totalPages}
                    onPageChange={setPage}
                  />
                )}
              </>
            )}
          </>
        )}

        {!query && (
          <div className={styles.welcome}>
            <SearchIcon size={64} />
            <h2>Search Discussion Forum</h2>
            <p>Find threads, topics, and conversations</p>
          </div>
        )}
      </div>
    </MainLayout>
  )
}
