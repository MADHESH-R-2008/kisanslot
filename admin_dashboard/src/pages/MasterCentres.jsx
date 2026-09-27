import { useState, useEffect } from 'react';
import { masterAPI } from '../services/masterApi';
import { Plus, Edit2, Eye, CheckCircle, XCircle, Search, RefreshCw, ChevronLeft, ChevronRight, Users, CalendarDays, Activity, MapPin } from 'lucide-react';

// ── Centre Detail Modal ─────────────────────────────────────────────────────
const CentreDetailModal = ({ centre, onClose }) => {
  const [detail, setDetail] = useState(null);
  const [operators, setOperators] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [d, ops] = await Promise.all([
          masterAPI.getCentre(centre.id),
          masterAPI.getCentreOperators(centre.id),
        ]);
        setDetail(d.data);
        setOperators(ops.data);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    load();
  }, [centre.id]);

  return (
    <div style={{
      position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem',
    }} onClick={onClose}>
      <div className="card" style={{ maxWidth: 640, width: '100%', maxHeight: '85vh', overflow: 'auto', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>Centre Details</h2>
          <button className="btn btn-secondary" onClick={onClose} style={{ padding: '0.4rem 0.8rem' }}>✕</button>
        </div>

        {loading ? <p style={{ color: 'var(--text-secondary)' }}>Loading...</p> : detail && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <InfoRow label="Centre Name" value={detail.name} />
              <InfoRow label="Centre Code" value={detail.code} />
              <InfoRow label="District" value={detail.district} />
              <InfoRow label="Address" value={detail.address} />
              <InfoRow label="Contact" value={detail.contact_number || '—'} />
              <InfoRow label="Status" value={detail.is_active ? '✅ Active' : '❌ Inactive'} />
              <InfoRow label="Total Counters" value={detail.total_counters} />
              <InfoRow label="Active Counters" value={detail.active_counters} />
              <InfoRow label="Today's Bookings" value={detail.today_bookings} />
              <InfoRow label="Current Queue" value={detail.queue} />
              <InfoRow label="Available Slots" value={detail.available_slots} />
              <InfoRow label="Pending Procurement" value={detail.pending_procurement} />
              <InfoRow label="Pending Payments" value={detail.pending_payments} />
              <InfoRow label="Operators" value={detail.operators} />
            </div>

            {operators.length > 0 && (
              <div>
                <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Assigned Operators</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', fontSize: '0.85rem' }}>
                    <thead><tr>{['Name', 'Username', 'Status', 'Last Login'].map(h => <th key={h} style={{ textAlign: 'left', padding: '0.5rem' }}>{h}</th>)}</tr></thead>
                    <tbody>
                      {operators.map((op) => (
                        <tr key={op.id}>
                          <td style={{ padding: '0.5rem' }}>{op.full_name || op.username}</td>
                          <td style={{ padding: '0.5rem' }}>{op.username}</td>
                          <td style={{ padding: '0.5rem' }}><StatusBadge active={op.is_active} /></td>
                          <td style={{ padding: '0.5rem' }}>{op.last_login ? new Date(op.last_login).toLocaleString() : 'Never'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Create/Edit Centre Modal ────────────────────────────────────────────────
const CentreFormModal = ({ centre, onClose, onSave }) => {
  const isEdit = !!centre;
  const [form, setForm] = useState({
    name: centre?.name || '',
    code: centre?.code || '',
    address: centre?.address || '',
    contact_number: centre?.contact_number || '',
    latitude: centre?.latitude || 0,
    longitude: centre?.longitude || 0,
    total_counters: centre?.total_counters || 3,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (isEdit) {
        await masterAPI.updateCentre(centre.id, form);
      } else {
        await masterAPI.createCentre(form);
      }
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save centre');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem',
    }} onClick={onClose}>
      <div className="card" style={{ maxWidth: 520, width: '100%', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>{isEdit ? 'Edit Centre' : 'Create Centre'}</h2>
          <button className="btn btn-secondary" onClick={onClose} style={{ padding: '0.4rem 0.8rem' }}>✕</button>
        </div>

        {error && <div style={{ backgroundColor: 'var(--danger-color)', color: 'white', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <FormField label="Centre Name" required>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </FormField>
          <FormField label="Centre Code" required>
            <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required disabled={isEdit} style={isEdit ? { opacity: 0.6 } : {}} />
          </FormField>
          <FormField label="Address" required>
            <textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required rows={2} />
          </FormField>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <FormField label="Contact Number">
              <input value={form.contact_number} onChange={(e) => setForm({ ...form, contact_number: e.target.value })} />
            </FormField>
            <FormField label="Total Counters">
              <input type="number" min={1} value={form.total_counters} onChange={(e) => setForm({ ...form, total_counters: parseInt(e.target.value) || 1 })} />
            </FormField>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <FormField label="Latitude">
              <input type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) || 0 })} />
            </FormField>
            <FormField label="Longitude">
              <input type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) || 0 })} />
            </FormField>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, padding: '0.5rem', background: 'var(--bg-subtle)', borderRadius: 6 }}>
            <MapPin size={14} style={{ display: 'inline', verticalAlign: 'text-bottom' }} /> District is automatically set from your assignment. You cannot change it.
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : isEdit ? 'Update Centre' : 'Create Centre'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ── Helpers ──────────────────────────────────────────────────────────────────
const InfoRow = ({ label, value }) => (
  <div>
    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>{label}</div>
    <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)', marginTop: '0.15rem' }}>{value ?? '—'}</div>
  </div>
);

const FormField = ({ label, required, children }) => (
  <div>
    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
      {label} {required && <span style={{ color: 'var(--danger-color)' }}>*</span>}
    </label>
    {children}
  </div>
);

const StatusBadge = ({ active }) => (
  <span style={{
    display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: 50, fontSize: '0.75rem', fontWeight: 600,
    backgroundColor: active ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
    color: active ? '#10b981' : '#ef4444',
  }}>
    {active ? 'Active' : 'Inactive'}
  </span>
);

// ── Main Component ───────────────────────────────────────────────────────────
const MasterCentres = () => {
  const [centres, setCentres] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCentre, setSelectedCentre] = useState(null);
  const [editCentre, setEditCentre] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const limit = 20;

  const fetchCentres = async () => {
    setLoading(true);
    try {
      const params = { page, limit };
      if (search.trim()) params.search = search.trim();
      if (statusFilter !== '') params.is_active = statusFilter === 'active';
      const res = await masterAPI.listCentres(params);
      setCentres(res.data.items);
      setTotal(res.data.total);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load centres');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchCentres(); }, [page, statusFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchCentres();
  };

  const handleToggleStatus = async (centre) => {
    try {
      await masterAPI.setCentreStatus(centre.id, !centre.is_active);
      fetchCentres();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem' }}>Centre Management</h2>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Manage procurement centres in your district
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Plus size={18} /> Create Centre
        </button>
      </div>

      {/* Filters */}
      <div className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
            <Search size={16} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            <input
              placeholder="Search by name or code..."
              value={search} onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 34, width: '100%' }}
            />
          </div>
          <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} style={{ minWidth: 140 }}>
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <button type="submit" className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <RefreshCw size={15} /> Search
          </button>
        </form>
      </div>

      {error && <p style={{ color: 'var(--danger-color)', marginBottom: '1rem' }}>{error}</p>}

      {/* Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%' }}>
          <thead>
            <tr>
              {['Centre Name', 'Code', 'District', 'Status', 'Counters', 'Bookings', 'Queue', 'Operators', 'Actions'].map(h => (
                <th key={h} style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Loading...</td></tr>
            ) : centres.length === 0 ? (
              <tr><td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>No centres found</td></tr>
            ) : centres.map((c) => (
              <tr key={c.id}>
                <td style={{ fontWeight: 600 }}>{c.name}</td>
                <td><code style={{ fontSize: '0.8rem' }}>{c.code}</code></td>
                <td>{c.district}</td>
                <td><StatusBadge active={c.is_active} /></td>
                <td>{c.active_counters}/{c.total_counters}</td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <CalendarDays size={14} /> {c.today_bookings}
                  </span>
                </td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Activity size={14} /> {c.queue}
                  </span>
                </td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Users size={14} /> {c.operators}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button className="btn btn-secondary" onClick={() => setSelectedCentre(c)} title="View Details" style={{ padding: '0.3rem 0.5rem' }}>
                      <Eye size={15} />
                    </button>
                    <button className="btn btn-secondary" onClick={() => setEditCentre(c)} title="Edit" style={{ padding: '0.3rem 0.5rem' }}>
                      <Edit2 size={15} />
                    </button>
                    <button
                      className={`btn ${c.is_active ? 'btn-secondary' : 'btn-primary'}`}
                      onClick={() => handleToggleStatus(c)}
                      title={c.is_active ? 'Deactivate' : 'Activate'}
                      style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                    >
                      {c.is_active ? <XCircle size={15} /> : <CheckCircle size={15} />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
          <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <ChevronLeft size={16} /> Prev
          </button>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Page {page} of {totalPages} ({total} total)</span>
          <button className="btn btn-secondary" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            Next <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Modals */}
      {selectedCentre && <CentreDetailModal centre={selectedCentre} onClose={() => setSelectedCentre(null)} />}
      {(showCreate || editCentre) && (
        <CentreFormModal
          centre={editCentre}
          onClose={() => { setShowCreate(false); setEditCentre(null); }}
          onSave={() => { setShowCreate(false); setEditCentre(null); fetchCentres(); }}
        />
      )}
    </div>
  );
};

export default MasterCentres;
