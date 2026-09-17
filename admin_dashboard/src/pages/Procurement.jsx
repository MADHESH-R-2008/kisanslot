import { useState, useEffect } from 'react';
import { procurementAPI } from '../services/api';
import { RefreshCw, Package } from 'lucide-react';

const statusColors = {
  PENDING:       { bg: '#fef3c7', color: '#92400e' },
  QUALITY_CHECK: { bg: '#dbeafe', color: '#1e40af' },
  WEIGHING:      { bg: '#ede9fe', color: '#5b21b6' },
  COMPLETED:     { bg: '#d1fae5', color: '#065f46' },
};

const StatusBadge = ({ status }) => {
  const s = statusColors[status] || { bg: '#f3f4f6', color: '#374151' };
  return (
    <span style={{ backgroundColor: s.bg, color: s.color, padding: '0.2rem 0.65rem', borderRadius: '50px', fontSize: '0.75rem', fontWeight: 600 }}>
      {status?.replace('_', ' ')}
    </span>
  );
};

const CompleteModal = ({ booking, onClose, onSave }) => {
  const [form, setForm] = useState({ actual_quantity: '', grade: 'A', price_per_quintal: '', payment_amount: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(booking.booking_id, form);
  };

  return (
    <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
      <div className="card glass animate-fade-in" style={{ width: '100%', maxWidth: '480px', padding: '2rem' }}>
        <h3 style={{ marginTop: 0 }}>Complete Procurement — Token #{booking.token_number}</h3>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.4rem' }}>Actual Quantity (kg)</label>
            <input type="number" required min="0" step="0.01" value={form.actual_quantity} onChange={(e) => setForm({ ...form, actual_quantity: e.target.value })}
              style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)', outline: 'none' }} />
          </div>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.4rem' }}>Grade</label>
            <select value={form.grade} onChange={(e) => setForm({ ...form, grade: e.target.value })}
              style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)', outline: 'none' }}>
              {['A', 'B', 'C', 'Rejected'].map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.4rem' }}>Price per Quintal (₹)</label>
            <input type="number" required min="0" step="0.01" value={form.price_per_quintal} onChange={(e) => setForm({ ...form, price_per_quintal: e.target.value })}
              style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)', outline: 'none' }} />
          </div>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.4rem' }}>Payment Amount (₹)</label>
            <input type="number" required min="0" step="0.01" value={form.payment_amount} onChange={(e) => setForm({ ...form, payment_amount: e.target.value })}
              style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)', outline: 'none' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Confirm & Complete</button>
          </div>
        </form>
      </div>
    </div>
  );
};

const Procurement = () => {
  const centreId = parseInt(localStorage.getItem('centre_id') || '1', 10);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBooking, setSelectedBooking] = useState(null);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const res = await procurementAPI.list(centreId);
      setRecords(res.data);
    } catch (err) {
      console.error('Failed to load procurement records', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRecords(); }, []);

  const handleStart = async (bookingId) => {
    try {
      await procurementAPI.start(bookingId);
      fetchRecords();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start procurement');
    }
  };

  const handleComplete = async (bookingId, data) => {
    try {
      await procurementAPI.complete(bookingId, data);
      setSelectedBooking(null);
      fetchRecords();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to complete procurement');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Procurement</h2>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>Quality check, weighing, and payment completion</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchRecords} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading…</div>
        ) : records.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Package size={40} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
            <p>No procurement records found.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-color)' }}>
                  {['Booking ID', 'Farmer', 'Crop', 'Expected Qty', 'Actual Qty', 'Grade', 'Price/Q', 'Payment', 'Status', 'Actions'].map((h) => (
                    <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', fontWeight: 600, borderBottom: '1px solid var(--border-color)', whiteSpace: 'nowrap' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid var(--border-color)' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-color)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = ''}
                  >
                    <td style={{ padding: '0.8rem 1rem', fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{r.booking_id}</td>
                    <td style={{ padding: '0.8rem 1rem', fontWeight: 500 }}>{r.farmer?.name || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem' }}>{r.booking?.crop || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem', textAlign: 'right' }}>{r.booking?.expected_quantity?.toLocaleString() || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem', textAlign: 'right' }}>{r.actual_quantity?.toLocaleString() || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem' }}>{r.grade || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem', textAlign: 'right' }}>₹{r.price_per_quintal?.toLocaleString() || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem', textAlign: 'right' }}>₹{r.payment_amount?.toLocaleString() || '—'}</td>
                    <td style={{ padding: '0.8rem 1rem' }}><StatusBadge status={r.status} /></td>
                    <td style={{ padding: '0.8rem 1rem' }}>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        {r.status === 'PENDING' && (
                          <button className="btn btn-primary" onClick={() => handleStart(r.booking_id)}
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}>
                            Start
                          </button>
                        )}
                        {(r.status === 'QUALITY_CHECK' || r.status === 'WEIGHING') && (
                          <button className="btn" onClick={() => setSelectedBooking(r)}
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                            Complete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedBooking && (
        <CompleteModal
          booking={selectedBooking}
          onClose={() => setSelectedBooking(null)}
          onSave={handleComplete}
        />
      )}
    </div>
  );
};

export default Procurement;
