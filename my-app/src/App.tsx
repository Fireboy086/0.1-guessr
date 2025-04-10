import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [items, setItems] = useState<string[]>([]);
  const [filteredItems, setFilteredItems] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Fetch items from Python API
    const apiUrl = 'http://127.0.0.1:5001/api/items'; // Updated port to 5001
    console.log('Fetching data from:', apiUrl);
    
    fetch(apiUrl)
      .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
          throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Data received:', data);
        setItems(data);
        setFilteredItems(data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setError(`Failed to load items: ${error.message}. Is the Python API running at ${apiUrl}?`);
        setIsLoading(false);
      });
  }, []);
  
  useEffect(() => {
    // Filter items based on search term
    const results = items.filter(item =>
      item.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredItems(results);
  }, [searchTerm, items]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  return (
    <div className="App">
      <div className="title-bar">
        My Selection App
      </div>
      
      <div className="search-container">
        <input
          type="text"
          placeholder="Search items..."
          value={searchTerm}
          onChange={handleSearch}
          className="search-input"
        />
      </div>
      
      <div className="selection-box">
        {isLoading ? (
          <div className="loading">Loading items...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : filteredItems.length > 0 ? (
          filteredItems.map((item, index) => (
            <div key={index} className="selection-item">
              {item}
            </div>
          ))
        ) : (
          <div className="no-results">No matching items found</div>
        )}
      </div>
      
      <div className="button-container">
        <button className="action-button blue">Blue</button>
        <button className="action-button green">Green</button>
        <button className="action-button orange">Orange</button>
        <button className="action-button red">Red</button>
      </div>
    </div>
  );
}

export default App;
