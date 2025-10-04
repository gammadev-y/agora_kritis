-- Agora Schema - RLS Policies
-- Index:
-- 1. Security Helper Function (is_admin_or_moderator)
-- 2. Enable RLS on Tables
-- 3. Public Read-Only & Admin-Managed Content Policies
-- 4. User-Generated Content Policies
-- 5. Contribution Workflow Policies
-- 6. Admin/Moderator RLS Policies
-- 7. Sourcing System RLS Policies
-- 8. Specific Policies for User-Generated Content

-- ====================================================================
-- SECTION 1: SECURITY HELPER FUNCTION
-- Description: This function allows policies to easily check if the
--              currently authenticated user is an admin or moderator.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.is_admin_or_moderator()
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM public.app_user_roles
    WHERE
      user_id = auth.uid() AND
      (role_id = 'agora_admin' OR role_id = 'agora_moderator')
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION agora.is_admin_or_moderator() IS 'Checks if the current user has an admin or moderator role for the Agora app.';


-- ====================================================================
-- SECTION 2: ENABLE RLS ON ALL 'agora' TABLES
-- Description: Activates RLS for every table in the schema. From this
--              point on, all access is denied unless a policy allows it.
-- ====================================================================

ALTER TABLE agora.person_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.assignment_statuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.promise_statuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.action_statuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.action_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.assembly_item_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.interest_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.government_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.government_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.political_parties ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.people ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.ministries ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.government_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.mandates ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.promises ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.government_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.contributions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.user_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.role_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.person_party_affiliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.action_promises ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.mandate_party_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.report_links ENABLE ROW LEVEL SECURITY;


-- ====================================================================
-- SECTION 3: RLS POLICIES FOR 'agora' SCHEMA
-- ====================================================================

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Part 3.1: Public Read-Only & Admin-Managed Content
-- Description: These policies allow anyone to view core platform data.
--              No write policies are created, enforcing the "Safety Net".
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CREATE POLICY "Allow public read access" ON agora.promises FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.government_actions FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.people FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.political_parties FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.government_entities FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.government_roles FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.mandates FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.ministries FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.mandate_party_results FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.role_assignments FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.person_party_affiliations FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.action_promises FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON agora.report_links FOR SELECT USING (true);

-- Lookup Tables
CREATE POLICY "Allow public read access on lookup tables" ON agora.person_types FOR SELECT USING (true);
CREATE POLICY "Allow public read access on lookup tables" ON agora.assignment_statuses FOR SELECT USING (true);
CREATE POLICY "Allow public read access on lookup tables" ON agora.promise_statuses FOR SELECT USING (true);
CREATE POLICY "Allow public read access on lookup tables" ON agora.action_statuses FOR SELECT USING (true);
CREATE POLICY "Allow public read access on lookup tables" ON agora.action_types FOR SELECT USING (true);
CREATE POLICY "Allow public read access on lookup tables" ON agora.assembly_item_outcomes FOR SELECT USING (true);
CREATE POLICY "Allow public read access on lookup tables" ON agora.interest_types FOR SELECT USING (true);
CREATE POLICY "Allow public read access on lookup tables" ON agora.government_levels FOR SELECT USING (true);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Part 3.2: User-Generated Content Policies
-- Description: Specific policies for tables that authenticated users
--              can directly interact with.
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- Table: agora.comments
CREATE POLICY "Allow public read access" ON agora.comments FOR SELECT USING (true);
CREATE POLICY "Allow users to create comments" ON agora.comments FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Allow owner to edit within 5 mins or admins anytime" ON agora.comments FOR UPDATE
    USING ( (auth.uid() = user_id AND (now() - created_at) < interval '5 minutes') OR agora.is_admin_or_moderator() );
CREATE POLICY "Allow owner to soft-delete or admins anytime" ON agora.comments FOR UPDATE -- For soft deletes
    USING ( (auth.uid() = user_id) OR agora.is_admin_or_moderator() );

-- Table: agora.reports
CREATE POLICY "Allow public read access" ON agora.reports FOR SELECT USING (true);
-- IMPORTANT: Your server action MUST NOT select the 'user_id' column for non-admin users.
CREATE POLICY "Allow authenticated users to create reports" ON agora.reports FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Allow owner to edit before approval or admins anytime" ON agora.reports FOR UPDATE
    USING ( (auth.uid() = user_id AND is_anonymous = false AND status <> 'APPROVED') OR agora.is_admin_or_moderator() );
CREATE POLICY "Allow owner to de-anonymize their report" ON agora.reports FOR UPDATE
    USING ( (auth.uid() = user_id AND is_anonymous = true) );

-- Table: agora.votes
CREATE POLICY "Allow public read access" ON agora.votes FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to create votes" ON agora.votes FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Allow owner to change their vote" ON agora.votes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Allow owner to delete their vote" ON agora.votes FOR DELETE USING (auth.uid() = user_id);

