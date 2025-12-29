// Type definitions for the application

export interface User {
  uid: string;
  userType: "patient" | "institution";
  name?: string;
}

export interface Patient extends User {
  userType: "patient";
  favorites: string[];
  bioData: Record<string, any>;
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
