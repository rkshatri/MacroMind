import axios from 'axios'

const BASE_URL = 'http://localhost:8000/api'

export async function generatePlan(payload) {
  const body = { ...payload }

  if (body.prefs && !body.user_prefs) {
    body.user_prefs = body.prefs
  }

  const response = await axios.post(`${BASE_URL}/generate`, body)
  return response.data
}

export async function getPantry() {
  const response = await axios.get(`${BASE_URL}/pantry`)
  return response.data
}

export async function updatePantry(data) {
  const response = await axios.post(`${BASE_URL}/pantry`, data)
  return response.data
}
