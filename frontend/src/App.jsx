import { useState } from 'react'

function App() {
  const [url, setUrl] = useState('')
  const [duration, setDuration] = useState('30-45s')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [videoUrls, setVideoUrls] = useState([])
  const [sliceCount, setSliceCount] = useState(1)
  const [captions, setCaptions] = useState(null)
  const [captionLoading, setCaptionLoading] = useState(false)
  const [selectedVideo, setSelectedVideo] = useState(null)

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

  const handleAddCaptions = async (vUrl) => {
    setSelectedVideo(vUrl);
    setCaptionLoading(true);
    setCaptions(null);
    setStatus("Transcribing video... This takes a few seconds.");

    try {
      const response = await fetch("http://localhost:8001/api/transcribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_url: vUrl })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setCaptions(data.segments);
        setStatus("Transcription complete! You can now edit the captions.");
      } else {
        setStatus("Error: " + data.message);
      }
    } catch (err) {
      setStatus("Error connecting to backend for transcription.");
    } finally {
      setCaptionLoading(false);
    }
  }

  const handleCaptionChange = (index, newText) => {
    const newCaptions = [...captions];
    newCaptions[index].text = newText;
    setCaptions(newCaptions);
  }

  const handleBurnCaptions = async () => {
    if (!captions || !selectedVideo) return;
    
    setCaptionLoading(true);
    setStatus("Burning captions into video... This might take a few moments.");

    try {
      const response = await fetch("http://localhost:8001/api/burn-captions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_url: selectedVideo, captions })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setStatus("Captions burned successfully!");
        
        // Replace the old video with the new one
        const updatedUrls = videoUrls.map(url => url === selectedVideo ? data.video_url : url);
        setVideoUrls(updatedUrls);
        
        // Select the new video and clear captions editor
        setSelectedVideo(data.video_url);
        setCaptions(null);
      } else {
        setStatus("Error: " + data.message);
      }
    } catch (err) {
      setStatus("Error connecting to backend to burn captions.");
    } finally {
      setCaptionLoading(false);
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
                    <div key={index} style={{textAlign: 'center', background: selectedVideo === vUrl ? 'rgba(99, 102, 241, 0.2)' : 'transparent', padding: '1rem', borderRadius: '12px'}}>
                      <video 
                        src={vUrl} 
                        controls 
                        style={{
                          width: '100%', 
                          borderRadius: '12px', 
                          border: selectedVideo === vUrl ? '2px solid var(--primary)' : '1px solid rgba(255,255,255,0.1)'
                        }} 
                      />
                      <p style={{marginTop: '0.5rem', color: 'var(--text-muted)'}}>Slice #{index + 1}</p>
                      <button 
                        onClick={() => handleAddCaptions(vUrl)}
                        disabled={captionLoading}
                        style={{
                          marginTop: '0.5rem', padding: '0.8rem 1rem', borderRadius: '8px', border: 'none',
                          background: 'var(--primary)', color: 'white', cursor: 'pointer', width: '100%',
                          fontWeight: 'bold'
                        }}
                      >
                        {captionLoading && selectedVideo === vUrl ? "⏳ Transcribing..." : "📝 Add Captions"}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {captions && selectedVideo && (
              <div style={{marginTop: '2rem', padding: '1.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '12px'}}>
                <h3>Caption Editor</h3>
                <p style={{marginBottom: '1rem', color: 'var(--text-muted)'}}>Editing captions for the selected slice. Adjust the text as needed.</p>
                <div style={{display: 'flex', flexDirection: 'column', gap: '0.8rem', maxHeight: '400px', overflowY: 'auto', paddingRight: '1rem'}}>
                  {captions.map((seg, idx) => (
                    <div key={idx} style={{display: 'flex', gap: '1rem', alignItems: 'center'}}>
                      <span style={{color: 'var(--primary)', minWidth: '90px', fontSize: '0.9rem', fontWeight: 'bold'}}>
                        {seg.start}s - {seg.end}s
                      </span>
                      <input 
                        type="text" 
                        className="url-input" 
                        value={seg.text} 
                        onChange={(e) => handleCaptionChange(idx, e.target.value)} 
                        style={{padding: '0.8rem', flex: 1}}
                      />
                    </div>
                  ))}
                </div>
                <button 
                  className="action-btn" 
                  style={{marginTop: '1.5rem', background: 'linear-gradient(135deg, #10b981, #3b82f6)'}}
                  onClick={handleBurnCaptions}
                  disabled={captionLoading}
                >
                  {captionLoading ? "⏳ Burning Captions..." : "🔥 Save & Burn Captions"}
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  )
}

export default App
