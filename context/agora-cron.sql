-- SCRIPT: CREATE BACKGROUND JOBS TABLE AND HELPER FUNCTION

-- Create the table to track the status of all background jobs.
CREATE TABLE IF NOT EXISTS agora.background_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type text NOT NULL, -- e.g., 'crawler-url-extract', 'kritis-analysis'
    status text NOT NULL DEFAULT 'PENDING', -- PENDING, SUCCESS, FAILED
    payload jsonb, -- Stores the inputs, e.g., {"url": "..."}
    result_message text, -- Stores the success or error message
    triggered_by uuid NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
COMMENT ON TABLE agora.background_jobs IS 'Tracks the status of asynchronous jobs like crawling and AI analysis.';
ALTER TABLE agora.background_jobs ENABLE ROW LEVEL SECURITY;

-- RLS: Users can only see the jobs they triggered. Admins can see all.
CREATE POLICY "Users can view their own jobs" ON agora.background_jobs
    FOR SELECT USING (auth.uid() = triggered_by OR agora.is_agora_admin_or_moderator());

-- IMPORTANT: Only server actions with service_role can INSERT or UPDATE jobs.
-- We create NO INSERT/UPDATE policies for regular users.

-- Create a helper function to easily create a new job and return its ID.
-- It's SECURITY DEFINER so it can be called from a user's session but run with admin rights.
CREATE OR REPLACE FUNCTION agora.create_new_job(p_job_type text, p_payload jsonb)
RETURNS uuid AS $$
DECLARE
    new_job_id uuid;
BEGIN
    INSERT INTO agora.background_jobs (job_type, payload, triggered_by)
    VALUES (p_job_type, p_payload, auth.uid())
    RETURNING id INTO new_job_id;
    RETURN new_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Context
--    The "Caller" (Next.js): When a user triggers a workflow, your server action will first create a "job ticket" in a new database table. It gets back a unique job_id.
--    The "Worker" (Python): The Next.js app passes this job_id to the GitHub Action. The Python script does its work.
--   The "Update" (Python): When the Python script finishes (either successfully or with an error), its very last step is to use its Supabase client to UPDATE the "job ticket" in the database with the final status.
--    The "Listener" (Next.js): Your Agora app will be listening in real-time for changes to this table. When it sees the status of the job update, it will trigger a notification.