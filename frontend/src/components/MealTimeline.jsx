import { useMemo } from 'react'

const parseMinutes = (time) => {
  const match = time.match(/(\d+):(\d+)(am|pm)/i)
  if (!match) {
    return 0
  }
  let [, hour, minute, period] = match
  hour = Number(hour)
  minute = Number(minute)

  if (period.toLowerCase() === 'pm' && hour !== 12) {
    hour += 12
  }
  if (period.toLowerCase() === 'am' && hour === 12) {
    hour = 0
  }
  return hour * 60 + minute
}

const isTimeBlock = (block) => block && typeof block === 'object' && 'start' in block && 'end' in block

const rangeGroups = (times) => {
  const sorted = [...times].sort((a, b) => parseMinutes(a) - parseMinutes(b))
  const groups = []
  let current = []

  sorted.forEach((time) => {
    if (!current.length) {
      current = [time]
      return
    }

    const previous = current[current.length - 1]
    if (parseMinutes(time) - parseMinutes(previous) === 30) {
      current.push(time)
    } else {
      groups.push(current)
      current = [time]
    }
  })

  if (current.length) {
    groups.push(current)
  }

  return groups
}

const formatRange = (group) => {
  if (group.length === 1) {
    return group[0]
  }

  const start = group[0]
  const endTime = parseMinutes(group[group.length - 1]) + 30
  const hour = Math.floor(endTime / 60) % 12 || 12
  const minute = endTime % 60
  const suffix = endTime < 720 ? 'am' : 'pm'
  return `${start} – ${hour}:${minute.toString().padStart(2, '0')}${suffix}`
}

function MealTimeline({ meals, busyBlocks, workoutBlocks }) {
  const entries = useMemo(() => {
    const items = []

    if (Array.isArray(busyBlocks)) {
      if (busyBlocks.every(isTimeBlock)) {
        busyBlocks.forEach((block) => {
          items.push({
            type: 'busy',
            time: block.start,
            label: `busy · ${block.start} – ${block.end}`,
            order: parseMinutes(block.start),
          })
        })
      } else {
        const busyGroups = rangeGroups(busyBlocks)
        busyGroups.forEach((group) => {
          items.push({
            type: 'busy',
            time: group[0],
            label: `busy · ${formatRange(group)}`,
            order: parseMinutes(group[0]),
          })
        })
      }
    }

    if (Array.isArray(workoutBlocks)) {
      if (workoutBlocks.every(isTimeBlock)) {
        workoutBlocks.forEach((block) => {
          items.push({
            type: 'workout',
            time: block.start,
            label: `workout · ${block.start} – ${block.end}`,
            order: parseMinutes(block.start),
          })
        })
      } else {
        const workoutGroups = rangeGroups(workoutBlocks)
        workoutGroups.forEach((group) => {
          items.push({
            type: 'workout',
            time: group[0],
            label: `workout · ${formatRange(group)}`,
            order: parseMinutes(group[0]),
          })
        })
      }
    }

    meals.forEach((meal) => {
      items.push({
        type: 'meal',
        time: meal.time,
        label: meal.food,
        meta: `${meal.calories} cal · ${meal.protein}g protein · ${meal.carbs}g carbs · ${meal.fat}g fat`,
        mealType: meal.type,
        order: parseMinutes(meal.time),
      })
    })

    return items.sort((a, b) => a.order - b.order)
  }, [meals, busyBlocks, workoutBlocks])

  return (
    <div className="card">
      <div className="section-heading">
        <h2>meal timeline</h2>
        <p className="section-copy">Review how the agent spaced meals, workouts, and busy time.</p>
      </div>
      <div className="timeline-list">
        {entries.map((entry, index) => (
          <div key={`${entry.type}-${entry.time}-${index}`} className="timeline-entry">
            <div
              className="timeline-dot"
              style={{ background: entry.dotColor || (entry.type === 'meal' ? '#1D9E75' : entry.type === 'busy' ? '#BA7517' : entry.type === 'workout' ? '#5366C5' : '#B7B5AF') }}
            />
            <div className={`timeline-card ${entry.type === 'busy' ? 'dashed' : ''}`}>
              <div className="timeline-card-header">
                <span className="timeline-time">{entry.time}</span>
                <h3 className={entry.type === 'meal' ? 'meal' : ''}>{entry.label}</h3>
              </div>
              {entry.meta && <p>{entry.meta}</p>}
              {entry.type === 'meal' && (
                <span className="badge meal-badge">{entry.mealType}</span>
              )}
              {entry.type === 'workout' && (
                <span className="badge workout-badge">workout</span>
              )}
              {entry.type === 'busy' && (
                <span className="badge busy-badge">busy</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MealTimeline
