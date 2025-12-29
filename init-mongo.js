// MongoDB initialization script
db = db.getSiblingDB("healthinsight");

// Create collections
db.createCollection("users");
db.createCollection("reports");
db.createCollection("llm_reports");
db.createCollection("chat_sessions");

// Create indexes for better performance
db.users.createIndex({ uid: 1 }, { unique: true });
db.reports.createIndex({ patient_id: 1 });
db.reports.createIndex({ report_id: 1 }, { unique: true });
db.llm_reports.createIndex({ patient_id: 1 });
db.llm_reports.createIndex({ report_id: 1 });
db.chat_sessions.createIndex({ patient_id: 1 });

print("Database initialized successfully");
