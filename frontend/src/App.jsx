import { useEffect, useRef, useState } from 'react'
import './App.css'
import ScheduleInput from './components/ScheduleInput'
import MealTimeline from './components/MealTimeline'
import MacroProgress from './components/MacroProgress'
import HungerCurve from './components/HungerCurve'
import Explanation from './components/Explanation'
import PantryPanel from './components/PantryPanel'
import { generatePlan } from './api'

const defaultPrefs = {
  wake_time: '6:00am',
  first_meal_time: '7:30am',
  evening_cutoff_time: '9:30pm',
  targets: {
    calories: 2400,
    protein: 150,
    carbs: 200,
    fat: 65,
  },
}

const heroCopy =
  "MacroMind uses a PPO reinforcement learning agent trained on thousands of simulated days to learn when to eat, and how to work around your schedule to hit your macros."

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

const formatTimeLabel = (hour, minute) => {
  const suffix = hour < 12 ? 'am' : 'pm'
  const displayHour = hour % 12 === 0 ? 12 : hour % 12
  return `${displayHour}:${minute.toString().padStart(2, '0')}${suffix}`
}

const addMinutes = (time, increment) => {
  const parsed = parseTimeTo24(time)
  if (!parsed) return time
  let total = parsed.hour * 60 + parsed.minute + increment
  total = (total + 24 * 60) % (24 * 60)
  return formatTimeLabel(Math.floor(total / 60), total % 60)
}

const getDayEndTime = (wakeTime) => addMinutes(wakeTime, 900)

const timeToStep = (timeStr, wakeTime) => {
  const parsed = parseTimeTo24(timeStr)
  const wake = parseTimeTo24(wakeTime)
  if (!parsed || !wake) return 0

  let totalMinutes = parsed.hour * 60 + parsed.minute
  let wakeMinutes = wake.hour * 60 + wake.minute
  let step = Math.floor((totalMinutes - wakeMinutes) / 30)
  return Math.max(0, Math.min(step, 29))
}

const getDefaultMorningRoutine = (wakeTime, firstMealTime) => {
  const step = timeToStep(firstMealTime, wakeTime)
  if (step <= 0) return null
  return {
    start: wakeTime,
    end: addMinutes(wakeTime, step * 30),
  }
}

const getDefaultEveningWinddown = (wakeTime, eveningCutoffTime) => {
  const step = timeToStep(eveningCutoffTime, wakeTime)
  const start = addMinutes(wakeTime, step * 30)
  return {
    start,
    end: addMinutes(start, 30),
  }
}

const loadingSteps = [
  {
    title: 'Reading your schedule',
    copy: 'The agent maps your busy blocks and workout windows into a 30-step day.',
  },
  {
    title: 'Planning the day',
    copy: 'The agent is choosing actions across 30 timesteps, balancing hunger, macros, and your schedule.',
  },
  {
    title: 'Selecting from your pantry',
    copy: 'The food library scores every item in your pantry against your current macro deficit and picks the best match.',
  },
  {
    title: 'Writing your explanation',
    copy: 'The agent retrieves real nutrition research and an LLM drafts a personalized explanation of every decision.',
  },
]

