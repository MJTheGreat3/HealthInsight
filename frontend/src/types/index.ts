// Type definitions for the application

export interface User {
  uid: string;
  userType: "patient" | "institution";
  name?: string;
}

export interface Patient extends User {
  userType: "patient";
  favorites: string[];
  bioData: Record<string, string | number | string[]>;
  reports: string[];
}

export interface Institution extends User {
  userType: "institution";
  patientList: string[];
}

export interface MetricData {
  name?: string;
  value?: string;
  remark?: string;
  range?: string;
  unit?: string;
  verdict?: "NORMAL" | "HIGH" | "LOW" | "CRITICAL";
}

export interface Report {
  id?: string;
  reportId: string;
  patientId: string;
  processedAt: Date;
  attributes: Record<string, MetricData>;
  llmOutput?: string;
  llmReportId?: string;
  selectedConcerns?: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ChatSession {
  id?: string;
  patientId: string;
  messages: ChatMessage[];
  context: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface WebSocketEvents {
  connected: {
    status: string;
    user_id: string;
    user_type: string;
    timestamp: string;
  };
  chat_started: { session_id: string; messages: ChatMessage[] };
  message_response: ChatMessage;
  typing: { typing: boolean };
  chat_ended: { session_id: string };
  data_update: { type: string; data: any; timestamp: string };
  notification: { notification: any; timestamp: string };
  error: { message: string };
  subscribed: { message: string };
}
