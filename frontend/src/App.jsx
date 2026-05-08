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
  const [activeTab, setActiveTab] = useState('slicer')
  const [imagePrompt, setImagePrompt] = useState('')
  const [imageAspectRatio, setImageAspectRatio] = useState('1:1')
  const [isGeneratingImage, setIsGeneratingImage] = useState(false)
  const [generatedImage, setGeneratedImage] = useState(null)
  const [imageError, setImageError] = useState(null)

  const [captionStyle, setCaptionStyle] = useState({
    fontSize: 24,
    color: '#ffffff',
    outline: 2,
    outlineColor: '#000000',
    shadow: 0,
    shadowColor: '#000000',
    position: 'bottom',
    animationStyle: 'sentence'
  });

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
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";
      const response = await fetch(`${apiUrl}/api/slice`, {
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
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";
      const response = await fetch(`${apiUrl}/api/transcribe`, {
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

  const handleRemoveCaptionSegment = (index) => {
    const newCaptions = captions.filter((_, i) => i !== index);
    setCaptions(newCaptions);
  }

  const handleClearAllCaptions = async () => {
    setCaptions([]);
    if (!selectedVideo) return;

    setCaptionLoading(true);
    setStatus("Removing captions from video... This might take a few moments.");

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";
      const response = await fetch(`${apiUrl}/api/burn-captions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_url: selectedVideo, captions: [], caption_style: captionStyle })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setStatus("Captions removed successfully!");

        // Replace the old video with the new one
        const updatedUrls = videoUrls.map(url => url === selectedVideo ? data.video_url : url);
        setVideoUrls(updatedUrls);

        // Select the new video and clear captions editor
        setSelectedVideo(data.video_url);
        setCaptions(null); // Close the editor completely after removing all
      } else {
        setStatus("Error: " + data.message);
      }
    } catch (err) {
      setStatus("Error connecting to backend to remove captions.");
    } finally {
      setCaptionLoading(false);
    }
  }

  const handleStyleChange = (key, value) => {
    setCaptionStyle(prev => ({ ...prev, [key]: value }));
  }

  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) return;

    setIsGeneratingImage(true);
    setImageError(null);
    setGeneratedImage(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";
      const response = await fetch(`${apiUrl}/api/generate-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: imagePrompt, aspect_ratio: imageAspectRatio })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setGeneratedImage(data.image_url);
      } else {
        setImageError(data.message);
      }
    } catch (err) {
      setImageError("Failed to connect to image generation service.");
    } finally {
      setIsGeneratingImage(false);
    }
  }

  const handleBurnCaptions = async () => {
    if (!captions || !selectedVideo) return;
    
    setCaptionLoading(true);
    setStatus("Burning captions into video... This might take a few moments.");

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";
      const response = await fetch(`${apiUrl}/api/burn-captions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_url: selectedVideo, captions, caption_style: captionStyle })
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
      
      <div className="dashboard-layout">
        <aside className="sidebar">
          <header>
            <h1 className="logo" style={{fontSize: '2rem'}}>EasySlice AI</h1>
            <p style={{fontSize: '0.9rem'}}>Transform long videos into viral shorts.</p>
          </header>

          <nav className="sidebar-nav">
            <button
              className={`nav-item ${activeTab === 'slicer' ? 'active' : ''}`}
              onClick={() => setActiveTab('slicer')}
            >
              ✂️ Video Slicer
            </button>
            <button
              className={`nav-item ${activeTab === 'video-gen' ? 'active' : ''}`}
              onClick={() => setActiveTab('video-gen')}
              disabled
            >
              🎥 AI Video Generator (Soon)
            </button>
            <button
              className={`nav-item ${activeTab === 'image-gen' ? 'active' : ''}`}
              onClick={() => setActiveTab('image-gen')}
            >
              🖼️ AI Image Generator
            </button>
          </nav>
        </aside>

        <main className="main-content">
          <div className="app-container">
            {activeTab === 'slicer' && (
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
                      <button
                        onClick={() => handleRemoveCaptionSegment(idx)}
                        style={{
                          padding: '0.8rem', borderRadius: '8px', border: '1px solid rgba(236,72,153,0.3)',
                          background: 'rgba(236,72,153,0.1)', color: 'var(--secondary)', cursor: 'pointer',
                          fontWeight: 'bold'
                        }}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  {captions.length === 0 && (
                    <p style={{textAlign: 'center', color: 'var(--text-muted)', padding: '2rem'}}>No captions. Click "Save & Burn" to remove captions from the video.</p>
                  )}
                </div>
                <div style={{display: 'flex', gap: '2rem', marginTop: '2rem'}}>
                  <div style={{flex: 2, padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}}>
                    <h4 style={{marginBottom: '1rem', color: 'var(--primary)'}}>🎨 Caption Styling</h4>
                    <div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap'}}>
                      <div className="input-group" style={{flex: 1, minWidth: '150px'}}>
                        <label style={{fontSize: '0.85rem'}}>Font Size</label>
                      <input 
                        type="number" 
                        className="url-input" 
                        value={captionStyle.fontSize} 
                        onChange={(e) => handleStyleChange('fontSize', parseInt(e.target.value))} 
                        min="10" max="60"
                        style={{padding: '0.5rem'}}
                      />
                    </div>
                    <div className="input-group" style={{flex: 1, minWidth: '100px'}}>
                      <label style={{fontSize: '0.85rem'}}>Text Color</label>
                      <input 
                        type="color" 
                        className="url-input" 
                        value={captionStyle.color} 
                        onChange={(e) => handleStyleChange('color', e.target.value)} 
                        style={{height: '42px', padding: '0 5px'}}
                      />
                    </div>
                    <div className="input-group" style={{flex: 1, minWidth: '150px'}}>
                      <label style={{fontSize: '0.85rem'}}>Outline Thickness</label>
                      <div style={{display: 'flex', gap: '0.5rem'}}>
                        <input
                          type="number"
                          className="url-input"
                          value={captionStyle.outline}
                          onChange={(e) => handleStyleChange('outline', parseInt(e.target.value))}
                          min="0" max="10"
                          style={{padding: '0.5rem', flex: 1}}
                        />
                        <input
                          type="color"
                          className="url-input"
                          value={captionStyle.outlineColor}
                          onChange={(e) => handleStyleChange('outlineColor', e.target.value)}
                          style={{height: '42px', padding: '0 5px', width: '50px'}}
                        />
                      </div>
                    </div>
                    <div className="input-group" style={{flex: 1, minWidth: '150px'}}>
                      <label style={{fontSize: '0.85rem'}}>Shadow Depth</label>
                      <div style={{display: 'flex', gap: '0.5rem'}}>
                        <input
                          type="number"
                          className="url-input"
                          value={captionStyle.shadow}
                          onChange={(e) => handleStyleChange('shadow', parseInt(e.target.value))}
                          min="0" max="10"
                          style={{padding: '0.5rem', flex: 1}}
                        />
                        <input
                          type="color"
                          className="url-input"
                          value={captionStyle.shadowColor}
                          onChange={(e) => handleStyleChange('shadowColor', e.target.value)}
                          style={{height: '42px', padding: '0 5px', width: '50px'}}
                        />
                      </div>
                    </div>
                    <div className="input-group" style={{flex: 1, minWidth: '150px'}}>
                      <label style={{fontSize: '0.85rem'}}>Position</label>
                      <select 
                        className="url-input" 
                        value={captionStyle.position} 
                        onChange={(e) => handleStyleChange('position', e.target.value)}
                        style={{padding: '0.5rem'}}
                      >
                        <option value="bottom">Bottom Center</option>
                        <option value="center">Middle Center</option>
                      </select>
                    </div>
                    </div>
                  </div>
                  <div style={{flex: 1, padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}}>
                    <h4 style={{marginBottom: '1rem', color: 'var(--secondary)'}}>🎬 Animation Effects</h4>
                    <div className="input-group" style={{marginBottom: 0}}>
                      <label style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Choose modern caption style</label>
                      <select
                        className="url-input"
                        value={captionStyle.animationStyle}
                        onChange={(e) => handleStyleChange('animationStyle', e.target.value)}
                        style={{padding: '0.8rem', marginTop: '0.5rem'}}
                      >
                        <option value="sentence">None (Sentence)</option>
                        <option value="word">Word by Word</option>
                        <option value="cumulative">Cumulative</option>
                        <option value="typewriter">Typewriter</option>
                        <option value="karaoke">Karaoke (Highlight)</option>
                        <option value="fade">Fade In</option>
                        <option value="popup">Pop Up</option>
                        <option value="bounce">Bounce</option>
                        <option value="glitch">Glitch</option>
                        <option value="neon">Neon Glow</option>
                        <option value="zoom">Zoom</option>
                        <option value="slide">Slide Up</option>
                        <option value="kinetic">Kinetic Pop</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div style={{display: 'flex', gap: '1rem', marginTop: '1.5rem'}}>
                  <button
                    className="action-btn"
                    style={{flex: 1, background: 'linear-gradient(135deg, #10b981, #3b82f6)'}}
                    onClick={handleBurnCaptions}
                    disabled={captionLoading}
                  >
                    {captionLoading ? "⏳ Burning Captions..." : "🔥 Save & Burn Captions"}
                  </button>
                  <button
                    className="action-btn"
                    style={{flex: 1, background: 'transparent', border: '1px solid var(--secondary)', color: 'var(--secondary)'}}
                    onClick={handleClearAllCaptions}
                    disabled={captionLoading}
                  >
                    🗑️ Remove All Captions From Video
                  </button>
                </div>
              </div>
            )}
              </div>
            )}

            {activeTab === 'image-gen' && (
              <div className="slicer-panel">
                <h2 style={{marginBottom: '2rem'}}>AI Image Generator</h2>

                <div className="input-group">
                  <label htmlFor="img-prompt">Describe your image in detail</label>
                  <textarea
                    id="img-prompt"
                    className="url-input"
                    placeholder="A futuristic cyber city bathed in neon lights..."
                    value={imagePrompt}
                    onChange={(e) => setImagePrompt(e.target.value)}
                    disabled={isGeneratingImage}
                    rows={4}
                    style={{resize: 'vertical'}}
                  />
                </div>

                <div className="input-group">
                  <label>Aspect Ratio</label>
                  <div className="duration-selector">
                    {['1:1', '16:9', '9:16', '4:5', '3:2'].map((ratio) => (
                      <button
                        key={ratio}
                        className={`duration-btn ${imageAspectRatio === ratio ? 'active' : ''}`}
                        onClick={() => setImageAspectRatio(ratio)}
                        disabled={isGeneratingImage}
                      >
                        {ratio}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  className="action-btn"
                  onClick={handleGenerateImage}
                  disabled={isGeneratingImage || !imagePrompt.trim()}
                >
                  {isGeneratingImage ? "🎨 Painting pixels..." : "✨ Generate Masterpiece"}
                </button>

                {imageError && (
                  <div className="status-box" style={{borderColor: 'var(--secondary)', color: 'var(--secondary)', background: 'rgba(236,72,153,0.1)'}}>
                    {imageError}
                  </div>
                )}

                {generatedImage && (
                  <div style={{marginTop: '3rem'}}>
                    <h3 style={{textAlign: 'center', marginBottom: '1.5rem'}}>Your AI Creation</h3>
                    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '2rem', borderRadius: '12px'}}>
                      <img
                        src={generatedImage}
                        alt="Generated AI art"
                        style={{maxWidth: '100%', maxHeight: '600px', borderRadius: '8px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)'}}
                      />
                      <div style={{display: 'flex', gap: '1rem', marginTop: '2rem', width: '100%', justifyContent: 'center'}}>
                        <button
                          className="action-btn"
                          style={{flex: 0, padding: '0.8rem 2rem', minWidth: '150px'}}
                          onClick={handleGenerateImage}
                          disabled={isGeneratingImage}
                        >
                          🔄 Regenerate
                        </button>
                        <button
                          className="action-btn"
                          style={{flex: 0, padding: '0.8rem 2rem', background: 'transparent', border: '1px solid var(--primary)', color: 'var(--text-main)', minWidth: '150px'}}
                          onClick={() => {
                            const a = document.createElement('a');
                            a.href = generatedImage;
                            a.download = 'ai-generated-art.jpg';
                            a.click();
                          }}
                        >
                          ⬇️ Download
                        </button>
                        <button
                          className="action-btn"
                          style={{flex: 0, padding: '0.8rem 2rem', background: 'transparent', border: '1px solid var(--text-muted)', color: 'var(--text-main)', minWidth: '150px'}}
                          onClick={() => {
                            navigator.clipboard.writeText(imagePrompt);
                            alert("Prompt copied to clipboard!");
                          }}
                        >
                          📋 Copy Prompt
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  )
}

export default App
