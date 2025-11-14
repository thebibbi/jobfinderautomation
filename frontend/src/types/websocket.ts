// WebSocket-related types
export type WebSocketEventType =
  | 'system.connected'
  | 'system.ping'
  | 'system.subscribed'
  | 'system.unsubscribed'
  | 'job.created'
  | 'job.analyzing'
  | 'job.analyzed'
  | 'application.status_changed'
  | 'application.updated'
  | 'interview.scheduled'
  | 'interview.updated'
  | 'interview.reminder'
  | 'skill_gap.completed'
  | 'followup.due'
  | 'followup.sent'
  | 'recommendations.new'
  | 'recommendations.updated'
  | 'offer.received'
  | 'offer.accepted';

export interface WebSocketMessage {
  type: WebSocketEventType;
  data: any;
  timestamp: string;
}

export interface WebSocketAction {
  action: 'subscribe' | 'unsubscribe' | 'ping' | 'get_stats';
  channel?: string;
}

export type WebSocketChannel =
  | 'jobs'
  | 'applications'
  | 'recommendations'
  | 'skills'
  | 'followups'
  | 'interviews'
  | 'system';
