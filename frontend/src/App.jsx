import { useState } from 'react'

function App() {
  const [url, setUrl] = useState('')
  const [duration, setDuration] = useState('30-45s')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [videoUrls, setVideoUrls] = useState([])
  const [sliceCount, setSliceCount] = useState(1)

  const durations = [
    { label: '15-30s', value: '15-30s' },
    { label: '30-45s', value: '30-45s' },
    { label: '45-60s', value: '45-60s' },
    { label: '60-120s', value: '60-120s' },
    { label: '150s', value: '150s' },
    { label: '180s', value: '180s' },
  ]

  const handleGenerate = async () => {
    if (!url) {
      alert("Please enter a YouTube URL.")
      return;
    }
    
    setStatus(`Processing ${sliceCount} stream(s)... This might take a moment.`)
    setLoading(true)
    setVideoUrls([])
    
    try {
      const response = await fetch("http://localhost:8001/api/slice", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url, duration, sliceCount: parseInt(sliceCount) })
      });
      
      const data = await response.json();
      setStatus(data.message);
      if (data.status === 'success' && data.video_urls) {
        setVideoUrls(data.video_urls);
      }
    } catch (error) {
      setStatus("Error connecting to the backend. Is it running?");
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="bg-gradient"></div>
      <div className="bg-gradient-2"></div>
      
      <div className="app-container">
        <header>
          <h1 className="logo">EasySlice AI</h1>
          <p>Transform long videos into viral, caption-ready shorts in seconds.</p>
        </header>

        <main>
          <div className="slicer-panel">
            <div className="input-group">
              <label htmlFor="yt-url">YouTube Video URL</label>
              <input 
                id="yt-url"
                type="text" 
                className="url-input" 
                placeholder="https://www.youtube.com/watch?v=..." 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="input-group">
              <label>Target Clip Duration</label>
              <div className="duration-selector">
                {durations.map((d) => (
                  <button 
                    key={d.value}
                    className={`duration-btn ${duration === d.value ? 'active' : ''}`}
                    onClick={() => setDuration(d.value)}
                    disabled={loading}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="input-group">
              <label htmlFor="slice-count">Number of Slices (Max 10)</label>
              <input 
                id="slice-count"
                type="number" 
                min="1" 
                max="10"
                className="url-input" 
                value={sliceCount}
                onChange={(e) => {
                  let val = parseInt(e.target.value);
                  if (val > 10) val = 10;
                  if (val < 1) val = 1;
                  setSliceCount(val || 1);
                }}
                disabled={loading}
              />
            </div>

            <button className="action-btn" onClick={handleGenerate} disabled={loading}>
              {loading ? "⚙️ Processing..." : "✨ Generate Magic Slices"}
            </button>

            {status && (
              <div className="status-box">
                {status}
              </div>
            )}

            {videoUrls.length > 0 && (
              <div style={{marginTop: '2rem'}}>
                <h3 style={{textAlign: 'center', marginBottom: '1rem'}}>Your Slices are Ready!</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  {videoUrls.map((vUrl, index) => (
                    <div key={index} style={{textAlign: 'center'}}>
                      <video 
                        src={vUrl} 
                        controls 
                        style={{
                          width: '100%', 
                          borderRadius: '12px', 
                          border: '1px solid rgba(255,255,255,0.1)'
                        }} 
                      />
                      <p style={{marginTop: '0.5rem', color: 'var(--text-muted)'}}>Slice #{index + 1}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  )
}

export default App
