import { useState, useEffect } from 'react';
import { centreAPI } from '../services/api';
import { Plus, Edit2, Trash2, MapPin, RefreshCw, ExternalLink } from 'lucide-react';

const CentreModal = ({ centre, onClose, onSave }) => {
  const [form, setForm] = useState(
    centre || {
      name: '', code: '', address: '', district: '', state: '',
      total_counters: 4, active_counters: 4,
      contact_number: '', google_map_url: '', is_active: true, is_paused: false,
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
          placeholder={opts.placeholder}
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
          {field('Centre ID *', 'code', 'text', { required: true })}
          {!centre && field('Centre Operator Password *', 'operator_password', 'password', { required: true })}
          {field('Contact Number', 'contact_number')}
          <div style={{ gridColumn: '1 / -1' }}>{field('Address *', 'address', 'text', { required: true })}</div>
          <div style={{ gridColumn: '1 / -1' }}>{field('Google Map URL / Link (Optional)', 'google_map_url', 'text', { placeholder: 'https://maps.google.com/?q=...' })}</div>
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
      console.error('Save centre error:', err);
      const msg = err.response?.data?.detail || 'Failed to save centre. Check your connection and try again.';
      window.alert(msg);
    }
  };

  const handleDelete = async (centre) => {
    if (!window.confirm(`Are you sure you want to delete "${centre.name}"? This will delete all its slots, counters, and bookings.`)) return;
    try {
      await centreAPI.remove(centre.id);
      fetchCentres();
    } catch (err) {
      console.error('Delete centre error:', err);
      const msg = err.response?.data?.detail || 'Failed to delete centre.';
      window.alert(msg);
    }
  };

  const visibleCentres = isSuperAdmin || role === 'ADMIN'
    ? centres
    : centres.filter(c => c.id === assignedCentreId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Procurement Centres</h2>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Manage procurement centres, location links, and counter capacities
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={fetchCentres} title="Refresh"><RefreshCw size={16} /></button>
          {canCreateCentres && (
            <button className="btn btn-primary" onClick={() => setModal('create')} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Plus size={16} /> Add Centre
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading centres...</div>
      ) : visibleCentres.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          No centres found. Click "Add Centre" to create one.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {visibleCentres.map((c) => (
            <div key={c.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', border: c.is_paused ? '1px solid var(--warning-color, #f59e0b)' : undefined }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.05rem' }}>{c.name}</h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>ID: {c.code}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.35rem' }}>
                    <span className={`badge ${c.is_active ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.7rem' }}>
                      {c.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {c.is_paused && <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>Paused</span>}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  <MapPin size={15} style={{ flexShrink: 0, marginTop: 2, color: 'var(--primary-color)' }} />
                  <div>
                    {c.address}, {c.district}, {c.state}
                    {c.google_map_url && (
                      <div style={{ marginTop: '0.25rem' }}>
                        <a href={c.google_map_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary-color)', fontSize: '0.75rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '2px', textDecoration: 'underline' }}>
                          Open in Google Maps <ExternalLink size={12} />
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', backgroundColor: 'var(--bg-subtle, #f8fafc)', padding: '0.65rem 0.85rem', borderRadius: 8, fontSize: '0.8rem', marginBottom: '1rem' }}>
                  <div>Counters: <strong>{c.active_counters}/{c.total_counters}</strong></div>
                  <div>Live Queue: <strong>{c.queue_count ?? 0}</strong></div>
                  <div>Est. Wait: <strong>{c.estimated_wait_minutes ?? 0}m</strong></div>
                  <div>Rating: <strong>⭐ {c.rating ?? 4.5}</strong></div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
                <button className="btn btn-secondary" onClick={() => setModal(c)} style={{ flex: 1, padding: '0.4rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.35rem' }}>
                  <Edit2 size={14} /> Edit
                </button>
                {canCreateCentres && (
                  <button className="btn btn-danger" onClick={() => handleDelete(c)} style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && <CentreModal centre={modal === 'create' ? null : modal} onClose={() => setModal(null)} onSave={handleSave} />}
    </div>
  );
};

export default Centres;
