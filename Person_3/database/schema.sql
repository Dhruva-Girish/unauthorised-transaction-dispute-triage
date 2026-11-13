-- schema.sql — ACID SQLite Database Schema for Dispute Triage (Unit 1.C, 1.D)

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    complaint_category TEXT NOT NULL,
    fraud_probability REAL,
    risk_level TEXT NOT NULL,
    priority TEXT NOT NULL,
    evidence_summary TEXT, -- JSON array
    recommended_action TEXT NOT NULL,
    requires_human_review INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'under_review',
    error TEXT,
    metadata TEXT, -- JSON object
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_category ON cases(complaint_category);
CREATE INDEX IF NOT EXISTS idx_cases_priority ON cases(priority);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source_service TEXT NOT NULL,
    details TEXT, -- JSON object
    duration_ms REAL,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_case_id ON audit_events(case_id);

CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    subscription_id TEXT PRIMARY KEY,
    target_url TEXT NOT NULL,
    events TEXT NOT NULL, -- JSON array of subscribed event types
    secret TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
