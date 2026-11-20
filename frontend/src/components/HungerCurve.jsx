import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from 'recharts'

const addMinutes = (time, increment) => {
  const match = time.match(/(\d+):(\d+)(am|pm)/i)
  if (!match) {
    return time
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

  let total = hour * 60 + minute + increment
  total = (total + 24 * 60) % (24 * 60)
  const nextHour = Math.floor(total / 60)
  const nextMinute = total % 60
  const suffix = nextHour < 12 ? 'am' : 'pm'
  const displayHour = nextHour % 12 === 0 ? 12 : nextHour % 12
  if (nextMinute == 0) {
    return `${displayHour}${suffix}`
  }
  else {
    return `${displayHour}:${nextMinute.toString().padStart(2, '0')}${suffix}`
  }
}

const buildChartData = (hungerCurve, wakeTime) =>
  hungerCurve.map((value, index) => ({
    step: index,
    hunger: value,
  }))

function HungerCurve({ hungerCurve, wakeTime }) {
  const data = buildChartData(hungerCurve || [], wakeTime)
  const xTickFormatter = (step) => addMinutes(wakeTime, Number(step) * 30)
  const tickValues = data.length > 1
    ? Array.from({ length: Math.min(7, data.length) }, (_, index) =>
        Math.round((index * (data.length - 1)) / Math.max(1, Math.min(7, data.length) - 1))
      )
    : [0]

  return (
    <div className="hunger-chart-card">
      <div className="section-heading">
        <h2>hunger across the day</h2>
      </div>
      <div style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 20 }}>
            <XAxis
              dataKey="step"
              type="number"
              domain={[0, data.length > 1 ? data.length - 1 : 1]}
              ticks={tickValues}
              tickFormatter={xTickFormatter}
              interval="preserveStartEnd"
              minTickGap={8}
              tick={{ fill: '#6B6860', fontSize: 12, fontFamily: 'system-ui, sans-serif' }}
              axisLine={true}
              tickLine={true}
              label={{ value: 'Time', position: 'insideBottomRight', offset: -6, fill: '#6B6860', fontSize: 12 }}
            />
            <YAxis
              domain={[0, 1]}
              tickCount={5}
              tick={{ fill: '#6B6860', fontSize: 12, fontFamily: 'system-ui, sans-serif' }}
              axisLine={false}
              tickLine={false}
            />
            <ReferenceLine y={0.7} stroke="#9B9890" strokeDasharray="4 4" />
            <Area type="monotone" dataKey="hunger" stroke="#BA7517" strokeWidth={2} fill="rgba(186, 117, 23, 0.08)" fillOpacity={1} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default HungerCurve
