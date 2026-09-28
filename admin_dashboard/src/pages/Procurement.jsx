import { useEffect, useState } from 'react';
import { procurementAPI, centreAPI } from '../services/api';

export default function Procurement() {
  const role = localStorage.getItem('role');
  const [data, setData] = useState({ items: [], page: 1, pages: 0 });
  const [centres, setCentres] = useState([]);
  const [filters, setFilters] = useState({ search: '', status: '', centre_id: role === 'CENTRE_OPERATOR' ? (localStorage.getItem('centre_id') || '') : '' });
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ accepted_quantity: '', rejected_quantity: '0', quality_grade: 'A', procurement_rate: '', remarks: '' });

  const load = async (page = 1) => {
    try {
      const response = await procurementAPI.list({ ...filters, centre_id: filters.centre_id || undefined, page, limit: 20 });
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load procurement records.');
    }
  };

  useEffect(() => {
    centreAPI.list().then((response) => setCentres(response.data)).catch(() => {});
    load();
  }, []);

  const start = async (bookingId) => {
    try { await procurementAPI.start(bookingId); await load(); }
    catch (err) { setError(err.response?.data?.detail || 'Unable to start procurement.'); }
  };

  const complete = async (event) => {
    event.preventDefault();
    setError('');
    const accepted = Number(form.accepted_quantity);
    const rejected = Number(form.rejected_quantity);
    const rate = Number(form.procurement_rate);
    if (![accepted, rejected, rate].every(Number.isFinite) || rate <= 0) {
      setError('Enter valid quantities and a rate greater than zero.');
      return;
    }
    if (accepted + rejected > Number(editing.quantity)) {
      setError('Accepted plus rejected quantity cannot exceed the booked quantity.');
      return;
    }
    try {
      await procurementAPI.complete(editing.booking_id, { ...form, accepted_quantity: accepted, rejected_quantity: rejected, procurement_rate: rate });
      setEditing(null);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to complete procurement. Start it first, then try again.');
    }
  };

  return <div>
    <h2>Procurement</h2>
    {error && <div className="card" style={{ padding: '.75rem', color: 'var(--danger-color)', marginBottom: '1rem' }}>{error}</div>}
    <div style={{ display: 'flex', gap: '.6rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
      <input placeholder="Booking or farmer" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
      <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><option value="">All statuses</option>{['PENDING', 'QUALITY_CHECK', 'WEIGHING', 'COMPLETED'].map((s) => <option key={s}>{s}</option>)}</select>
      {role !== 'CENTRE_OPERATOR' && <select value={filters.centre_id} onChange={(e) => setFilters({ ...filters, centre_id: e.target.value })}><option value="">All centres</option>{centres.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>}
      <button className="btn btn-secondary" onClick={() => load(1)}>Apply</button>
    </div>
    <div className="card" style={{ overflowX: 'auto' }}><table style={{ width: '100%' }}><thead><tr>{['Token', 'Booking', 'Farmer', 'Centre', 'Produce', 'Original', 'Accepted', 'Rejected', 'Grade', 'Rate', 'Total', 'Status', 'Action'].map((h) => <th key={h}>{h}</th>)}</tr></thead><tbody>{data.items.map((p) => <tr key={p.id}><td>{p.token}</td><td>{p.booking_id}</td><td>{p.farmer}</td><td>{p.centre}</td><td>{p.produce}</td><td>{p.quantity}</td><td>{p.accepted_quantity ?? '—'}</td><td>{p.rejected_quantity ?? 0}</td><td>{p.quality_grade}</td><td>₹{p.rate}</td><td>₹{p.total_amount ?? 0}</td><td>{p.status}</td><td>{p.status === 'PENDING' ? <button onClick={() => start(p.booking_id)}>Start</button> : p.status !== 'COMPLETED' && <button onClick={() => { setError(''); setEditing(p); }}>Complete</button>}</td></tr>)}</tbody></table></div>
    {editing && <div className="card" style={{ padding: '1rem', marginTop: '1rem' }}><h3>Complete {editing.booking_id}</h3><form onSubmit={complete} style={{ display: 'flex', gap: '.6rem', flexWrap: 'wrap' }}><input type="number" min="0" required placeholder="Accepted quantity" value={form.accepted_quantity} onChange={(e) => setForm({ ...form, accepted_quantity: e.target.value })} /><input type="number" min="0" required placeholder="Rejected quantity" value={form.rejected_quantity} onChange={(e) => setForm({ ...form, rejected_quantity: e.target.value })} /><input required placeholder="Grade" value={form.quality_grade} onChange={(e) => setForm({ ...form, quality_grade: e.target.value })} /><input type="number" min="0.01" required placeholder="Rate" value={form.procurement_rate} onChange={(e) => setForm({ ...form, procurement_rate: e.target.value })} /><input placeholder="Remarks" value={form.remarks} onChange={(e) => setForm({ ...form, remarks: e.target.value })} /><button className="btn btn-primary">Complete</button><button type="button" onClick={() => setEditing(null)}>Cancel</button></form></div>}
  </div>;
}
