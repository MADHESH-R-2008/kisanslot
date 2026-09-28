import { useState, useEffect, useCallback } from 'react';
import { masterAPI } from '../services/masterApi';
import {
  Plus, Edit2, CheckCircle, XCircle, Search, RefreshCw, Users, Building2, Key
} from 'lucide-react';

// ── Status Badge ────────────────────────────────────────────────────────────
const StatusBadge = ({ active }) => (
  <span style={{
    display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: 50, fontSize: '0.75rem', fontWeight: 600,
    backgroundColor: active ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
    color: active ? '#10b981' : '#ef4444',
  }}>
    {active ? 'Active' : 'Inactive'}
  </span>
);

// ── Create/Edit Operator Modal ──────────────────────────────────────────────
const OperatorFormModal = ({ operator, centres, onClose, onSave }) => {
  const isEdit = !!operator;
  const [form, setForm] = useState({
    full_name: operator?.full_name || '',
    username: operator?.username || '',
    mobile: operator?.mobile || '',
    password: '',
    centre_id: operator?.centre_id || (centres.length > 0 ? centres[0].id : ''),
    is_active: operator?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (isEdit) {
        const data = { full_name: form.full_name, username: form.username, mobile: form.mobile || null };
        if (form.password) data.password = form.password;
        await masterAPI.updateOperator(operator.id, data);
      } else {
        await masterAPI.createOperator({
          full_name: form.full_name,
          username: form.username,
          mobile: form.mobile || null,
          password: form.password,
          centre_id: Number(form.centre_id),
          is_active: form.is_active,
        });
      }
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save operator');
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
          <h2 style={{ margin: 0 }}>{isEdit ? 'Edit Operator' : 'Create Operator'}</h2>
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

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
              Username <span style={{ color: 'var(--danger-color)' }}>*</span>
            </label>
            <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
              Mobile
            </label>
            <input value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} placeholder="Optional" />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
              Password {!isEdit && <span style={{ color: 'var(--danger-color)' }}>*</span>}
              {isEdit && <span style={{ fontSize: '0.75rem' }}> (leave blank to keep current)</span>}
            </label>
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required={!isEdit} minLength={8} />
          </div>

          {!isEdit && (
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, marginBottom: '0.35rem', color: 'var(--text-secondary)' }}>
                Assign Centre <span style={{ color: 'var(--danger-color)' }}>*</span>
              </label>
              <select value={form.centre_id} onChange={(e) => setForm({ ...form, centre_id: e.target.value })} required>
                <option value="">Select centre</option>
                {centres.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
              </select>
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : isEdit ? 'Update' : 'Create Operator'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ── Change Centre Modal ─────────────────────────────────────────────────────
const ChangeCentreModal = ({ operator, centres, onClose, onSave }) => {
  const [centreId, setCentreId] = useState(operator.centre_id || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await masterAPI.assignOperatorCentre(operator.id, Number(centreId));
      onSave();
    } catch (err) {
      setError(err.response?.data?.detail || 'Cannot assign to that centre');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem',
    }} onClick={onClose}>
      <div className="card" style={{ maxWidth: 400, width: '100%', padding: '2rem' }} onClick={(e) => e.stopPropagation()}>
        <h2 style={{ margin: '0 0 1rem' }}>Change Centre Assignment</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0 0 1rem' }}>
          Reassign <strong>{operator.full_name || operator.username}</strong> to a different centre within your district.
        </p>
        {error && <div style={{ backgroundColor: 'var(--danger-color)', color: 'white', padding: '0.75rem', borderRadius: 6, marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</div>}
        <form onSubmit={handleSubmit}>
          <select value={centreId} onChange={(e) => setCentreId(e.target.value)} required style={{ width: '100%', marginBottom: '1rem' }}>
            <option value="">Select centre</option>
            {centres.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
          </select>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Assign'}</button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────────────────
const MasterOperators = () => {
  const [operators, setOperators] = useState([]);
  const [centres, setCentres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [editOperator, setEditOperator] = useState(null);
  const [changeCentreOp, setChangeCentreOp] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const centresRes = await masterAPI.listCentres({ limit: 100 });
      const allCentres = centresRes.data.items || [];
      setCentres(allCentres);

      const allOps = [];
      for (const centre of allCentres) {
        try {
          const opsRes = await masterAPI.getCentreOperators(centre.id);
          allOps.push(...(opsRes.data || []).map((op) => ({ ...op, centre_name: centre.name })));
        } catch { /* skip */ }
      }
      setOperators(allOps);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load operators');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleToggleStatus = async (op) => {
    try {
      await masterAPI.setOperatorStatus(op.id, !op.is_active);
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
          <h2 style={{ margin: 0, fontSize: '1.3rem' }}>Operator Management</h2>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Manage centre operators in your district
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={fetchData} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Plus size={18} /> Create Operator
          </button>
        </div>
      </div>

      {error && <p style={{ color: 'var(--danger-color)', marginBottom: '1rem' }}>{error}</p>}

      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: 'rgba(59,130,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#3b82f6' }}><Users size={20} /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total Operators</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{operators.length}</div>
          </div>
        </div>
        <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: 'rgba(16,185,129,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}><CheckCircle size={20} /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Active</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{operators.filter(o => o.is_active).length}</div>
          </div>
        </div>
        <div className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: 'rgba(139,92,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b5cf6' }}><Building2 size={20} /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Centres</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{centres.length}</div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%' }}>
          <thead>
            <tr>{['Name', 'Username', 'Mobile', 'Centre', 'Status', 'Created', 'Last Login', 'Actions'].map(h => <th key={h} style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Loading...</td></tr>
            ) : operators.length === 0 ? (
              <tr><td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>No operators found</td></tr>
            ) : operators.map((op) => (
              <tr key={op.id}>
                <td style={{ fontWeight: 600 }}>{op.full_name || op.username}</td>
                <td><code style={{ fontSize: '0.8rem' }}>{op.username}</code></td>
                <td>{op.mobile || '—'}</td>
                <td>{op.centre_name || op.centre || '—'}</td>
                <td><StatusBadge active={op.is_active} /></td>
                <td style={{ fontSize: '0.85rem' }}>{op.created_at ? new Date(op.created_at).toLocaleDateString() : '—'}</td>
                <td style={{ fontSize: '0.85rem' }}>{op.last_login ? new Date(op.last_login).toLocaleString() : 'Never'}</td>
                <td>
                  <div style={{ display: 'flex', gap: '0.35rem' }}>
                    <button className="btn btn-secondary" onClick={() => setEditOperator(op)} title="Edit" style={{ padding: '0.3rem 0.5rem' }}>
                      <Edit2 size={14} />
                    </button>
                    <button className="btn btn-secondary" onClick={() => setChangeCentreOp(op)} title="Change Centre" style={{ padding: '0.3rem 0.5rem' }}>
                      <Building2 size={14} />
                    </button>
                    <button
                      className={`btn ${op.is_active ? 'btn-secondary' : 'btn-primary'}`}
                      onClick={() => handleToggleStatus(op)}
                      title={op.is_active ? 'Deactivate' : 'Activate'}
                      style={{ padding: '0.3rem 0.5rem' }}
                    >
                      {op.is_active ? <XCircle size={14} /> : <CheckCircle size={14} />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {(showCreate || editOperator) && (
        <OperatorFormModal
          operator={editOperator}
          centres={centres}
          onClose={() => { setShowCreate(false); setEditOperator(null); }}
          onSave={() => { setShowCreate(false); setEditOperator(null); fetchData(); }}
        />
      )}
      {changeCentreOp && (
        <ChangeCentreModal
          operator={changeCentreOp}
          centres={centres}
          onClose={() => setChangeCentreOp(null)}
          onSave={() => { setChangeCentreOp(null); fetchData(); }}
        />
      )}
    </div>
  );
};

export default MasterOperators;
