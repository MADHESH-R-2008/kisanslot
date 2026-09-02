import { useState, useEffect } from 'react';
import { Users, Clock, CheckCircle, Activity } from 'lucide-react';
import { queueAPI } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    waiting_count: 0,
    processing_count: 0,
    completed_count: 0,
    active_counters: 0
  });

  const fetchStats = async () => {
    try {
      const response = await queueAPI.getCentreStatus(1); // Default to centre 1 for now
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats", error);
    }
  };

  useEffect(() => {
    fetchStats();
    // Poll every 5s for now, in a real app this would listen to WebSockets
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2>Today's Overview</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Live statistics for your centre</p>
      </div>

      <div className="stat-grid">
        <div className="card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(37, 99, 235, 0.1)', color: 'var(--secondary-color)' }}>
            <Users size={24} />
          </div>
          <div className="stat-info">
            <h3>Total Farmers</h3>
            <p>{stats.waiting_count + stats.processing_count + stats.completed_count}</p>
          </div>
        </div>

        <div className="card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', color: 'var(--accent-color)' }}>
            <Clock size={24} />
          </div>
          <div className="stat-info">
            <h3>Waiting</h3>
            <p>{stats.waiting_count}</p>
          </div>
        </div>

        <div className="card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(5, 150, 105, 0.1)', color: 'var(--primary-color)' }}>
            <CheckCircle size={24} />
          </div>
          <div className="stat-info">
            <h3>Completed</h3>
            <p>{stats.completed_count}</p>
          </div>
        </div>

        <div className="card stat-card">
          <div className="stat-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger-color)' }}>
            <Activity size={24} />
          </div>
          <div className="stat-info">
            <h3>Active Counters</h3>
            <p>{stats.active_counters}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Recent Activity</h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>View the full queue to see detailed operations.</p>
        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
           <a href="/queue" className="btn btn-primary">Go to Queue Management</a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
