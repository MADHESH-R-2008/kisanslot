import { useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '../services/api';

/**
 * Hook that maintains a WebSocket connection to a specific centre's queue.
 * @param {number|null} centreId - The centre to subscribe to. Pass null to disable.
 * @param {function} onMessage - Called with parsed JSON whenever a message arrives.
 */
export function useQueueSocket(centreId, onMessage) {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    if (!centreId) return;
    const url = `${WS_URL}/queue/${centreId}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log(`[WS] Connected to centre ${centreId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      console.log(`[WS] Disconnected from centre ${centreId}. Reconnecting in 3s…`);
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error('[WS] Error', err);
      ws.close();
    };

    wsRef.current = ws;
  }, [centreId, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);
}
