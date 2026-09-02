import { useState, useEffect, useCallback } from 'react';
import { queueAPI } from '../services/api';
import { useQueueSocket } from '../hooks/useQueueSocket';
import { Megaphone, Play, CheckCircle, XCircle, Pause, PlayCircle, Wifi, WifiOff } from 'lucide-react';

const centreId = parseInt(localStorage.getItem('centre_id') || '1', 10);

const statusColors = {
  WAITING:    { bg: '#fef3c7', color: '#92400e', label: 'Waiting' },
  CONFIRMED:  { bg: '#fef3c7', color: '#92400e', label: 'Confirmed' },
  ARRIVED:    { bg: '#dbeafe', color: '#1e40af', label: 'Arrived' },
  CALLED:     { bg: '#ede9fe', color: '#5b21b6', label: 'Called' },
  PROCESSING: { bg: '#d1fae5', color: '#065f46', label: 'Processing' },
  COMPLETED:  { bg: '#f0fdf4', color: '#15803d', label: 'Completed' },
  NO_SHOW:    { bg: '#fee2e2', color: '#991b1b', label: 'No Show' },
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

const Queue = () => {
  const [queueData, setQueueData] = useState({
    queue: [], waiting_count: 0, processing_count: 0,
    completed_count: 0, active_counters: 0, is_paused: false,
  });
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

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

  // WebSocket for real-time updates
  const onWsMessage = useCallback((data) => {
    if (data.event === 'QUEUE_UPDATED') {
      fetchQueue(); // Re-fetch full data when we get an update signal
      setWsConnected(true);
    }
  }, [fetchQueue]);

  useQueueSocket(centreId, onWsMessage);

  useEffect(() => {
    fetchQueue();
    // Fallback poll every 10s in case WS isn't connected
    const interval = setInterval(fetchQueue, 10000);
    return () => clearInterval(interval);
  }, [fetchQueue]);

  const handleAction = async (action, bookingId = null) => {
    const key = bookingId ? `${action}-${bookingId}` : action;
    setActionLoading(key);
    try {
      switch (action) {
        case 'callNext': await queueAPI.callNext(); break;
        case 'pause': await queueAPI.pauseQueue(); break;
        case 'resume': await queueAPI.resumeQueue(); break;
        case 'start': await queueAPI.startProcessing(bookingId); break;
        case 'complete': await queueAPI.completeProcessing(bookingId); break;
        case 'noShow': await queueAPI.markNoShow(bookingId); break;
        default: break;
      }
      await fetchQueue();
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const statCards = [
    { label: 'Waiting', value: queueData.waiting_count, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
    { label: 'Processing', value: queueData.processing_count, color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
    { label: 'Completed', value: queueData.completed_count, color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
    { label: 'Counters', value: queueData.active_counters, color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)' },
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
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

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
                  {['Token', 'Farmer', 'Status', 'Position', 'Arrival', 'Actions'].map((h) => (
                    <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', fontWeight: 600, borderBottom: '1px solid var(--border-color)' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queueData.queue.map((entry, idx) => (
                  <tr key={entry.booking_id} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.2s' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-color)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = ''}
                  >
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--primary-color)' }}>#{entry.token}</span>
                    </td>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 500 }}>{entry.farmer_name}</td>
                    <td style={{ padding: '0.85rem 1rem' }}><StatusBadge status={entry.status} /></td>
                    <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>
                      {entry.queue_position ? `#${entry.queue_position}` : '—'}
                    </td>
                    <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                      {entry.arrival_time
                        ? new Date(entry.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : '—'}
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
                              <Play size={12} /> Start
                            </button>
                            <button
                              className="btn btn-danger"
                              onClick={() => handleAction('noShow', entry.booking_id)}
                              disabled={!!actionLoading}
                              style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                            >
                              <XCircle size={12} /> No Show
                            </button>
                          </>
                        )}
                        {entry.status === 'PROCESSING' && (
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
