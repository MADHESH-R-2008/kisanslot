import { useState, useEffect } from 'react';
import { superAdminAPI } from '../services/masterApi';
import api from '../services/masterApi';
import {
  Plus, Edit2, CheckCircle, XCircle, RefreshCw, Shield, MapPin, Users
} from 'lucide-react';

const StatusBadge = ({ active }) => (
  <span style={{
    display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: 50, fontSize: '0.75rem', fontWeight: 600,
    backgroundColor: active ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
    color: active ? '#10b981' : '#ef4444',
  }}>
    {active ? 'Active' : 'Inactive'}
  </span>
);

// ── Create/Edit Master Modal ────────────────────────────────────────────────
const MasterFormModal = ({ master, districts, onClose, onSave }) => {
  const isEdit = !!master;
  const [form, setForm] = useState({
    full_name: master?.full_name || '',
    username: master?.username || '',
    mobile: master?.mobile || '',
    password: '',
    district_id: master?.district_id || '',
    is_active: master?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (isEdit) {
        const data = { full_name: form.full_name, mobile: form.mobile || null };
        if (form.district_id) data.district_id = Number(form.district_id);
        if (form.password) data.password = form.password;
        await superAdminAPI.updateMaster(master.id, data);
      } else {
        await superAdminAPI.createMaster({
          full_name: form.full_name,
          username: form.username,
          mobile: form.mobile || null,
          password: form.password,
          district_id: Number(form.district_id),
          is_active: form.is_active,
        });
      }
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save master');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem',
    }} onClick={onClose}>
      <div className="card" style={{ maxWidth: 480, width: '100%', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0 }}>{isEdit ? 'Edit Master' : 'Create Master'}</h2>
          <button className="btn btn-secondary" onClick={onClose} style={{ padding: '0.4rem 0.8rem' }}>✕</button>
        </div>

        {error && <div style={{ backgroundColor: 'var(--danger-color)', color: 'white', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
              Full Name <span style={{ color: 'var(--danger-color)' }}>*</span>
            </label>
            <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          </div>

          {!isEdit && (
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                Username <span style={{ color: 'var(--danger-color)' }}>*</span>
              </label>
              <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>Mobile</label>
            <input value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} placeholder="Optional" />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
              Password {!isEdit && <span style={{ color: 'var(--danger-color)' }}>*</span>}
              {isEdit && <span style={{ fontSize: '0.75rem' }}> (leave blank to keep current)</span>}
            </label>
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required={!isEdit} minLength={8} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
              District <span style={{ color: 'var(--danger-color)' }}>*</span>
            </label>
            <select value={form.district_id} onChange={(e) => setForm({ ...form, district_id: e.target.value })} required>
              <option value="">Select district</option>
              {districts.map((d) => <option key={d.id} value={d.id}>{d.name} ({d.code})</option>)}
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : isEdit ? 'Update Master' : 'Create Master'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────────────────
const Masters = () => {
  const [masters, setMasters] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [editMaster, setEditMaster] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await superAdminAPI.listMasters();
      setMasters(res.data);

      // Fetch districts from the master list data
      const districtMap = {};
      res.data.forEach((m) => {
        if (m.district_id && m.district) {
          districtMap[m.district_id] = { id: m.district_id, name: m.district, code: `DIST-${m.district_id}` };
        }
      });
      // Also fetch from centres API to get all districts
      try {
        const centresRes = await api.get('/centres/');
        const centreData = Array.isArray(centresRes.data) ? centresRes.data : [];
        centreData.forEach((c) => {
          if (c.district && !Object.values(districtMap).find(d => d.name === c.district)) {
            const id = Object.keys(districtMap).length + 1;
            districtMap[id] = { id, name: c.district, code: `DIST-${id}` };
          }
        });
      } catch { /* ignore */ }

      // Fallback districts
      if (Object.keys(districtMap).length === 0) {
        for (let i = 1; i <= 3; i++) {
          districtMap[i] = { id: i, name: `District ${i}`, code: `DIST-${i}` };
        }
      }
      setDistricts(Object.values(districtMap));
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load masters');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleToggleStatus = async (master) => {
    try {
      await superAdminAPI.setMasterStatus(master.id, !master.is_active);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem' }}>
            <Shield size={22} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '0.5rem', color: '#7c3aed' }} />
            Master Management
          </h2>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Create and manage district masters
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={fetchData} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Plus size={18} /> Create Master
          </button>
        </div>
      </div>

      {error && <p style={{ color: 'var(--danger-color)', marginBottom: '1rem' }}>{error}</p>}

      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: 'rgba(124,58,237,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#7c3aed' }}><Users size={20} /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Masters</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{masters.length}</div>
          </div>
        </div>
        <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: 'rgba(16,185,129,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}><CheckCircle size={20} /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Active</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{masters.filter(m => m.is_active).length}</div>
          </div>
        </div>
        <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: 'rgba(6,182,212,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0891b2' }}><MapPin size={20} /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Districts Covered</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{new Set(masters.map(m => m.district_id).filter(Boolean)).size}</div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%' }}>
          <thead>
            <tr>{['Name', 'Username', 'Mobile', 'District', 'Status', 'Created', 'Last Login', 'Actions'].map(h => <th key={h} style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Loading...</td></tr>
            ) : masters.length === 0 ? (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>No masters found</td></tr>
            ) : masters.map((m) => (
              <tr key={m.id}>
                <td style={{ fontWeight: 600 }}>{m.full_name || '—'}</td>
                <td><code style={{ fontSize: '0.8rem' }}>{m.username}</code></td>
                <td>{m.mobile || '—'}</td>
                <td>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <MapPin size={14} /> {m.district || '—'}
                  </span>
                </td>
                <td><StatusBadge active={m.is_active} /></td>
                <td style={{ fontSize: '0.85rem' }}>{m.created_at ? new Date(m.created_at).toLocaleDateString() : '—'}</td>
                <td style={{ fontSize: '0.85rem' }}>{m.last_login ? new Date(m.last_login).toLocaleString() : 'Never'}</td>
                <td>
                  <div style={{ display: 'flex', gap: '0.35rem' }}>
                    <button className="btn btn-secondary" onClick={() => setEditMaster(m)} title="Edit" style={{ padding: '0.3rem 0.5rem' }}>
                      <Edit2 size={14} />
                    </button>
                    <button
                      className={`btn ${m.is_active ? 'btn-secondary' : 'btn-primary'}`}
                      onClick={() => handleToggleStatus(m)}
                      title={m.is_active ? 'Deactivate' : 'Activate'}
                      style={{ padding: '0.3rem 0.5rem' }}
                    >
                      {m.is_active ? <XCircle size={14} /> : <CheckCircle size={14} />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {(showCreate || editMaster) && (
        <MasterFormModal
          master={editMaster}
          districts={districts}
          onClose={() => { setShowCreate(false); setEditMaster(null); }}
          onSave={() => { setShowCreate(false); setEditMaster(null); fetchData(); }}
        />
      )}
    </div>
  );
};

export default Masters;
