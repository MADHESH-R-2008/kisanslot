import { useEffect, useState } from 'react';
import { paymentAPI, centreAPI } from '../services/api';

const normalizeStatus = (status) => status === 'PAID' ? 'PAID' : (status || 'PENDING').toUpperCase();

export default function Payments() {
  const [data, setData] = useState({ items: [], page: 1, pages: 0 });
  const [centres, setCentres] = useState([]);
  const [filters, setFilters] = useState({ search: '', status: '', centre_id: '' });
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const load = async (page = 1) => {
    try {
      setError('');
      const response = await paymentAPI.list({
        ...filters,
        centre_id: filters.centre_id || undefined,
        page,
        limit: 20,
      });
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load payments.');
    }
  };

  useEffect(() => {
    centreAPI.list().then((response) => setCentres(response.data)).catch(() => setCentres([]));
    load();
  }, []);

  const runAction = async (payment, action, successMessage) => {
    try {
      setBusyId(payment.id);
      setError('');
      setMessage('');
      await action();
      setMessage(successMessage);
      await load(data.page || 1);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to update payment status.');
    } finally {
      setBusyId(null);
    }
  };

  const markProcessing = (payment) => runAction(
    payment,
    () => paymentAPI.process(payment.booking_id),
    `Payment ${payment.booking_id} is now processing.`,
  );

  const markPaid = (payment) => {
    const transactionId = window.prompt('Enter the bank transaction reference / UTR number:');
    if (transactionId === null) return;
    if (!transactionId.trim()) {
      setError('Transaction reference is required to mark a payment as paid.');
      return;
    }
    runAction(
      payment,
      () => paymentAPI.complete(payment.booking_id, transactionId.trim()),
      `Payment ${payment.booking_id} marked as paid.`,
    );
  };

  const markFailed = (payment) => {
    if (!window.confirm(`Mark payment ${payment.booking_id} as failed?`)) return;
    runAction(
      payment,
      () => paymentAPI.fail(payment.booking_id),
      `Payment ${payment.booking_id} marked as failed.`,
    );
  };

  return (
    <div>
      <h2>Payments</h2>
      {error && <p style={{ color: '#b91c1c', fontWeight: 600 }}>{error}</p>}
      {message && <p style={{ color: '#15803d', fontWeight: 600 }}>{message}</p>}

      <div style={{ display: 'flex', gap: '.6rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        <input
          placeholder="Booking, farmer or transaction"
          value={filters.search}
          onChange={(event) => setFilters({ ...filters, search: event.target.value })}
        />
        <select
          value={filters.status}
          onChange={(event) => setFilters({ ...filters, status: event.target.value })}
        >
          <option value="">All statuses</option>
          {['PENDING', 'PROCESSING', 'PAID', 'FAILED'].map((status) => (
            <option key={status}>{status}</option>
          ))}
        </select>
        <select
          value={filters.centre_id}
          onChange={(event) => setFilters({ ...filters, centre_id: event.target.value })}
        >
          <option value="">All centres</option>
          {centres.map((centre) => (
            <option key={centre.id} value={centre.id}>{centre.name}</option>
          ))}
        </select>
        <button className="btn btn-secondary" onClick={() => load(1)}>Apply</button>
      </div>

      <div className="card" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%' }}>
          <thead>
            <tr>
              {['ID', 'Booking', 'Farmer', 'Centre', 'Amount', 'Method', 'Transaction', 'Status', 'Date', 'Action'].map((heading) => (
                <th key={heading}>{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.items.map((payment) => {
              const status = normalizeStatus(payment.status);
              const busy = busyId === payment.id;
              return (
                <tr key={payment.id}>
                  <td>{payment.id}</td>
                  <td>{payment.booking_id}</td>
                  <td>{payment.farmer}</td>
                  <td>{payment.centre}</td>
                  <td>₹{Number(payment.amount || 0).toLocaleString('en-IN')}</td>
                  <td>{payment.payment_method || 'DBT'}</td>
                  <td>{payment.transaction_reference || '—'}</td>
                  <td><strong>{status}</strong></td>
                  <td>{payment.payment_date ? new Date(payment.payment_date).toLocaleString() : '—'}</td>
                  <td>
                    {(status === 'PENDING' || status === 'FAILED') && (
                      <button disabled={busy} onClick={() => markProcessing(payment)}>
                        {busy ? 'Updating…' : 'Start Processing'}
                      </button>
                    )}
                    {status === 'PROCESSING' && (
                      <div style={{ display: 'flex', gap: '.4rem', whiteSpace: 'nowrap' }}>
                        <button disabled={busy} onClick={() => markPaid(payment)}>
                          {busy ? 'Updating…' : 'Mark Paid'}
                        </button>
                        <button className="btn btn-secondary" disabled={busy} onClick={() => markFailed(payment)}>
                          Mark Failed
                        </button>
                      </div>
                    )}
                    {status === 'PAID' && <span style={{ color: '#15803d' }}>Completed</span>}
                  </td>
                </tr>
              );
            })}
            {!data.items.length && (
              <tr><td colSpan="10" style={{ textAlign: 'center' }}>No payment records found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <p>
        <button disabled={data.page <= 1} onClick={() => load(data.page - 1)}>Previous</button>
        {' '}Page {data.page} of {data.pages || 1}{' '}
        <button disabled={data.page >= data.pages} onClick={() => load(data.page + 1)}>Next</button>
      </p>
    </div>
  );
}