-- Table: agora.user_interests
CREATE POLICY "Allow owner to view their own interests" ON agora.user_interests FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow authenticated users to create interests" ON agora.user_interests FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Allow owner to delete their interest" ON agora.user_interests FOR DELETE USING (auth.uid() = user_id);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Part 3.3: Contribution Workflow Policies
-- Description: Policies governing the user contribution system.
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- Table: agora.contributions
CREATE POLICY "Allow all users to view contributions" ON agora.contributions FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to create contributions" ON agora.contributions FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Allow owner to edit/delete before review or admins anytime" ON agora.contributions
    FOR UPDATE USING ( (auth.uid() = submitter_user_id AND status = 'PENDING_REVIEW') OR agora.is_admin_or_moderator() );

-- ====================================================================
-- Part 4: ADMIN/MODERATOR RLS POLICIES
-- Description: Applies a single, permissive policy to every table in
--              the 'agora' schema for privileged users.
-- ====================================================================

-- Table: agora.action_promises
CREATE POLICY "Allow full access for admins and moderators" ON agora.action_promises FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.action_statuses
CREATE POLICY "Allow full access for admins and moderators" ON agora.action_statuses FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.action_types
CREATE POLICY "Allow full access for admins and moderators" ON agora.action_types FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.assembly_item_outcomes
CREATE POLICY "Allow full access for admins and moderators" ON agora.assembly_item_outcomes FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.assignment_statuses
CREATE POLICY "Allow full access for admins and moderators" ON agora.assignment_statuses FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.comments
CREATE POLICY "Allow full access for admins and moderators" ON agora.comments FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.contributions
CREATE POLICY "Allow full access for admins and moderators" ON agora.contributions FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.government_actions
CREATE POLICY "Allow full access for admins and moderators" ON agora.government_actions FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.government_entities
CREATE POLICY "Allow full access for admins and moderators" ON agora.government_entities FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.government_levels
CREATE POLICY "Allow full access for admins and moderators" ON agora.government_levels FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.government_roles
CREATE POLICY "Allow full access for admins and moderators" ON agora.government_roles FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.interest_types
CREATE POLICY "Allow full access for admins and moderators" ON agora.interest_types FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.mandate_party_results
CREATE POLICY "Allow full access for admins and moderators" ON agora.mandate_party_results FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.mandates
CREATE POLICY "Allow full access for admins and moderators" ON agora.mandates FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.ministries
CREATE POLICY "Allow full access for admins and moderators" ON agora.ministries FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.people
CREATE POLICY "Allow full access for admins and moderators" ON agora.people FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.person_party_affiliations
CREATE POLICY "Allow full access for admins and moderators" ON agora.person_party_affiliations FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.person_types
CREATE POLICY "Allow full access for admins and moderators" ON agora.person_types FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.political_parties
CREATE POLICY "Allow full access for admins and moderators" ON agora.political_parties FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.promise_statuses
CREATE POLICY "Allow full access for admins and moderators" ON agora.promise_statuses FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.promises
CREATE POLICY "Allow full access for admins and moderators" ON agora.promises FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.report_links
CREATE POLICY "Allow full access for admins and moderators" ON agora.report_links FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.reports
CREATE POLICY "Allow full access for admins and moderators" ON agora.reports FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.role_assignments
CREATE POLICY "Allow full access for admins and moderators" ON agora.role_assignments FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.user_interests
CREATE POLICY "Allow full access for admins and moderators" ON agora.user_interests FOR ALL USING (agora.is_agora_admin_or_moderator());

-- Table: agora.votes
CREATE POLICY "Allow full access for admins and moderators" ON agora.votes FOR ALL USING (agora.is_agora_admin_or_moderator());

-- ====================================================================
-- SCRIPT: AGORA SOURCING SYSTEM RLS POLICIES
-- Purpose: Configures RLS for the evidence and sourcing tables.
-- ====================================================================

-- ====================================================================
-- SECTION 1: ENABLE RLS ON ALL NEW TABLES
-- Description: Activates RLS for every new table in the sourcing system.
-- ====================================================================

ALTER TABLE agora.source_entity_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.source_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.source_relationship_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.source_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.source_urls ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.source_entity_type_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.promise_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.action_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.report_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.source_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE agora.source_ai_analysis ENABLE ROW LEVEL SECURITY;


-- ====================================================================
-- SECTION 2: CREATE RLS POLICIES
-- Description: Creates policies for public reads, user contributions,
--              and the admin/moderator master access.
-- ====================================================================

DO $$
DECLARE
    table_name TEXT;
BEGIN
    -- This loop applies the 'Allow full access for admins and moderators'
    -- and 'Allow public read access' policies to all tables listed.
    FOR table_name IN
        SELECT unnest(ARRAY[
            'source_entity_types', 'source_types', 'source_relationship_types', 'source_entities',
            'sources', 'source_urls', 'source_entity_type_assignments', 'promise_sources',
            'action_sources', 'report_sources', 'source_relationships', 'source_ai_analysis'
        ])
    LOOP
        -- Drop existing policies to ensure a clean slate
        EXECUTE format('DROP POLICY IF EXISTS "Allow full access for admins and moderators" ON agora.%I;', table_name);
        EXECUTE format('DROP POLICY IF EXISTS "Allow public read access" ON agora.%I;', table_name);

        -- POLICY: Admins/Moderators get a master key for all actions.
        EXECUTE format(
            'CREATE POLICY "Allow full access for admins and moderators" ON agora.%I FOR ALL USING (agora.is_agora_admin_or_moderator());',
            table_name
        );

        -- POLICY: Everyone can view the data.
        EXECUTE format(
            'CREATE POLICY "Allow public read access" ON agora.%I FOR SELECT USING (true);',
            table_name
        );
    END LOOP;
