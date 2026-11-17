import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Dose, type Slot } from './api'

const SLOTS: Slot[] = ['morning', 'afternoon', 'evening']

function currentSlot(): Slot {
  const hour = new Date().getHours()
  if (hour < 12) return 'morning'
  if (hour < 18) return 'afternoon'
  return 'evening'
}

const doseKey = (d: Dose) => `${d.patient_id}-${d.medication_id}`

export default function App() {
  const queryClient = useQueryClient()
  const [nurse, setNurse] = useState('')
  const [slot, setSlot] = useState<Slot>(currentSlot())
  // alert text shown on a dose's row, e.g. "already given" from the API
  const [rowAlerts, setRowAlerts] = useState<Record<string, string>>({})

  const patients = useQuery({ queryKey: ['patients'], queryFn: api.patients })
  const doses = useQuery({
    queryKey: ['doses', slot],
    queryFn: () => api.doses(slot),
    refetchInterval: 60_000, // re-check every minute so doses turn "missed" when a slot ends
  })

  const setRowAlert = (d: Dose, text?: string) =>
    setRowAlerts((prev) => {
      const next = { ...prev }
      if (text) next[doseKey(d)] = text
      else delete next[doseKey(d)]
      return next
    })

  const administer = useMutation({
    mutationFn: (dose: Dose) =>
      api.administer({ patient_id: dose.patient_id, medication_id: dose.medication_id, slot, nurse }),
    onSuccess: (_, dose) => setRowAlert(dose),
    onError: (err, dose) => setRowAlert(dose, err.message),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['doses'] }),
  })


  const giveDose = (dose: Dose) => {
    if (!nurse.trim()) {
      setRowAlert(dose, 'Enter your name before recording a dose.')
      return
    }
    administer.mutate(dose)
  }

  const changeSlot = (s: Slot) => {
    setSlot(s)
    setRowAlerts({})
  }

  const counts = {
    pending: doses.data?.filter((d) => d.status === 'pending').length ?? 0,
    administered: doses.data?.filter((d) => d.status === 'administered').length ?? 0,
    missed: doses.data?.filter((d) => d.status === 'missed').length ?? 0,
  }

  return (
    <div className="page">
      <header>
        <h1>Medication Round</h1>
        <div className="controls">
          <label>
            Nurse
            <input value={nurse} onChange={(e) => setNurse(e.target.value)} placeholder="Your name" />
          </label>
        </div>
      </header>

      <nav className="tabs">
        {SLOTS.map((s) => (
          <button key={s} className={s === slot ? 'active' : ''} onClick={() => changeSlot(s)}>
            {s[0].toUpperCase() + s.slice(1)}
          </button>
        ))}
      </nav>

      <p className="summary">
        <span className="badge pending">{counts.pending} pending</span>
        <span className="badge administered">{counts.administered} given</span>
        <span className="badge missed">{counts.missed} missed</span>
      </p>

      {doses.isLoading && <p>Loading…</p>}
      {doses.isError && <p className="error-text">Can't reach the API. Is uvicorn running?</p>}

      <table>
        <thead>
          <tr>
            <th>Room</th>
            <th>Patient</th>
            <th>Medication</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {doses.data?.map((d) => (
            <tr key={doseKey(d)}>
              <td>{d.room}</td>
              <td>{d.patient_name}</td>
              <td>
                {d.medication_name} <span className="muted">{d.dosage}</span>
              </td>
              <td>
                <span className={`badge ${d.status}`}>{d.status}</span>
                {d.administered_at && (
                  <div className="muted small">
                    {new Date(d.administered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}{' '}
                    by {d.administered_by}
                  </div>
                )}
                {d.status === 'missed' && <div className="error-text small">⚠ Not given in this slot</div>}
                {rowAlerts[doseKey(d)] && <div className="error-text small">⚠ {rowAlerts[doseKey(d)]}</div>}
              </td>
              <td>
                <button
                  onClick={() => giveDose(d)}
                  disabled={administer.isPending}
                  className={d.status === 'pending' ? '' : 'secondary'}
                >
                  Mark as given
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Patients</h2>
      <div className="cards">
        {patients.data?.map((p) => (
          <div className="card" key={p.id}>
            <strong>{p.name}</strong> <span className="muted">Room {p.room}</span>
            <ul>
              {p.medications.map((m) => (
                <li key={m.id}>
                  {m.name} {m.dosage} <span className="muted">({m.slots.join(', ')})</span>
                  {m.instructions && <div className="muted small">{m.instructions}</div>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}

