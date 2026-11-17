export type Slot = 'morning' | 'afternoon' | 'evening'
export type Status = 'pending' | 'administered' | 'missed'

export interface Medication {
  id: string
  name: string
  dosage: string
  instructions: string
  slots: Slot[]
}

export interface Patient {
  id: string
  name: string
  room: string
  medications: Medication[]
}

export interface Dose {
  patient_id: string
  patient_name: string
  room: string
  medication_id: string
  medication_name: string
  dosage: string
  slot: Slot
  status: Status
  administered_at: string | null
  administered_by: string | null
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? 'Something went wrong')
  return data
}

export const api = {
  patients: () => request<Patient[]>('/api/patients'),
  doses: (slot: Slot) => request<Dose[]>(`/api/doses?slot=${slot}`),
  administer: (body: { patient_id: string; medication_id: string; slot: Slot; nurse: string }) =>
    request('/api/doses/administer', { method: 'POST', body: JSON.stringify(body) }),
  reset: () => request('/api/demo/reset', { method: 'POST' }),
}
