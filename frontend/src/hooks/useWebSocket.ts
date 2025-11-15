'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { WebSocketMessage, WebSocketChannel } from '@/types/websocket';

interface UseWebSocketOptions {
  userId?: string;
  channels?: WebSocketChannel[];
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { userId = 'web-user', channels = ['jobs', 'applications', 'interviews'], onMessage, onConnect, onDisconnect } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5; // Reasonable number of attempts before giving up

  const connect = useCallback(() => {
    // Stop trying if we've exceeded max attempts
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.log('Max reconnection attempts reached. WebSocket disabled.');
      return;
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const channelsParam = channels.join(',');
    const url = `${wsUrl}/api/v1/ws?user_id=${userId}&channels=${channelsParam}`;

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);

          // Respond to ping
          if (message.type === 'system.ping') {
            ws.send(JSON.stringify({ action: 'pong' }));
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket closed');
        setIsConnected(false);
        onDisconnect?.();

        // Only reconnect if we haven't exceeded max attempts
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current += 1;

          console.log(`⏳ Reconnecting in ${delay}ms... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else {
          console.log('⚠️ WebSocket connection failed. Real-time updates disabled. Please refresh the page to retry.');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      reconnectAttemptsRef.current = maxReconnectAttempts; // Stop trying
    }
  }, [userId, channels, onMessage, onConnect, onDisconnect]);

  useEffect(() => {
    // Only connect if not already connected or connecting
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []); // Empty dependency array to prevent reconnection on every render

  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const subscribe = useCallback((channel: WebSocketChannel) => {
    send({ action: 'subscribe', channel });
  }, [send]);

  const unsubscribe = useCallback((channel: WebSocketChannel) => {
    send({ action: 'unsubscribe', channel });
  }, [send]);

  return {
    isConnected,
    lastMessage,
    send,
    subscribe,
    unsubscribe,
  };
}
