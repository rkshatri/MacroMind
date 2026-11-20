import { useEffect, useMemo, useState } from 'react'

const buildEpisode = () => {
  const busySet = new Set()
  const eatSet = new Set()
  for (let index = 0; index < 4; index += 1) {
    busySet.add(3 + index * 7)
    eatSet.add(5 + index * 6)
  }
  return {
    busySteps: Array.from(busySet),
    eatSteps: Array.from(eatSet),
  }
}

const formatPercentage = (value) => `${Math.round(value)}%`

const randomProbabilities = (hunger, isBusy, isEating) => {
  const baseMeal = isEating ? 70 : Math.min(65, 20 + hunger * 60)
  const snack = isBusy ? 10 : Math.max(15, 40 - hunger * 20)
  const wait = Math.max(10, 100 - baseMeal - snack)
  return {
    wait,
    snack,
    meal: 100 - wait - snack,
  }
}

function AgentDemo() {
  const [step, setStep] = useState(0)
  const [hunger, setHunger] = useState(0.18)
  const [calories, setCalories] = useState(90)
  const [reward, setReward] = useState(0)
  const [actionProbs, setActionProbs] = useState({ wait: 60, snack: 25, meal: 15 })
  const episode = useMemo(buildEpisode, [])

  useEffect(() => {
    const interval = setInterval(() => {
      setStep((current) => {
        const next = current >= 29 ? 0 : current + 1
        const isBusy = episode.busySteps.includes(next)
        const isEating = episode.eatSteps.includes(next)

        setHunger((currentHunger) => {
          const delta = isEating ? -0.28 : isBusy ? 0.05 : 0.03
          return Math.max(0, Math.min(1, currentHunger + delta))
        })

        setCalories((currentCalories) => currentCalories + (isEating ? 210 : 6))
        setReward((currentReward) => currentReward + (isEating ? 2.5 : isBusy ? 0.3 : 0.6))
        setActionProbs(randomProbabilities(hunger, isBusy, isEating))

        return next
      })
    }, 200)

    return () => clearInterval(interval)
  }, [episode, hunger])

  const slots = Array.from({ length: 30 }, (_, index) => {
    if (episode.eatSteps.includes(index)) {
      return { type: 'meal' }
    }
    if (episode.busySteps.includes(index)) {
      return { type: 'busy' }
    }
    if (index === step && hunger > 0.75) {
      return { type: 'hungry' }
    }
    return { type: 'idle' }
  })

  return (
    <div className="card agent-card">
      <div className="section-heading">
        <div>
          <h2>agent demo</h2>
          <p className="section-copy">watch the policy learn.</p>
        </div>
      </div>

      <div className="episode-row">
        {slots.map((slot, index) => (
          <div
            key={index}
            className={`episode-slot ${slot.type} ${index === step ? 'active' : ''}`}
          />
        ))}
      </div>

      <div className="analytics-grid">
        <div className="metric-card">
          <strong>Hunger</strong>
          <p>{hunger.toFixed(2)}</p>
        </div>
        <div className="metric-card">
          <strong>Calories</strong>
          <p>{Math.min(3500, calories).toFixed(0)}</p>
        </div>
        <div className="metric-card">
          <strong>Reward</strong>
          <p>{reward.toFixed(1)}</p>
        </div>
      </div>

      <div className="policy-row">
        {['wait', 'snack', 'meal'].map((label) => (
          <div key={label} className="policy-slot">
            <span>{label}</span>
            <div className="policy-bar">
              <div
                className="policy-fill"
                style={{
                  width: formatPercentage(actionProbs[label]),
                  background:
                    label === 'wait'
                      ? '#D0D4D8'
                      : label === 'snack'
                      ? '#BA7517'
                      : '#1D9E75',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AgentDemo
