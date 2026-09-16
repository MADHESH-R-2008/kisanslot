import { useState, useEffect } from 'react';
import { centreAPI } from '../services/api';
import { Plus, Edit2, Trash2, MapPin, RefreshCw } from 'lucide-react';

const CentreModal = ({ centre, onClose, onSave }) => {
  const [form, setForm] = useState(
    centre || {
      name: '', code: '', address: '', district: '', state: '',
      total_counters: 4, active_counters: 4,
      contact_number: '', is_active: true, is_paused: false,
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (form.active_counters > form.total_counters) {
      window.alert('Active counters cannot be greater than total counters.');
      return;
    }
    onSave(form);
  };

  const field = (label, key, type = 'text', opts = {}) => (
    <div key={key}>
      <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>{label}</label>
      {type === 'checkbox' ? (
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={!!form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.checked })} style={{ width: 16, height: 16 }} />
          <span style={{ fontSize: '0.875rem' }}>{opts.checkLabel}</span>
        </label>
      ) : (
        <input
          type={type}
          value={form[key] ?? ''}
          onChange={(e) => setForm({ ...form, [key]: type === 'number' ? Number(e.target.value) : e.target.value })}
          required={opts.required}
          min={opts.min}
          style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)', outline: 'none', fontSize: '0.875rem' }}
        />
      )}
    </div>
  );

  return (
    <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem' }}>
      <div className="card glass animate-fade-in" style={{ width: '100%', maxWidth: '560px', padding: '2rem', maxHeight: '90vh', overflowY: 'auto' }}>
        <h3 style={{ marginTop: 0 }}>{centre ? 'Edit Centre' : 'Create New Centre'}</h3>
        <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div style={{ gridColumn: '1 / -1' }}>{field('Centre Name *', 'name', 'text', { required: true })}</div>
          {field('Centre Code *', 'code', 'text', { required: true })}
          {field('Contact Number', 'contact_number')}
          <div style={{ gridColumn: '1 / -1' }}>{field('Address *', 'address', 'text', { required: true })}</div>
          {field('District *', 'district', 'text', { required: true })}
          {field('State *', 'state', 'text', { required: true })}
          {field('Total Counters', 'total_counters', 'number', { min: 1 })}
          {field('Active Counters', 'active_counters', 'number', { min: 0 })}
          {field('Is Active', 'is_active', 'checkbox', { checkLabel: 'Centre is active' })}
          {field('Is Paused', 'is_paused', 'checkbox', { checkLabel: 'Queue is paused' })}
          <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>{centre ? 'Save Changes' : 'Create Centre'}</button>
          </div>
        </form>
      </div>
    </div>
  );
};

const Centres = () => {
  const [centres, setCentres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // null | 'create' | centre object
  const role = localStorage.getItem('role');
  const assignedCentreId = Number(localStorage.getItem('centre_id'));
  const canCreateCentres = role === 'ADMIN' || role === 'SUPER_ADMIN';
  const isSuperAdmin = role === 'SUPER_ADMIN';

  const fetchCentres = async () => {
    setLoading(true);
    try {
      const res = await centreAPI.list();
      setCentres(res.data);
    } catch (err) {
      console.error('Failed to load centres', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchCentres(); }, []);

  const handleSave = async (form) => {
    try {
      if (modal && modal.id) {
        await centreAPI.update(modal.id, form);
      } else {
        await centreAPI.create(form);
      }
      setModal(null);
      fetchCentres();
    } catch (err) {
      const detail = err.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => `${item.loc?.slice(-1)[0] || 'Field'}: ${item.msg}`).join('\n')
        : detail;
      alert(message || (err.response?.status === 403
        ? 'You need an Admin or Super Admin account to create a centre.'
        : 'Failed to save centre. Check your connection and try again.'));
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this centre? This cannot be undone.')) return;
    try {
      await centreAPI.remove(id);
      fetchCentres();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete centre');
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Centres</h2>
          <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0' }}>Manage procurement centres</p>
          {!canCreateCentres && (
            <p style={{ color: 'var(--text-secondary)', margin: '0.5rem 0 0', fontSize: '0.82rem' }}>
              Centre operators can update only their assigned centre. Sign in as an Admin or Super Admin to create a centre.
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={fetchCentres} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <RefreshCw size={16} /> Refresh
          </button>
          {canCreateCentres && (
            <button className="btn btn-primary" onClick={() => setModal('create')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Plus size={16} /> Add Centre
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading centres…</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
          {centres.map((c) => (
            <div key={c.id} className="card" style={{ padding: '1.5rem', position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>{c.name}</span>
                    <span style={{
                      padding: '0.1rem 0.5rem', borderRadius: '50px', fontSize: '0.7rem', fontWeight: 600,
                      backgroundColor: c.is_active ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                      color: c.is_active ? '#065f46' : '#991b1b',
                    }}>
                      {c.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {c.is_paused && (
                      <span style={{ padding: '0.1rem 0.5rem', borderRadius: '50px', fontSize: '0.7rem', fontWeight: 600, backgroundColor: '#fef3c7', color: '#92400e' }}>
                        Paused
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Code: {c.code}</div>
                </div>
                <div style={{ display: 'flex', gap: '0.35rem' }}>
                  {(role !== 'CENTRE_OPERATOR' || c.id === assignedCentreId) && (
                    <button onClick={() => setModal(c)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '0.25rem' }} title="Edit">
                      <Edit2 size={16} />
                    </button>
                  )}
                  {isSuperAdmin && (
                    <button onClick={() => handleDelete(c.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger-color)', padding: '0.25rem' }} title="Delete">
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>

              {c.address && (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  <MapPin size={14} style={{ flexShrink: 0, marginTop: 2 }} />
                  <span>{[c.address, c.district, c.state].filter(Boolean).join(', ')}</span>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' }}>
                {[
                  { label: 'Total Counters', value: c.total_counters },
                  { label: 'Active Counters', value: c.active_counters },
                  { label: 'Contact', value: c.contact_number || '—' },
                  { label: 'Rating', value: c.rating ? `${c.rating} ⭐` : '—' },
                ].map(({ label, value }) => (
                  <div key={label} style={{ backgroundColor: 'var(--bg-color)', borderRadius: 8, padding: '0.5rem 0.75rem' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{value}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          {centres.length === 0 && (
            <div style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No centres found. Click "Add Centre" to create one.
            </div>
          )}
        </div>
      )}

      {modal !== null && (
        <CentreModal
          centre={modal === 'create' ? null : modal}
          onClose={() => setModal(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default Centres;