function HeroIllustration() {
  const timelineItems = [
    { time: '7:30am', label: '2 eggs', side: 'left', accent: '#1D9E75', y: 86 },
    { time: '10:00am', label: 'meeting', side: 'right', accent: '#BA7517', y: 142 },
    { time: '12:30pm', label: 'Quesadilla', side: 'left', accent: '#1D9E75', y: 198 },
    { time: '3:00pm', label: 'workout', side: 'right', accent: '#5366C5', y: 254 },
    { time: '6:00pm', label: 'Pasta', side: 'left', accent: '#1D9E75', y: 310 },
  ]

  const getCardWidth = (label) => Math.min(168, Math.max(105, 94 + label.length * 2))

  return (
    <svg viewBox="0 0 360 420" className="hero-illustration" role="img" aria-label="Warm illustrated day timeline">
      <rect x="12" y="12" width="336" height="396" rx="30" fill="#fff" stroke="#E2DDD6" strokeWidth="2" />
      <path d="M 180 64 v 292" fill="none" strokeDasharray="6" stroke="#E2DDD6" strokeWidth="3" strokeLinecap="round" />
      <path d="M 180 356 l -5 -7 m 5 7 l 5 -7" fill="none" stroke="#E2DDD6" strokeWidth="3"/>

      {timelineItems.map((item) => {
        const cardWidth = getCardWidth(item.label)
        const cardX = item.side === 'left' ? 160 - cardWidth : 200
        const textX = cardX + cardWidth / 2
        const cardY = item.y - 20

        return (
          <g key={item.time}>
            <circle cx="180" cy={item.y} r="10" fill={item.accent} />
            <rect x={cardX} y={cardY} width={cardWidth} height="42" rx="18" fill="#F5EFE6" stroke="#E2DDD6" strokeWidth="2" />
            <text x={textX} y={item.y - 4} fill="#2C2A27" fontSize="12" fontFamily="Georgia, Times New Roman, serif" textAnchor="middle">
              {item.time}
            </text>
            <text x={textX} y={item.y + 12} fill="#6B6860" fontSize="11" fontFamily="system-ui, sans-serif" textAnchor="middle">
              {item.label}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function App() {
  const [view, setView] = useState('setup')
  const [prefs, setPrefs] = useState(defaultPrefs)
  const [schedule, setSchedule] = useState(() => {
    const busyBlocks = []
    const morningBlock = getDefaultMorningRoutine(defaultPrefs.wake_time, defaultPrefs.first_meal_time)
    if (morningBlock) busyBlocks.push(morningBlock)
    busyBlocks.push(getDefaultEveningWinddown(defaultPrefs.wake_time, defaultPrefs.evening_cutoff_time))
    return {
      busy_blocks: busyBlocks,
      workout_blocks: [],
    }
  })
  const [showPantry, setShowPantry] = useState(false)
  const [hasMorningRoutine, setHasMorningRoutine] = useState(true)
  const [hasEveningWinddown, setHasEveningWinddown] = useState(true)
  const [mealPlan, setMealPlan] = useState(null)
  const [loadingStep, setLoadingStep] = useState(0)
  const howItWorksRef = useRef(null)
  const demoRef = useRef(null)

  useEffect(() => {
    if (view !== 'loading') {
      return undefined
    }

    setLoadingStep(0)
    const interval = window.setInterval(() => {
      setLoadingStep((current) => (current + 1) % loadingSteps.length)
    }, 2500)

    return () => window.clearInterval(interval)
  }, [view])

  const scrollTo = (ref) => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleWakeTimeChange = (newWakeTime) => {
    const oldWakeTime = prefs.wake_time
    setPrefs((current) => ({ ...current, wake_time: newWakeTime }))

    if (hasMorningRoutine || hasEveningWinddown) {
      const oldMorningRoutine = getDefaultMorningRoutine(oldWakeTime, prefs.first_meal_time)
      const oldEveningWinddown = getDefaultEveningWinddown(oldWakeTime, prefs.evening_cutoff_time)
      const nextMorningRoutine = getDefaultMorningRoutine(newWakeTime, prefs.first_meal_time)
      const nextEveningWinddown = getDefaultEveningWinddown(newWakeTime, prefs.evening_cutoff_time)

      setSchedule((currentSchedule) => {
        const nextBusyBlocks = currentSchedule.busy_blocks
          .map((block) => {
            const isMorning = hasMorningRoutine && oldMorningRoutine && block.start === oldMorningRoutine.start && block.end === oldMorningRoutine.end
            const isEvening = hasEveningWinddown && block.start === oldEveningWinddown.start && block.end === oldEveningWinddown.end

            if (isMorning) return nextMorningRoutine
            if (isEvening) return nextEveningWinddown
            return block
          })
          .filter(Boolean)

        return {
          ...currentSchedule,
          busy_blocks: nextBusyBlocks,
        }
      })
    }
  }

  const handleGenerate = async () => {
    setView('loading')
    try {
      const response = await generatePlan({
        busy_blocks: schedule.busy_blocks,
        workout_blocks: schedule.workout_blocks,
        prefs,
      })
      setMealPlan(response)
      setView('results')
    } catch (error) {
      console.error(error)
      setView('setup')
      window.alert('Unable to generate a meal plan. Please try again.')
    }
  }

  const resetPlan = () => {
    setPrefs(defaultPrefs)
    setSchedule(() => {
      const busyBlocks = []
      const morningBlock = getDefaultMorningRoutine(defaultPrefs.wake_time, defaultPrefs.first_meal_time)
      if (morningBlock) busyBlocks.push(morningBlock)
      busyBlocks.push(getDefaultEveningWinddown(defaultPrefs.wake_time, defaultPrefs.evening_cutoff_time))
      return {
        busy_blocks: busyBlocks,
        workout_blocks: [],
      }
    })
    setHasMorningRoutine(true)
    setHasEveningWinddown(true)
    setMealPlan(null)
    setView('setup')
    demoRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const workoutBlocksForTimeline = schedule.workout_blocks.length
    ? schedule.workout_blocks
    : (mealPlan?.workout_blocks ?? [])

  return (
    <div className="app-shell">
      <header className="page-nav">
        <div className="brand">MacroMind</div>
        <nav className="nav-links">
          <button type="button" onClick={() => scrollTo(howItWorksRef)}>
            how it works
          </button>
          <button type="button" onClick={() => scrollTo(demoRef)}>
            try it
          </button>
          <button type="button" className="nav-ghost" onClick={() => setShowPantry(true)}>
            pantry
          </button>
        </nav>
      </header>

      <main>
        <section className="hero-section">
          <div className="hero-copy">
            <p className="section-label">REINFORCEMENT LEARNING · NUTRITION</p>
            <h1>MacroMind</h1>
            <p className="hero-subtitle">An AI agent that learns to plan your meals around your life</p>
            <p className="hero-body">{heroCopy}</p>
            <div className="hero-actions">
              <button type="button" className="primary-button hero-button" onClick={() => scrollTo(demoRef)}>
                try it
              </button>
              <button type="button" className="ghost-button hero-button" onClick={() => scrollTo(howItWorksRef)}>
                how it works
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <HeroIllustration />
          </div>
        </section>

        <section className="section accent-section how-section" ref={howItWorksRef}>
          <div className="section-intro">
            <p className="section-label">HOW IT WORKS</p>
            <h2>How MacroMind thinks about your day</h2>
          </div>
          <div className="feature-grid">
            <article className="feature-card">
              <span className="feature-number">01</span>
              <h3>The Environment</h3>
              <p>Every day is simulated as 30 timesteps, each representing 30 minutes. The agent lives in this environment — it sees your schedule, your hunger level, and your remaining macro targets at every step.</p>
            </article>
            <article className="feature-card">
              <span className="feature-number">02</span>
              <h3>The Policy</h3>
              <p>A PPO neural network learns which action to take at each timestep: wait, eat a snack, or eat a meal. Over thousands of simulated days, it discovers that eating before busy blocks, recovering after workouts, and spacing meals evenly leads to the highest reward.</p>
            </article>
            <article className="feature-card">
              <span className="feature-number">03</span>
              <h3>The Explanation</h3>
              <p>After the agent plans your day, a RAG pipeline retrieves relevant nutrition research and generates a plain-language explanation of every decision — grounded in science, not generic advice.</p>
            </article>
          </div>
          <blockquote className="feature-quote">
            The agent doesn't follow rules. It writes them.
          </blockquote>
        </section>

        <section className="section demo-section" ref={demoRef}>
          <div className="section-intro">
            <p className="section-label">TRY IT</p>
            <h2>Plan a day that feels simple and sensible</h2>
            <p className="hero-body">Add your busy blocks and workout windows for today. The agent will plan meals around your schedule, respecting your macro targets and hunger patterns.</p>
          </div>

          <div className="demo-grid">
            <aside className="demo-column schedule-column">
              <ScheduleInput
                schedule={schedule}
                setSchedule={setSchedule}
                onGenerate={handleGenerate}
                prefs={prefs}
                onWakeTimeChange={handleWakeTimeChange}
                hasMorningRoutine={hasMorningRoutine}
                setHasMorningRoutine={setHasMorningRoutine}
                hasEveningWinddown={hasEveningWinddown}
                setHasEveningWinddown={setHasEveningWinddown}
              />
            </aside>

            <div className="demo-column results-column">
              {mealPlan ? (
                <div className="results-group">
                  <div className="results-header-compact">
                    <div>
                      <p className="section-label">YOUR PLAN</p>
                      <h3>Here’s what the agent chose</h3>
                    </div>
                    <button type="button" className="secondary-button" onClick={resetPlan}>
                      plan another day
                    </button>
                  </div>

                  <div className='section-divider'/>

                  <MealTimeline
                    meals={mealPlan.meals}
                    busyBlocks={schedule.busy_blocks.filter((block) => {
                      const morningRoutineBlock = hasMorningRoutine &&
                        block.start === prefs.wake_time &&
                        block.end === prefs.first_meal_time

                      const eveningWinddownBlock = hasEveningWinddown &&
                        block.start === prefs.evening_cutoff_time &&
                        block.end === getDayEndTime(prefs.wake_time)

                      return !morningRoutineBlock && !eveningWinddownBlock
                    })}
                    workoutBlocks={workoutBlocksForTimeline}
                    morningRoutine={mealPlan.morning_routine}
                    eveningCutoff={mealPlan.evening_cutoff}
                  />
                  <MacroProgress totals={mealPlan.totals} targets={mealPlan.targets} />
                  <HungerCurve hungerCurve={mealPlan.hunger_curve} wakeTime={prefs.wake_time} />
                  <Explanation explanation={mealPlan.explanation} sources={['macro_timing', 'meal_spacing']} />
                </div>
              ) : (
                <div className="placeholder-card">
                  <div className="placeholder-graphic">
                    <div className="placeholder-line" />
                    <div className="placeholder-dot dot-meal" />
                    <div className="placeholder-dot dot-busy" />
                    <div className="placeholder-dot dot-meal small" />
                    <div className="placeholder-line short" />
                    <div className="placeholder-dot dot-meal" />
                    <div className="placeholder-text">your meal plan will appear here</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        <footer className="footer-section">
          <div className="footer-grid" style={{ marginTop: '20px' }}>
            <div>
              <p className="section-label">MODEL</p>
              <h3>PPO via Stable-Baselines3</h3>
              <p>Custom Gymnasium environment, 30-step day simulation, and a personalized food library from USDA data.</p>
            </div>
            <div>
              <p className="section-label">EXPLANATION</p>
              <h3>LangChain + Ollama</h3>
              <p>FAISS vector retrieval, nomic-embed-text embeddings, and a nutrition knowledge base to support grounded reasoning.</p>
            </div>
            <div>
              <p className="section-label">INFRASTRUCTURE</p>
              <h3>FastAPI + React</h3>
              <p>Backend API, Vite frontend, AWS EC2 with S3 and CloudFront, all built on Python 3.11.</p>
            </div>
          </div>
          <p className="footer-tagline" style={{ marginTop: '60px' }}>Built by Rohan Kshatriya · 2026</p>
        </footer>
      </main>

      {view === 'loading' && (
        <div className="loading-overlay">
          <div className="loading-inner simplified">
            {loadingSteps.map((step, index) => (
              <div key={step.title} className={`loading-step simplified ${loadingStep === index ? 'active' : ''}`}>
                <div className="loading-icon" aria-hidden="true">
                  {index === 0 && ' 🧠 '}
                  {index === 1 && ' ⚙️ '}
                  {index === 2 && ' 🧪 '}
                  {index === 3 && ' ✍️ '}
                </div>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.copy}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <PantryPanel open={showPantry} onClose={() => setShowPantry(false)} />
    </div>
  )
}

export default App
