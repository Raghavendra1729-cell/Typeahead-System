import React, { useState, useEffect, useRef } from 'react';
import './index.css';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [trending, setTrending] = useState([]);
  const [isFocused, setIsFocused] = useState(false);
  const [toastMsg, setToastMsg] = useState('');
  const searchContainerRef = useRef(null);

  // Close dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target)) {
        setIsFocused(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch Global Trending Top 10
  const fetchTrending = async () => {
    try {
      const res = await fetch(`${API_URL}/trending`);
      const data = await res.json();
      setTrending(data.data || []);
    } catch (err) {
      console.error("Error fetching trending:", err);
    }
  };

  useEffect(() => {
    fetchTrending();
    const interval = setInterval(fetchTrending, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle typing & Debounce Auto-Submit
  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }
    
    const fetchSuggestions = async () => {
      try {
        const res = await fetch(`${API_URL}/suggest?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        setSuggestions(data.data || []);
      } catch (err) {
        console.error("Error fetching suggestions:", err);
      }
    };
    fetchSuggestions();

    // AUTO-SEARCH REMOVED AS REQUESTED
    // We no longer debounce and submit automatically. 
  }, [query]);

  const handleSearchSubmit = async (searchQuery) => {
    if (!searchQuery.trim()) return;
    
    try {
      await fetch(`${API_URL}/search?q=${encodeURIComponent(searchQuery)}`, { method: 'POST' });
      
      setToastMsg(`Searched: "${searchQuery}"`);
      setTimeout(() => setToastMsg(''), 3000);
      fetchTrending();

      // Open the real Google search in a new tab
      window.open(`https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`, '_blank');
    } catch (err) {
      console.error("Error submitting search:", err);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearchSubmit(query);
      setIsFocused(false);
      e.target.blur(); // Remove DOM focus so clicking it again works!
    }
  };

  const handleItemClick = (item) => {
    setQuery(item);
    handleSearchSubmit(item);
    setIsFocused(false);
  };

  const clearSearch = () => {
    setQuery('');
    setSuggestions([]);
    setIsFocused(true);
  };

  return (
    <>
      <h1 className="logo">Wannabe Google</h1>
      
      <div className="search-container" ref={searchContainerRef}>
        <div className={`search-box ${isFocused ? 'focused' : ''}`}>
          <svg className="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path>
          </svg>
          
          <input 
            type="text" 
            className="search-input"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsFocused(true); // FIX: Ensure dropdown opens when typing
            }}
            onFocus={() => setIsFocused(true)}
            onClick={() => setIsFocused(true)} // FIX: Ensure clicking an already-focused input opens dropdown
            onKeyDown={onKeyDown}
            placeholder="Search Wannabe Google or type a URL"
            autoComplete="off"
            spellCheck="false"
          />

          {/* Clear Button (X) - Only shows if there is text */}
          {query && (
            <div className="clear-btn" onClick={clearSearch}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
                <path fill="#9aa0a6" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </div>
          )}
        </div>

        {isFocused && (
          <div className="dropdown">
            {!query.trim() && (
              <>
                <div className="dropdown-header">
                  <div className="pulse"></div> Trending Right Now
                </div>
                {trending.map((trend, idx) => (
                  <div key={idx} className="dropdown-item" onClick={() => handleItemClick(trend)}>
                    <svg className="item-icon trending-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/></svg>
                    <span>{trend}</span>
                  </div>
                ))}
              </>
            )}

            {query.trim() && suggestions.length > 0 && (
              <>
                {suggestions.map((sug, idx) => (
                  <div key={idx} className="dropdown-item" onClick={() => handleItemClick(sug)}>
                    <svg className="item-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path></svg>
                    <span>{sug}</span>
                  </div>
                ))}
              </>
            )}

            {query.trim() && suggestions.length === 0 && (
              <div className="dropdown-item" style={{ color: '#9aa0a6', fontStyle: 'italic', cursor: 'default' }}>
                No suggestions found...
              </div>
            )}
          </div>
        )}
      </div>

      {toastMsg && <div className="dummy-toast">{toastMsg}</div>}
    </>
  );
}

export default App;
