function MacroProgress({ totals, targets }) {
  const rows = [
    { label: 'calories', key: 'calories', color: '#BA7517', unit: 'cal' },
    { label: 'protein', key: 'protein', color: '#1D9E75', unit: 'g' },
    { label: 'carbs', key: 'carbs', color: '#6B6860', unit: 'g' },
    { label: 'fat', key: 'fat', color: '#BA7517', unit: 'g' },
  ]

  return (
    <div className="card">
      <div className="section-heading">
        <h2>macro progress</h2>
        <p className="section-copy">See where the day is ahead of or behind target.</p>
      </div>
      <div className="progress-row">
        {rows.map((row) => {
          const consumed = totals[row.key] ?? 0
          const target = targets[row.key] ?? 1
          const ratio = Math.min((consumed / target) * 100, 110)
          const overTarget = consumed > target * 1.1
          return (
            <div key={row.key}>
              <div className="progress-label">
                <span>{row.label}</span>
                <span>
                  {Math.round(consumed)} / {target}
                  {row.unit}
                </span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{
                    width: `${ratio}%`,
                    background: overTarget ? '#E24B4A' : row.color,
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default MacroProgress
