import { useState, useEffect, useCallback } from 'react';
import { queueAPI, counterAPI } from '../services/api';
import { useQueueSocket } from '../hooks/useQueueSocket';
import { Megaphone, Play, CheckCircle, XCircle, Pause, PlayCircle, Wifi, WifiOff, SkipForward, Monitor, Clock, BarChart3, Users, Zap, AlertTriangle } from 'lucide-react';

const centreId = parseInt(localStorage.getItem('centre_id') || '1', 10);

const statusColors = {
  WAITING:    { bg: '#fef3c7', color: '#92400e', label: 'Waiting' },
  CONFIRMED:  { bg: '#fef3c7', color: '#92400e', label: 'Confirmed' },
  ARRIVED:    { bg: '#dbeafe', color: '#1e40af', label: 'Arrived' },
  VERIFIED:   { bg: '#dbeafe', color: '#1e40af', label: 'Verified' },
  CALLED:     { bg: '#ede9fe', color: '#5b21b6', label: 'Called' },
  SERVING:    { bg: '#d1fae5', color: '#065f46', label: 'Serving' },
  PROCESSING: { bg: '#d1fae5', color: '#065f46', label: 'Processing' },
  COMPLETED:  { bg: '#f0fdf4', color: '#15803d', label: 'Completed' },
  NO_SHOW:    { bg: '#fee2e2', color: '#991b1b', label: 'No Show' },
  SKIPPED:    { bg: '#fff7ed', color: '#c2410c', label: 'Skipped' },
  CANCELLED:  { bg: '#fee2e2', color: '#991b1b', label: 'Cancelled' },
};

const StatusBadge = ({ status }) => {
  const s = statusColors[status] || { bg: '#f3f4f6', color: '#374151', label: status };
  return (
    <span style={{
      backgroundColor: s.bg,
      color: s.color,
      padding: '0.2rem 0.65rem',
      borderRadius: '50px',
      fontSize: '0.75rem',
      fontWeight: 600,
      whiteSpace: 'nowrap',
    }}>
      {s.label}
    </span>
  );
};

const counterStatusColors = {
  ACTIVE: { bg: '#d1fae5', color: '#065f46', label: 'Active' },
  BUSY: { bg: '#ede9fe', color: '#5b21b6', label: 'Busy' },
  INACTIVE: { bg: '#f3f4f6', color: '#6b7280', label: 'Inactive' },
  MAINTENANCE: { bg: '#fef3c7', color: '#92400e', label: 'Maintenance' },
};

