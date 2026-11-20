import { useState } from 'react'

function Explanation({ explanation, sources }) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="explanation-card">
      <div className="explanation-title">
        <div>
          <p className="eyebrow">nutrition coach</p>
          <p className="explanation-subtitle">powered by llama3.2</p>
        </div>
        <button
          type="button"
          className="toggle-button"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? 'collapse' : 'expand'}
          <span className={`toggle-icon ${expanded ? '' : 'collapsed'}`}>›</span>
        </button>
      </div>
      {expanded && <p className="explanation-copy">{explanation}</p>}
      <div className="explanation-footer">
        sources: {sources.join(' · ')}
      </div>
    </div>
  )
}

export default Explanation
