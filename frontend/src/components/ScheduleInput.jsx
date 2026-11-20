import { useEffect, useMemo, useState } from 'react'

const parseTimeTo24 = (time) => {
  const match = time.match(/(\d+):(\d+)(am|pm)/i)
  if (!match) return null
  let [, hour, minute, period] = match
  hour = Number(hour)
  minute = Number(minute)
  if (period.toLowerCase() === 'pm' && hour !== 12) hour += 12
  if (period.toLowerCase() === 'am' && hour === 12) hour = 0
  return { hour, minute }
}

const addMinutes = (time, increment) => {
  const parsed = parseTimeTo24(time)
  if (!parsed) return time
  let total = parsed.hour * 60 + parsed.minute + increment
  total = (total + 24 * 60) % (24 * 60)
  const hour = Math.floor(total / 60)
  const minute = total % 60
  const suffix = hour < 12 ? 'am' : 'pm'
  const displayHour = hour % 12 === 0 ? 12 : hour % 12
  return `${displayHour}:${minute.toString().padStart(2, '0')}${suffix}`
}

const createStartTimeOptions = () => {
  const options = []
  for (let hour = 3; hour <= 11; hour += 1) {
    for (let minute = 0; minute < 60; minute += 30) {
      const displayHour = hour % 12 === 0 ? 12 : hour % 12
      const suffix = hour < 12 ? 'am' : 'pm'
      const label = `${displayHour}:${minute.toString().padStart(2, '0')}${suffix}`
      options.push({ value: label, label })
    }
  }
  return options
}

const createTimeOptions = (wakeTime) => {
  const parsed = wakeTime.match(/(\d+):(\d+)(am|pm)/i)
  if (!parsed) {
    return []
  }
  let [, hour, minute, suffix] = parsed
  hour = Number(hour)
  minute = Number(minute)
  if (suffix.toLowerCase() === 'pm' && hour !== 12) hour += 12
  if (suffix.toLowerCase() === 'am' && hour === 12) hour = 0

  const options = []
  for (let index = 0; index < 30; index += 1) {
    const total = hour * 60 + minute + index * 30
    const normalized = (total + 24 * 60) % (24 * 60)
    const optionHour = Math.floor(normalized / 60)
    const optionMinute = normalized % 60
    const displayHour = optionHour % 12 === 0 ? 12 : optionHour % 12
    const optionSuffix = optionHour < 12 ? 'am' : 'pm'
    const label = `${displayHour}:${optionMinute.toString().padStart(2, '0')}${optionSuffix}`
    options.push({ value: label, label })
  }
  return options
}

const addBlockToSchedule = (schedule, setSchedule, key, block) => {
  const list = schedule[key]
  const alreadyExists = list.some(
    (item) => item.start === block.start && item.end === block.end
  )
  if (alreadyExists) {
    return
  }

  setSchedule({
    ...schedule,
    [key]: [...list, block],
  })
}

const removeBlock = (schedule, setSchedule, key, index) => {
  const nextBlocks = schedule[key].filter((_, itemIndex) => itemIndex !== index)
  setSchedule({
    ...schedule,
    [key]: nextBlocks,
  })
}

function ScheduleInput({ schedule, setSchedule, onGenerate, prefs, onWakeTimeChange }) {
  const dayStartOptions = useMemo(createStartTimeOptions, [])
  const options = useMemo(() => createTimeOptions(prefs.wake_time), [prefs.wake_time])
  const [busyStart, setBusyStart] = useState(options[0]?.value || '')
  const [busyEnd, setBusyEnd] = useState(options[1]?.value || options[0]?.value || '')
  const [workoutStart, setWorkoutStart] = useState(options[0]?.value || '')
  const [workoutEnd, setWorkoutEnd] = useState(options[1]?.value || options[0]?.value || '')

  useEffect(() => {
    if (!options.length) {
      return
    }

    if (!options.some((option) => option.value === busyStart)) {
      setBusyStart(options[0].value)
    }
    if (!options.some((option) => option.value === busyEnd)) {
      setBusyEnd(options[1]?.value || options[0].value)
    }
    if (!options.some((option) => option.value === workoutStart)) {
      setWorkoutStart(options[0].value)
    }
    if (!options.some((option) => option.value === workoutEnd)) {
      setWorkoutEnd(options[1]?.value || options[0].value)
    }
  }, [options, busyStart, busyEnd, workoutStart, workoutEnd])

  const dayEndTime = addMinutes(prefs.wake_time, 900)

  const handleRemoveBusyBlock = (index) => {
    removeBlock(schedule, setSchedule, 'busy_blocks', index)
  }

  return (
    <div className="card schedule-card">
      <div className="section">
        <div className="section-heading">
          <h2>day start</h2>
          <p className="section-copy">Choose when your day begins, and the timeline adjusts accordingly.</p>
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="day-start">day begins</label>
            <select
              id="day-start"
              value={prefs.wake_time}
              onChange={(event) => onWakeTimeChange(event.target.value)}
            >
              {dayStartOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>day ends</label>
            <div className="day-boundary-value">{dayEndTime}</div>
          </div>
          <div />
        </div>
      </div>

      <div className="section-divider" />

      <div className="section">
        <div className="section-heading">
          <h2>busy windows</h2>
          <p className="section-copy">Add times when you need to stay focused.</p>
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="busy-start">start</label>
            <select
              id="busy-start"
              value={busyStart}
              onChange={(event) => setBusyStart(event.target.value)}
            >
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="busy-end">end</label>
            <select
              id="busy-end"
              value={busyEnd}
              onChange={(event) => setBusyEnd(event.target.value)}
            >
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="primary-button"
            onClick={() => {
              if (busyStart !== busyEnd) {
                addBlockToSchedule(schedule, setSchedule, 'busy_blocks', {
                  start: busyStart,
                  end: busyEnd,
                })
              }
            }}
          >
            add
          </button>
        </div>
        <div className="chip-list">
          {schedule.busy_blocks.map((block, index) => (
            <span key={`${block.start}-${block.end}-${index}`} className="chip">
              {`${block.start} – ${block.end}`}
              <button
                type="button"
                onClick={() => handleRemoveBusyBlock(index)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="section-divider" />

      <div className="section">
        <div className="section-heading">
          <h2>workout window</h2>
          <p className="section-copy">Block movement or exercise time so meals stay on track.</p>
        </div>
        <div className="form-row">
          <div>
            <label htmlFor="workout-start">start</label>
            <select
              id="workout-start"
              value={workoutStart}
              onChange={(event) => setWorkoutStart(event.target.value)}
            >
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="workout-end">end</label>
            <select
              id="workout-end"
              value={workoutEnd}
              onChange={(event) => setWorkoutEnd(event.target.value)}
            >
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="primary-button"
            onClick={() => {
              if (workoutStart !== workoutEnd) {
                addBlockToSchedule(schedule, setSchedule, 'workout_blocks', {
                  start: workoutStart,
                  end: workoutEnd,
                })
              }
            }}
          >
            add
          </button>
        </div>
        <div className="chip-list">
          {schedule.workout_blocks.map((block, index) => (
            <span key={`${block.start}-${block.end}-${index}`} className="chip workout">
              {block.start} – {block.end}
              <button
                type="button"
                onClick={() => removeBlock(schedule, setSchedule, 'workout_blocks', index)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="section-divider" />

      <div className="section">
        <button type="button" className="primary-button full-width" onClick={onGenerate}>
          Generate my plan →
        </button>
      </div>
    </div>
  )
}

export default ScheduleInput
