import { useEffect, useState } from 'react'
import { getPantry, updatePantry } from '../api'

function PantryPanel({ open, onClose }) {
  const [pantry, setPantry] = useState([])
  const [form, setForm] = useState({
    name: '',
    meal_type: 'any',
    calories_per_unit: '',
    protein_per_unit: '',
    carbs_per_unit: '',
    fat_per_unit: '',
    unit: '',
    default_quantity: 1,
  })

  useEffect(() => {
    if (!open) {
      return
    }

    getPantry()
      .then((data) => setPantry(data.foods || []))
      .catch((error) => {
        console.error(error)
        setPantry([])
      })
  }, [open])

  const addFood = () => {
    if (!form.name.trim()) {
      return
    }

    setPantry((current) => [
      ...current,
      {
        name: form.name,
        meal_type: form.meal_type,
        calories_per_unit: Number(form.calories_per_unit) || 0,
        protein_per_unit: Number(form.protein_per_unit) || 0,
        carbs_per_unit: Number(form.carbs_per_unit) || 0,
        fat_per_unit: Number(form.fat_per_unit) || 0,
        unit: form.unit || 'serving',
        default_quantity: Number(form.default_quantity) || 1,
      },
    ])
    setForm({
      name: '',
      meal_type: 'any',
      calories_per_unit: '',
      protein_per_unit: '',
      carbs_per_unit: '',
      fat_per_unit: '',
      unit: '',
      default_quantity: 1,
    })
  }

  const removeFood = (index) => {
    setPantry((current) => current.filter((_, itemIndex) => itemIndex !== index))
  }

  const savePantry = async () => {
    try {
      await updatePantry({ foods: pantry })
      window.alert('Pantry saved successfully')
    } catch (error) {
      console.error(error)
      window.alert('Unable to save pantry')
    }
  }

  if (!open) {
    return null
  }

  return (
    <>
      <div className="pantry-backdrop" onClick={onClose} />
      <aside className="pantry-panel">
        <div className="pantry-header">
          <div>
            <h2>pantry</h2>
            <p className="section-copy">Manage the foods your agent can choose.</p>
          </div>
          <button type="button" className="secondary-button" onClick={onClose}>
            close
          </button>
        </div>

        {pantry.map((item, index) => (
          <div key={`${item.name}-${index}`} className="pantry-row">
            <div>
              <p><strong>{item.name}<small className='small'> · {item.meal_type}</small></strong>
              </p>
              <small>{item.calories_per_unit} cal · {item.protein_per_unit}g protein · {item.carbs_per_unit}g carbs · {item.fat_per_unit}g fat · qty {item.default_quantity}</small>
            </div>
            <button type="button" className="pantry-remove" onClick={() => removeFood(index)}>
              ×
            </button>
          </div>
        ))}

        <div className="pantry-form">
          <label>
            name
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </label>
          <label>
            meal type
            <select value={form.meal_type} onChange={(event) => setForm({ ...form, meal_type: event.target.value })}>
              <option value="any">any</option>
              <option value="breakfast">breakfast</option>
              <option value="snack">snack</option>
            </select>
          </label>
          <label>
            calories
            <input
              type="number"
              value={form.calories_per_unit}
              onChange={(event) => setForm({ ...form, calories_per_unit: event.target.value })}
            />
          </label>
          <label>
            protein
            <input
              type="number"
              value={form.protein_per_unit}
              onChange={(event) => setForm({ ...form, protein_per_unit: event.target.value })}
            />
          </label>
          <label>
            carbs
            <input
              type="number"
              value={form.carbs_per_unit}
              onChange={(event) => setForm({ ...form, carbs_per_unit: event.target.value })}
            />
          </label>
          <label>
            fat
            <input
              type="number"
              value={form.fat_per_unit}
              onChange={(event) => setForm({ ...form, fat_per_unit: event.target.value })}
            />
          </label>
          <label>
            quantity
            <input
              type="number"
              value={form.default_quantity}
              min="1"
              onChange={(event) => setForm({ ...form, default_quantity: event.target.value })}
            />
          </label>
        </div>

        <div className="pantry-footer">
          <button type="button" className="primary-button full-width" onClick={addFood}>
            add food
          </button>
          <button type="button" className="secondary-button full-width" onClick={savePantry}>
            save pantry
          </button>
        </div>
      </aside>
    </>
  )
}

export default PantryPanel