END;
$$;

DROP POLICY IF EXISTS "Allow public read access" ON agora.report_content;
CREATE POLICY "Allow public read access" ON agora.report_content FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow owner or admin to manage content" ON agora.report_content;
CREATE POLICY "Allow owner or admin to manage content" ON agora.report_content
    FOR ALL USING (
        agora.is_agora_admin_or_moderator() OR
        (SELECT user_id FROM agora.reports WHERE id = report_id) = auth.uid()
    );

-- Policies for 'report_author_anonymity' (EXTREMELY STRICT)
DROP POLICY IF EXISTS "DENY ALL ACCESS" ON agora.report_author_anonymity;
-- We create NO policies on this table. This means NO ONE can read or write to it via the
-- client-side API. All interactions MUST happen in server actions using the
-- service_role key, or via SECURITY DEFINER functions. This is the safety net.

-- Policies for 'report_attachments'
DROP POLICY IF EXISTS "Allow public read access" ON agora.report_attachments;
CREATE POLICY "Allow public read access" ON agora.report_attachments FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow owner or admin to manage attachments" ON agora.report_attachments;
CREATE POLICY "Allow owner or admin to manage attachments" ON agora.report_attachments
    FOR ALL USING (
        agora.is_agora_admin_or_moderator() OR
        (SELECT user_id FROM agora.reports WHERE id = report_id) = auth.uid()
    );

-- Policies for 'urls' (Generic, can be expanded later)
DROP POLICY IF EXISTS "Allow public read access" ON agora.urls;
CREATE POLICY "Allow public read access" ON agora.urls FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow admin to manage URLs" ON agora.urls;
CREATE POLICY "Allow admin to manage URLs" ON agora.urls FOR ALL USING (agora.is_agora_admin_or_moderator());

-- ====================================================================
-- SECTION 3: SPECIFIC POLICIES FOR USER-GENERATED CONTENT
-- Description: These policies are layered on top of the general admin
--              and read policies for specific user actions.
-- ====================================================================

-- Table: agora.source_relationships (Linking evidence to evidence)
DROP POLICY IF EXISTS "Allow authenticated users to create relationships" ON agora.source_relationships;
DROP POLICY IF EXISTS "Allow owner to manage their relationships" ON agora.source_relationships;

CREATE POLICY "Allow authenticated users to create relationships" ON agora.source_relationships
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow owner to manage their relationships" ON agora.source_relationships
    FOR UPDATE USING (auth.uid() = user_id);


-- Table: agora.report_sources (Linking evidence to a user's report)
DROP POLICY IF EXISTS "Allow authenticated users to link sources to reports" ON agora.report_sources;
DROP POLICY IF EXISTS "Allow owner to unlink sources from their reports" ON agora.report_sources;

CREATE POLICY "Allow authenticated users to link sources to reports" ON agora.report_sources
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated' AND
        -- Security check: Ensure the user owns the report they are linking to.
        (SELECT user_id FROM agora.reports WHERE id = report_id) = auth.uid()
    );

CREATE POLICY "Allow owner to unlink sources from their reports" ON agora.report_sources
    FOR DELETE USING (
        -- Security check: Ensure the user owns the report they are unlinking from.
        (SELECT user_id FROM agora.reports WHERE id = report_id) = auth.uid()
    );
DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOR table_name IN
        SELECT unnest(ARRAY[
            'budget_statuses', 'budget_category_types', 'funding_source_types',
            'budget_categories', 'budgets', 'budget_spending_items',
            'budget_spending_events', 'budget_amendments', 'funding_sources',
            'funding_entries', 'budget_allocations', 'promise_spending_links',
            'action_spending_links', 'action_funding_links'
        ])
    LOOP
        -- Drop existing policies to ensure a clean slate
        EXECUTE format('DROP POLICY IF EXISTS "Allow full access for admins and moderators" ON agora.%I;', table_name);
        EXECUTE format('DROP POLICY IF EXISTS "Allow public read access" ON agora.%I;', table_name);

        -- POLICY 1: Admins/Moderators get a master key for all actions.
        -- This policy uses the security helper function created previously.
        EXECUTE format(
            'CREATE POLICY "Allow full access for admins and moderators" ON agora.%I FOR ALL USING (agora.is_agora_admin_or_moderator());',
            table_name
        );

        -- POLICY 2: Everyone can view the data.
        EXECUTE format(
            'CREATE POLICY "Allow public read access" ON agora.%I FOR SELECT USING (true);',
            table_name
        );
    END LOOP;
END;
$$;