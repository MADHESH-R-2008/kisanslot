import { useState, useEffect } from 'react';
import { queueAPI } from '../services/api';
import { Megaphone, Play, CheckCircle, XCircle } from 'lucide-react';

const Queue = () => {
  const [queueData, setQueueData] = useState({
    queue: [],
    waiting_count: 0,
    processing_count: 0,
    completed_count: 0,
    active_counters: 0
  });

  const [loading, setLoading] = useState(true);

  const fetchQueue = async () => {
    try {
      const response = await queueAPI.getCentreStatus(1);
      setQueueData(response.data);
    } catch (error) {
      console.error("Failed to fetch queue", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    // Use polling or WebSocket here. We'll poll every 3 seconds for now.
    const interval = setInterval(fetchQueue, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (actionFn, ...args) => {
    try {
      await actionFn(...args);
      fetchQueue();
    } catch (err) {
      alert(err.response?.data?.detail || "Action failed");
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'WAITING':
      case 'CONFIRMED':
      case 'ARRIVED':
        return <span className="badge badge-warning">WAITING</span>;
      case 'CALLED':
        return <span className="badge badge-info">CALLED</span>;
      case 'PROCESSING':
        return <span className="badge badge-primary" style={{backgroundColor: '#dbeafe', color: '#1e40af'}}>PROCESSING</span>;
      case 'COMPLETED':
        return <span className="badge badge-success">COMPLETED</span>;
      default:
        return <span className="badge badge-secondary">{status}</span>;
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2>Queue Management</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Live view of the procurement queue</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => handleAction(queueAPI.callNext)}
          style={{ fontSize: '1.1rem', padding: '0.75rem 1.5rem', borderRadius: '50px', boxShadow: 'var(--shadow-md)' }}
        >
          <Megaphone size={20} />
          Call Next Farmer
        </button>
      </div>

      <div className="card table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading queue...</div>
        ) : queueData.queue.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No farmers currently in the queue.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Token</th>
                <th>Farmer</th>
                <th>Status</th>
                <th>Arrival Time</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queueData.queue.map((entry) => (
                <tr key={entry.booking_id}>
                  <td>
                    <div style={{ fontWeight: 'bold', fontSize: '1.1rem', color: 'var(--primary-color)' }}>
                      #{entry.token}
                    </div>
                  </td>
                  <td style={{ fontWeight: 500 }}>{entry.farmer_name}</td>
                  <td>{getStatusBadge(entry.status)}</td>
                  <td>{entry.arrival_time ? new Date(entry.arrival_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {entry.status === 'CALLED' && (
                        <>
                          <button className="btn btn-primary" onClick={() => handleAction(queueAPI.startProcessing, entry.booking_id)} style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>
                            <Play size={14} /> Start
                          </button>
                          <button className="btn btn-danger" onClick={() => handleAction(queueAPI.markNoShow, entry.booking_id)} style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>
                            <XCircle size={14} /> No Show
                          </button>
                        </>
                      )}
                      {entry.status === 'PROCESSING' && (
                        <button className="btn" style={{ backgroundColor: '#10b981', color: 'white', padding: '0.25rem 0.5rem', fontSize: '0.75rem', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={() => handleAction(queueAPI.completeProcessing, entry.booking_id)}>
                          <CheckCircle size={14} /> Complete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Queue;
