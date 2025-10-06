-- Agora Schema - Background Jobs and Notifications Tables
-- This file contains the tables for the workflow notification system

-- ====================================================================
-- BACKGROUND JOBS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS agora.background_jobs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  job_type text NOT NULL,
  status text NOT NULL DEFAULT 'PENDING',
  source_id uuid,
  workflow_name text,
  github_run_id text,
  payload jsonb,
  error_message text,
  result_message text,
  triggered_by uuid NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  started_at timestamp with time zone,
  completed_at timestamp with time zone,
  CONSTRAINT background_jobs_pkey PRIMARY KEY (id),
  CONSTRAINT background_jobs_triggered_by_fkey FOREIGN KEY (triggered_by) REFERENCES auth.users(id),
  CONSTRAINT background_jobs_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id),
  CONSTRAINT background_jobs_status_check CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED'))
);

COMMENT ON TABLE agora.background_jobs IS 'Tracks all background workflow jobs triggered by users';
COMMENT ON COLUMN agora.background_jobs.job_type IS 'Type of job (e.g., crawler, analyst, ingestion)';
COMMENT ON COLUMN agora.background_jobs.status IS 'Current status of the job';
COMMENT ON COLUMN agora.background_jobs.result_message IS 'JSON string with job result and optional link';

CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON agora.background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_background_jobs_triggered_by ON agora.background_jobs(triggered_by);
CREATE INDEX IF NOT EXISTS idx_background_jobs_created_at ON agora.background_jobs(created_at DESC);

-- ====================================================================
-- NOTIFICATIONS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS agora.notifications (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  icon_name text NOT NULL DEFAULT 'info',
  title text NOT NULL,
  body text,
  link_url text,
  is_read boolean NOT NULL DEFAULT false,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT notifications_pkey PRIMARY KEY (id),
  CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

COMMENT ON TABLE agora.notifications IS 'Stores user notifications from various system events';
COMMENT ON COLUMN agora.notifications.icon_name IS 'Material icon name for the notification';
COMMENT ON COLUMN agora.notifications.is_read IS 'Whether the user has read the notification';

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON agora.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON agora.notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON agora.notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON agora.notifications(user_id, is_read) WHERE is_read = false;

-- ====================================================================
-- ENABLE ROW LEVEL SECURITY
-- ====================================================================

ALTER TABLE agora.background_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.notifications ENABLE ROW LEVEL SECURITY;

-- RLS Policies for background_jobs
CREATE POLICY "Users can view their own jobs"
  ON agora.background_jobs FOR SELECT
  USING (auth.uid() = triggered_by);

CREATE POLICY "Admins can view all jobs"
  ON agora.background_jobs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid()
      AND app_role IN ('agora_admin', 'agora_moderator')
    )
  );

-- RLS Policies for notifications
CREATE POLICY "Users can view their own notifications"
  ON agora.notifications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications"
  ON agora.notifications FOR UPDATE
  USING (auth.uid() = user_id);

-- System can insert notifications (executed by triggers)
CREATE POLICY "System can insert notifications"
  ON agora.notifications FOR INSERT
  WITH CHECK (true);