const Queue = () => {
  const [queueData, setQueueData] = useState({
    queue: [], waiting_count: 0, processing_count: 0,
    serving_count: 0, completed_count: 0, skipped_count: 0,
    cancelled_count: 0, active_counters: 0, is_paused: false,
  });
  const [stats, setStats] = useState(null);
  const [counters, setCounters] = useState([]);
  const [showCounters, setShowCounters] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [skipConfirm, setSkipConfirm] = useState(null);

  const fetchQueue = useCallback(async () => {
    try {
      const res = await queueAPI.getCentreStatus(centreId);
      setQueueData(res.data);
    } catch (err) {
      console.error('Failed to fetch queue', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await queueAPI.getQueueStats(centreId);
      setStats(res.data);
    } catch (err) {
      console.error('Failed to fetch stats', err);
    }
  }, []);

  const fetchCounters = useCallback(async () => {
    try {
      const res = await counterAPI.listByCentre(centreId);
      setCounters(res.data);
    } catch (err) {
      console.error('Failed to fetch counters', err);
    }
  }, []);

  // WebSocket for real-time updates
  const onWsMessage = useCallback((data) => {
    if (['QUEUE_UPDATED', 'FARMER_CALLED', 'SERVING_STARTED', 'COMPLETED', 'SKIPPED', 'BOOKING_CREATED', 'ACK'].includes(data.event)) {
      fetchQueue();
      if (showStats) fetchStats();
      if (showCounters) fetchCounters();
      setWsConnected(true);
    }
  }, [fetchQueue, fetchStats, fetchCounters, showStats, showCounters]);

  useQueueSocket(centreId, onWsMessage);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 10000);
    return () => clearInterval(interval);
  }, [fetchQueue]);

  useEffect(() => {
    if (showStats) fetchStats();
  }, [showStats, fetchStats]);

  useEffect(() => {
    if (showCounters) fetchCounters();
  }, [showCounters, fetchCounters]);

  const handleAction = async (action, bookingId = null) => {
    const key = bookingId ? `${action}-${bookingId}` : action;
    setActionLoading(key);
    try {
      switch (action) {
        case 'callNext': await queueAPI.callNext(centreId); break;
        case 'pause': await queueAPI.pauseQueue(); break;
        case 'resume': await queueAPI.resumeQueue(); break;
        case 'start': await queueAPI.startProcessing(bookingId); break;
        case 'complete': await queueAPI.completeProcessing(bookingId); break;
        case 'noShow': await queueAPI.markNoShow(bookingId); break;
        case 'skip': await queueAPI.skipFarmer(bookingId); setSkipConfirm(null); break;
        default: break;
      }
      await fetchQueue();
      if (showStats) await fetchStats();
      if (showCounters) await fetchCounters();
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleCounter = async (counterId) => {
    try {
      await counterAPI.toggle(counterId);
      await fetchCounters();
      await fetchQueue();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to toggle counter');
    }
  };

  const statCards = [
    { label: 'Waiting', value: queueData.waiting_count, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', icon: <Users size={16} /> },
    { label: 'Called/Serving', value: queueData.processing_count + (queueData.serving_count || 0), color: '#3b82f6', bg: 'rgba(59,130,246,0.1)', icon: <Zap size={16} /> },
    { label: 'Completed', value: queueData.completed_count, color: '#10b981', bg: 'rgba(16,185,129,0.1)', icon: <CheckCircle size={16} /> },
    { label: 'Skipped', value: queueData.skipped_count || 0, color: '#f97316', bg: 'rgba(249,115,22,0.1)', icon: <SkipForward size={16} /> },
    { label: 'Counters', value: queueData.active_counters, color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)', icon: <Monitor size={16} /> },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <h2 style={{ margin: 0 }}>Queue Management</h2>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: wsConnected ? '#10b981' : '#9ca3af' }}>
              {wsConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
              {wsConnected ? 'Live' : 'Polling'}
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            {queueData.is_paused
              ? '⚠️ Queue is currently PAUSED'
              : 'Live procurement queue — Centre ' + centreId}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary"
            onClick={() => setShowStats(v => !v)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <BarChart3 size={16} />
            {showStats ? 'Hide Stats' : 'Stats'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setShowCounters(v => !v)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Monitor size={16} />
            {showCounters ? 'Hide Counters' : 'Counters'}
          </button>
          <button
            className={`btn ${queueData.is_paused ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => handleAction(queueData.is_paused ? 'resume' : 'pause')}
            disabled={actionLoading === 'pause' || actionLoading === 'resume'}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            {queueData.is_paused ? <PlayCircle size={16} /> : <Pause size={16} />}
            {queueData.is_paused ? 'Resume Queue' : 'Pause Queue'}
          </button>
          <button
            className="btn btn-primary"
            onClick={() => handleAction('callNext')}
            disabled={!!actionLoading || queueData.is_paused}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', borderRadius: '50px', padding: '0.6rem 1.25rem' }}
          >
            <Megaphone size={18} />
            {actionLoading === 'callNext' ? 'Calling…' : 'Call Next Farmer'}
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {statCards.map((s) => (
          <div key={s.label} className="card" style={{ padding: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '1.3rem', fontWeight: 700, color: s.color }}>{s.value}</span>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>{s.icon} {s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Today's Statistics Panel */}
      {showStats && stats && (
        <div className="card animate-fade-in" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><BarChart3 size={18} /> Today&apos;s Statistics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1rem' }}>
            {[
              { label: 'Total Bookings', value: stats.total_bookings, color: '#6366f1' },
              { label: 'Waiting', value: stats.waiting, color: '#f59e0b' },
              { label: 'Serving', value: stats.serving, color: '#3b82f6' },
              { label: 'Completed', value: stats.completed, color: '#10b981' },
              { label: 'Skipped', value: stats.skipped, color: '#f97316' },
              { label: 'Cancelled', value: stats.cancelled, color: '#ef4444' },
              { label: 'No Show', value: stats.no_show, color: '#991b1b' },
              { label: 'Avg Process (min)', value: stats.average_processing_minutes, color: '#8b5cf6' },
              { label: 'Avg Wait (min)', value: stats.average_wait_minutes, color: '#0ea5e9' },
            ].map(s => (
              <div key={s.label} style={{ textAlign: 'center', padding: '0.75rem', borderRadius: 8, border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: 4 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Counter Management Panel */}
      {showCounters && (
        <div className="card animate-fade-in" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Monitor size={18} /> Counter Management</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {counters.map(c => {
              const cs = counterStatusColors[c.status] || counterStatusColors.INACTIVE;
              return (
                <div key={c.id} style={{ padding: '1rem', borderRadius: 10, border: `2px solid ${cs.color}20`, background: cs.bg }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{c.name}</span>
                    <span style={{
                      backgroundColor: cs.color + '20',
                      color: cs.color,
                      padding: '0.15rem 0.5rem',
                      borderRadius: '50px',
                      fontSize: '0.7rem',
                      fontWeight: 600,
                    }}>{cs.label}</span>
                  </div>
                  {c.status === 'BUSY' && c.current_farmer_name && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                      <div>🧑‍🌾 {c.current_farmer_name}</div>
                      {c.current_token_display && <div style={{ fontWeight: 600, color: cs.color }}>Token: {c.current_token_display}</div>}
                    </div>
                  )}
                  <button
                    className="btn btn-secondary"
                    style={{ width: '100%', fontSize: '0.75rem', padding: '0.35rem' }}
                    onClick={() => handleToggleCounter(c.id)}
                    disabled={c.status === 'BUSY'}
                  >
                    {c.status === 'ACTIVE' ? 'Deactivate' : c.status === 'BUSY' ? 'Busy (In Use)' : 'Activate'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Skip Confirmation Modal */}
      {skipConfirm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card" style={{ maxWidth: 400, padding: '2rem', textAlign: 'center' }}>
            <AlertTriangle size={40} color="#f59e0b" style={{ marginBottom: '1rem' }} />
            <h3 style={{ margin: '0 0 0.5rem' }}>Skip this farmer?</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              Token <strong>#{skipConfirm.token}</strong> ({skipConfirm.farmer_name}) will be marked as SKIPPED. They will need to contact the centre desk.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <button className="btn btn-secondary" onClick={() => setSkipConfirm(null)}>Cancel</button>
              <button
                className="btn btn-danger"
                onClick={() => handleAction('skip', skipConfirm.booking_id)}
                disabled={!!actionLoading}
              >
                {actionLoading ? 'Skipping…' : 'Confirm Skip'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Queue Table */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: 0 }}>Current Queue</h3>
        </div>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading queue…
          </div>
        ) : queueData.queue.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Megaphone size={40} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
            <p>No farmers currently in the queue.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-color)' }}>
                  {['Token', 'Farmer', 'Produce', 'Quantity', 'Booking Time', 'Status', 'Counter', 'Action'].map((h) => (
                    <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', fontWeight: 600, borderBottom: '1px solid var(--border-color)' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queueData.queue.map((entry) => (
                  <tr key={entry.booking_id} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.2s' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-color)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = ''}
                  >
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div>
                        <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--primary-color)' }}>
                          {entry.token_display || `#${entry.token}`}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 500 }}>{entry.farmer_name}</td>
                    <td style={{ padding: '0.85rem 1rem', fontSize: '0.875rem' }}>{entry.produce_type || entry.crop || 'Paddy'}</td>
                    <td style={{ padding: '0.85rem 1rem', fontSize: '0.875rem', fontWeight: 600 }}>{entry.quantity ? `${entry.quantity} kg` : '—'}</td>
                    <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                      {entry.booking_time ? new Date(entry.booking_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}><StatusBadge status={entry.status} /></td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      {entry.counter_name ? (
                        <span style={{ fontSize: '0.8rem', fontWeight: 500, color: '#5b21b6' }}>{entry.counter_name}</span>
                      ) : <span style={{ color: 'var(--text-secondary)' }}>—</span>}
                    </td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                        {entry.status === 'CALLED' && (
                          <>
                            <button
                              className="btn btn-primary"
                              onClick={() => handleAction('start', entry.booking_id)}
                              disabled={!!actionLoading}
                              style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                            >
                              <Play size={12} /> Start Serving
                            </button>
                            <button
                              onClick={() => setSkipConfirm(entry)}
                              disabled={!!actionLoading}
                              style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', backgroundColor: '#f97316', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem', fontWeight: 500 }}
                            >
                              <SkipForward size={12} /> Skip
                            </button>
                          </>
                        )}
                        {(entry.status === 'SERVING' || entry.status === 'PROCESSING') && (
                          <button
                            onClick={() => handleAction('complete', entry.booking_id)}
                            disabled={!!actionLoading}
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem', fontWeight: 500 }}
                          >
                            <CheckCircle size={12} /> Complete
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
    </div>
  );
};

export default Queue;
