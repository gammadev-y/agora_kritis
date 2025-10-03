-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE agora.action_funding_links (
  action_id uuid NOT NULL,
  funding_entry_id uuid NOT NULL,
  influence_type text NOT NULL,
  predicted_impact_amount numeric,
  translations jsonb,
  CONSTRAINT action_funding_links_pkey PRIMARY KEY (funding_entry_id, action_id),
  CONSTRAINT action_funding_links_action_id_fkey FOREIGN KEY (action_id) REFERENCES agora.government_actions(id),
  CONSTRAINT action_funding_links_funding_entry_id_fkey FOREIGN KEY (funding_entry_id) REFERENCES agora.funding_entries(id)
);
CREATE TABLE agora.action_promises (
  action_id uuid NOT NULL,
  promise_id uuid NOT NULL,
  CONSTRAINT action_promises_pkey PRIMARY KEY (promise_id, action_id),
  CONSTRAINT action_promises_action_id_fkey FOREIGN KEY (action_id) REFERENCES agora.government_actions(id),
  CONSTRAINT action_promises_promise_id_fkey FOREIGN KEY (promise_id) REFERENCES agora.promises(id)
);
CREATE TABLE agora.action_sources (
  action_id uuid NOT NULL,
  source_id uuid NOT NULL,
  translations jsonb,
  CONSTRAINT action_sources_pkey PRIMARY KEY (action_id, source_id),
  CONSTRAINT action_sources_action_id_fkey FOREIGN KEY (action_id) REFERENCES agora.government_actions(id),
  CONSTRAINT action_sources_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.action_spending_links (
  action_id uuid NOT NULL,
  spending_item_id uuid NOT NULL,
  allocated_amount numeric NOT NULL,
  translations jsonb,
  CONSTRAINT action_spending_links_pkey PRIMARY KEY (action_id, spending_item_id),
  CONSTRAINT action_spending_links_action_id_fkey FOREIGN KEY (action_id) REFERENCES agora.government_actions(id),
  CONSTRAINT action_spending_links_spending_item_id_fkey FOREIGN KEY (spending_item_id) REFERENCES agora.budget_spending_items(id)
);
CREATE TABLE agora.action_statuses (
  id text NOT NULL,
  translations jsonb NOT NULL,
  color_hex text,
  CONSTRAINT action_statuses_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.action_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT action_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.assembly_item_outcomes (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT assembly_item_outcomes_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.assignment_statuses (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT assignment_statuses_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.budget_allocations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  funding_entry_id uuid NOT NULL,
  spending_item_id uuid,
  allocated_amount numeric,
  allocated_percentage numeric,
  allocation_rule jsonb,
  translations jsonb,
  CONSTRAINT budget_allocations_pkey PRIMARY KEY (id),
  CONSTRAINT budget_allocations_funding_entry_id_fkey FOREIGN KEY (funding_entry_id) REFERENCES agora.funding_entries(id),
  CONSTRAINT budget_allocations_spending_item_id_fkey FOREIGN KEY (spending_item_id) REFERENCES agora.budget_spending_items(id)
);
CREATE TABLE agora.budget_amendments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  spending_item_id uuid NOT NULL,
  source_id uuid NOT NULL,
  amendment_date date NOT NULL,
  previous_amount numeric NOT NULL,
  new_amount numeric NOT NULL,
  translations jsonb,
  CONSTRAINT budget_amendments_pkey PRIMARY KEY (id),
  CONSTRAINT budget_amendments_spending_item_id_fkey FOREIGN KEY (spending_item_id) REFERENCES agora.budget_spending_items(id),
  CONSTRAINT budget_amendments_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.budget_categories (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  parent_category_id uuid,
  type_id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT budget_categories_pkey PRIMARY KEY (id),
  CONSTRAINT budget_categories_parent_category_id_fkey FOREIGN KEY (parent_category_id) REFERENCES agora.budget_categories(id),
  CONSTRAINT budget_categories_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.budget_category_types(id)
);
CREATE TABLE agora.budget_category_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT budget_category_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.budget_spending_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  spending_item_id uuid NOT NULL,
  source_id uuid,
  amount numeric NOT NULL,
  event_date date NOT NULL,
  translations jsonb,
  CONSTRAINT budget_spending_events_pkey PRIMARY KEY (id),
  CONSTRAINT budget_spending_events_spending_item_id_fkey FOREIGN KEY (spending_item_id) REFERENCES agora.budget_spending_items(id),
  CONSTRAINT budget_spending_events_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.budget_spending_items (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  budget_id uuid NOT NULL,
  category_id uuid NOT NULL,
  ministry_id uuid,
  budgeted_amount numeric NOT NULL,
  sentiment_score numeric NOT NULL DEFAULT 0.0,
  translations jsonb,
  slug text UNIQUE,
  parent_spending_item_id uuid,
  CONSTRAINT budget_spending_items_pkey PRIMARY KEY (id),
  CONSTRAINT budget_spending_items_budget_id_fkey FOREIGN KEY (budget_id) REFERENCES agora.budgets(id),
  CONSTRAINT budget_spending_items_category_id_fkey FOREIGN KEY (category_id) REFERENCES agora.budget_categories(id),
  CONSTRAINT budget_spending_items_ministry_id_fkey FOREIGN KEY (ministry_id) REFERENCES agora.ministries(id),
  CONSTRAINT budget_spending_items_parent_spending_item_id_fkey FOREIGN KEY (parent_spending_item_id) REFERENCES agora.budget_spending_items(id)
);
CREATE TABLE agora.budget_statuses (
  id text NOT NULL,
  translations jsonb NOT NULL,
  color_hex text,
  icon_name text,
  CONSTRAINT budget_statuses_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.budgets (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  government_entity_id uuid NOT NULL,
  year integer NOT NULL,
  status_id text NOT NULL,
  translations jsonb,
  total_budgeted_spending numeric NOT NULL DEFAULT 0,
  total_actual_spending numeric NOT NULL DEFAULT 0,
  slug text UNIQUE,
  mandate_id uuid,
  CONSTRAINT budgets_pkey PRIMARY KEY (id),
  CONSTRAINT budgets_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT budgets_status_id_fkey FOREIGN KEY (status_id) REFERENCES agora.budget_statuses(id),
  CONSTRAINT budgets_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id)
);
CREATE TABLE agora.comments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  parent_comment_id uuid,
  target_id uuid NOT NULL,
  target_table text NOT NULL,
  content text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT comments_pkey PRIMARY KEY (id),
  CONSTRAINT comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id),
  CONSTRAINT comments_parent_comment_id_fkey FOREIGN KEY (parent_comment_id) REFERENCES agora.comments(id)
);
CREATE TABLE agora.contributions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  submitter_user_id uuid NOT NULL,
  reviewer_user_id uuid,
  target_table text NOT NULL,
  submitted_data jsonb NOT NULL,
  status text NOT NULL DEFAULT 'PENDING_REVIEW'::text,
  notes text,
  reviewed_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT contributions_pkey PRIMARY KEY (id),
  CONSTRAINT contributions_submitter_user_id_fkey FOREIGN KEY (submitter_user_id) REFERENCES public.user_profiles(id),
  CONSTRAINT contributions_reviewer_user_id_fkey FOREIGN KEY (reviewer_user_id) REFERENCES public.user_profiles(id)
);
CREATE TABLE agora.document_chunks (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  chunk_index integer NOT NULL,
  content text,
  embedding USER-DEFINED,
  CONSTRAINT document_chunks_pkey PRIMARY KEY (id),
  CONSTRAINT document_chunks_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.funding_entries (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  funding_source_id uuid NOT NULL,
  government_entity_id uuid NOT NULL,
  year integer NOT NULL,
  predicted_revenue numeric,
  actual_revenue numeric,
  prediction_source_id uuid,
  actual_source_id uuid,
  transfer_source_spending_item_id uuid,
  CONSTRAINT funding_entries_pkey PRIMARY KEY (id),
  CONSTRAINT funding_entries_funding_source_id_fkey FOREIGN KEY (funding_source_id) REFERENCES agora.funding_sources(id),
  CONSTRAINT funding_entries_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT funding_entries_prediction_source_id_fkey FOREIGN KEY (prediction_source_id) REFERENCES agora.sources(id),
  CONSTRAINT funding_entries_actual_source_id_fkey FOREIGN KEY (actual_source_id) REFERENCES agora.sources(id),
  CONSTRAINT funding_entries_transfer_source_spending_item_id_fkey FOREIGN KEY (transfer_source_spending_item_id) REFERENCES agora.budget_spending_items(id)
);
CREATE TABLE agora.funding_source_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT funding_source_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.funding_sources (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  type_id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT funding_sources_pkey PRIMARY KEY (id),
  CONSTRAINT funding_sources_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.funding_source_types(id)
);
CREATE TABLE agora.glossary (
  term text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT glossary_pkey PRIMARY KEY (term)
);
CREATE TABLE agora.government_actions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  action_type_id text,
  status_id text,
  responsible_role_id uuid,
  government_entity_id uuid,
  timeline_proposal_date date,
  timeline_implementation_date date,
  translations jsonb,
  is_active boolean NOT NULL DEFAULT true,
  ministry_id uuid,
  mandate_id uuid,
  CONSTRAINT government_actions_pkey PRIMARY KEY (id),
  CONSTRAINT government_actions_action_type_id_fkey FOREIGN KEY (action_type_id) REFERENCES agora.action_types(id),
  CONSTRAINT government_actions_status_id_fkey FOREIGN KEY (status_id) REFERENCES agora.action_statuses(id),
  CONSTRAINT government_actions_responsible_role_id_fkey FOREIGN KEY (responsible_role_id) REFERENCES agora.government_roles(id),
  CONSTRAINT government_actions_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT government_actions_ministry_id_fkey FOREIGN KEY (ministry_id) REFERENCES agora.ministries(id),
  CONSTRAINT government_actions_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id)
);
CREATE TABLE agora.government_entities (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  level_id text NOT NULL,
  parent_entity_id uuid,
  country_code character,
  translations jsonb,
  area USER-DEFINED,
  is_active boolean NOT NULL DEFAULT true,
  slug text UNIQUE,
  image_url text,
  CONSTRAINT government_entities_pkey PRIMARY KEY (id),
  CONSTRAINT government_entities_level_id_fkey FOREIGN KEY (level_id) REFERENCES agora.government_levels(id),
  CONSTRAINT government_entities_parent_entity_id_fkey FOREIGN KEY (parent_entity_id) REFERENCES agora.government_entities(id)
);
CREATE TABLE agora.government_levels (
  id text NOT NULL,
  translations jsonb NOT NULL,
  parent_level_id text,
  CONSTRAINT government_levels_pkey PRIMARY KEY (id),
  CONSTRAINT government_levels_parent_level_id_fkey FOREIGN KEY (parent_level_id) REFERENCES agora.government_levels(id)
);
CREATE TABLE agora.government_roles (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  government_entity_id uuid NOT NULL,
  ministry_id uuid,
  translations jsonb,
  order smallint,
  CONSTRAINT government_roles_pkey PRIMARY KEY (id),
  CONSTRAINT government_roles_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT government_roles_ministry_id_fkey FOREIGN KEY (ministry_id) REFERENCES agora.ministries(id)
);
CREATE TABLE agora.ingestion_logs (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  ingestion_id uuid NOT NULL,
  action text NOT NULL,
  payload jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT ingestion_logs_pkey PRIMARY KEY (id),
  CONSTRAINT ingestion_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id),
  CONSTRAINT ingestion_logs_ingestion_id_fkey FOREIGN KEY (ingestion_id) REFERENCES agora.pending_ingestions(id)
);
CREATE TABLE agora.interest_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  icon_name text,
  CONSTRAINT interest_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.law_article_references (
  source_article_version_id uuid NOT NULL,
  target_article_version_id uuid NOT NULL,
  reference_type text NOT NULL,
  CONSTRAINT law_article_references_pkey PRIMARY KEY (source_article_version_id, target_article_version_id),
  CONSTRAINT law_article_references_source_article_version_id_fkey FOREIGN KEY (source_article_version_id) REFERENCES agora.law_article_versions(id),
  CONSTRAINT law_article_references_target_article_version_id_fkey FOREIGN KEY (target_article_version_id) REFERENCES agora.law_article_versions(id)
);
CREATE TABLE agora.law_article_version_tags (
  version_id uuid NOT NULL,
  tag_id uuid NOT NULL,
  CONSTRAINT law_article_version_tags_pkey PRIMARY KEY (version_id, tag_id),
  CONSTRAINT law_article_version_tags_version_id_fkey FOREIGN KEY (version_id) REFERENCES agora.law_article_versions(id),
  CONSTRAINT law_article_version_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES agora.tags(id)
);
CREATE TABLE agora.law_article_versions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  article_id uuid NOT NULL,
  mandate_id uuid NOT NULL,
  status_id text NOT NULL,
  valid_from date NOT NULL,
  valid_to date,
  official_text text NOT NULL,
  translations jsonb,
  CONSTRAINT law_article_versions_pkey PRIMARY KEY (id),
  CONSTRAINT law_article_versions_article_id_fkey FOREIGN KEY (article_id) REFERENCES agora.law_articles(id),
  CONSTRAINT law_article_versions_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id),
  CONSTRAINT law_article_versions_status_id_fkey FOREIGN KEY (status_id) REFERENCES agora.law_version_statuses(id)
);
CREATE TABLE agora.law_articles (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  law_id uuid NOT NULL,
  article_number text NOT NULL,
  CONSTRAINT law_articles_pkey PRIMARY KEY (id),
  CONSTRAINT law_articles_law_id_fkey FOREIGN KEY (law_id) REFERENCES agora.laws(id)
);
CREATE TABLE agora.law_categories (
  id text NOT NULL,
  translations jsonb,
  CONSTRAINT law_categories_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.law_relationships (
  source_law_id uuid NOT NULL,
  target_law_id uuid NOT NULL,
  relationship_type text NOT NULL,
  CONSTRAINT law_relationships_pkey PRIMARY KEY (source_law_id, target_law_id),
  CONSTRAINT law_relationships_source_law_id_fkey FOREIGN KEY (source_law_id) REFERENCES agora.laws(id),
  CONSTRAINT law_relationships_target_law_id_fkey FOREIGN KEY (target_law_id) REFERENCES agora.laws(id)
);
CREATE TABLE agora.law_types (
  id text NOT NULL,
  translations jsonb,
  CONSTRAINT law_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.law_version_statuses (
  id text NOT NULL,
  translations jsonb,
  CONSTRAINT law_version_statuses_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.laws (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  government_entity_id uuid NOT NULL,
  official_number text UNIQUE,
  slug text NOT NULL UNIQUE,
  type_id text,
  category_id text,
  enactment_date date,
  official_title text NOT NULL,
  translations jsonb,
  CONSTRAINT laws_pkey PRIMARY KEY (id),
  CONSTRAINT laws_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT laws_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.law_types(id),
  CONSTRAINT laws_category_id_fkey FOREIGN KEY (category_id) REFERENCES agora.law_categories(id)
);
CREATE TABLE agora.mandate_party_results (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  mandate_id uuid NOT NULL,
  party_id uuid NOT NULL,
  vote_percentage numeric,
  seat_count integer,
  rank integer,
  CONSTRAINT mandate_party_results_pkey PRIMARY KEY (id),
  CONSTRAINT mandate_party_results_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id),
  CONSTRAINT mandate_party_results_party_id_fkey FOREIGN KEY (party_id) REFERENCES agora.political_parties(id)
);
CREATE TABLE agora.mandates (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  government_entity_id uuid NOT NULL,
  translations jsonb,
  start_date date NOT NULL,
  end_date date,
  slug text UNIQUE,
  CONSTRAINT mandates_pkey PRIMARY KEY (id),
  CONSTRAINT mandates_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id)
);
CREATE TABLE agora.ministries (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  government_entity_id uuid NOT NULL,
  translations jsonb,
  CONSTRAINT ministries_pkey PRIMARY KEY (id),
  CONSTRAINT ministries_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id)
);
CREATE TABLE agora.pending_extractions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  document_chunk_id uuid,
  status text NOT NULL DEFAULT 'PENDING'::text,
  extracted_data jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT pending_extractions_pkey PRIMARY KEY (id),
  CONSTRAINT pending_extractions_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id),
  CONSTRAINT pending_extractions_document_chunk_id_fkey FOREIGN KEY (document_chunk_id) REFERENCES agora.document_chunks(id)
);
CREATE TABLE agora.pending_ingestions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  status text NOT NULL DEFAULT 'PENDING_VALIDATION'::text,
  ingestion_data jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT pending_ingestions_pkey PRIMARY KEY (id),
  CONSTRAINT pending_ingestions_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.people (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  full_name text NOT NULL UNIQUE,
  preferred_name text,
  person_type_id text NOT NULL,
  avatar_url text,
  date_of_birth date,
  translations jsonb,
  is_active boolean NOT NULL DEFAULT true,
  CONSTRAINT people_pkey PRIMARY KEY (id),
  CONSTRAINT people_person_type_id_fkey FOREIGN KEY (person_type_id) REFERENCES agora.person_types(id)
);
CREATE TABLE agora.person_party_affiliations (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  person_id uuid NOT NULL,
  party_id uuid,
  start_date date NOT NULL,
  end_date date,
  CONSTRAINT person_party_affiliations_pkey PRIMARY KEY (id),
  CONSTRAINT person_party_affiliations_person_id_fkey FOREIGN KEY (person_id) REFERENCES agora.people(id),
  CONSTRAINT person_party_affiliations_party_id_fkey FOREIGN KEY (party_id) REFERENCES agora.political_parties(id)
);
CREATE TABLE agora.person_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  icon_name text,
  CONSTRAINT person_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.political_parties (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  acronym text,
  country_code character,
  translations jsonb,
  logo_url text,
  official_website_url text,
  date_founded date,
  headquarters_address text,
  primary_color text,
  secondary_color text,
  national_order integer,
  is_active boolean NOT NULL DEFAULT true,
  CONSTRAINT political_parties_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.promise_sources (
  promise_id uuid NOT NULL,
  source_id uuid NOT NULL,
  translations jsonb,
  CONSTRAINT promise_sources_pkey PRIMARY KEY (source_id, promise_id),
  CONSTRAINT promise_sources_promise_id_fkey FOREIGN KEY (promise_id) REFERENCES agora.promises(id),
  CONSTRAINT promise_sources_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.promise_spending_links (
  promise_id uuid NOT NULL,
  spending_item_id uuid NOT NULL,
  allocated_amount numeric NOT NULL,
  translations jsonb,
  CONSTRAINT promise_spending_links_pkey PRIMARY KEY (promise_id, spending_item_id),
  CONSTRAINT promise_spending_links_promise_id_fkey FOREIGN KEY (promise_id) REFERENCES agora.promises(id),
  CONSTRAINT promise_spending_links_spending_item_id_fkey FOREIGN KEY (spending_item_id) REFERENCES agora.budget_spending_items(id)
);
CREATE TABLE agora.promise_statuses (
  id text NOT NULL,
  translations jsonb NOT NULL,
  color_hex text,
  icon text,
  order smallint,
  CONSTRAINT promise_statuses_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.promises (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE,
  date_made date,
  status_id text,
  government_entity_id uuid,
  translations jsonb,
  is_active boolean NOT NULL DEFAULT true,
  promised_by uuid,
  ministry_id uuid,
  mandate_id uuid,
  CONSTRAINT promises_pkey PRIMARY KEY (id),
  CONSTRAINT promises_status_id_fkey FOREIGN KEY (status_id) REFERENCES agora.promise_statuses(id),
  CONSTRAINT promises_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT promises_promised_by_fkey FOREIGN KEY (promised_by) REFERENCES agora.people(id),
  CONSTRAINT promises_ministry_id_fkey FOREIGN KEY (ministry_id) REFERENCES agora.ministries(id),
  CONSTRAINT promises_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id)
);
CREATE TABLE agora.prompts (
  id text NOT NULL,
  title text NOT NULL,
  prompt_text text NOT NULL,
  version_history jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT prompts_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.report_attachments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  report_id uuid NOT NULL,
  url_id uuid NOT NULL,
  translations jsonb,
  display_order smallint DEFAULT 0,
  CONSTRAINT report_attachments_pkey PRIMARY KEY (id),
  CONSTRAINT report_attachments_report_id_fkey FOREIGN KEY (report_id) REFERENCES agora.reports(id),
  CONSTRAINT report_attachments_url_id_fkey FOREIGN KEY (url_id) REFERENCES agora.urls(id)
);
CREATE TABLE agora.report_author_anonymity (
  report_id uuid NOT NULL,
  user_id uuid NOT NULL,
  CONSTRAINT report_author_anonymity_pkey PRIMARY KEY (report_id),
  CONSTRAINT report_author_anonymity_report_id_fkey FOREIGN KEY (report_id) REFERENCES agora.reports(id),
  CONSTRAINT report_author_anonymity_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id)
);
CREATE TABLE agora.report_content (
  report_id uuid NOT NULL,
  content_body jsonb NOT NULL,
  CONSTRAINT report_content_pkey PRIMARY KEY (report_id),
  CONSTRAINT report_content_report_id_fkey FOREIGN KEY (report_id) REFERENCES agora.reports(id)
);
CREATE TABLE agora.report_links (
  report_id uuid NOT NULL,
  target_id uuid NOT NULL,
  target_table text NOT NULL,
  CONSTRAINT report_links_pkey PRIMARY KEY (target_table, target_id, report_id),
  CONSTRAINT report_links_report_id_fkey FOREIGN KEY (report_id) REFERENCES agora.reports(id)
);
CREATE TABLE agora.report_sources (
  report_id uuid NOT NULL,
  source_id uuid NOT NULL,
  translations jsonb,
  CONSTRAINT report_sources_pkey PRIMARY KEY (report_id, source_id),
  CONSTRAINT report_sources_report_id_fkey FOREIGN KEY (report_id) REFERENCES agora.reports(id),
  CONSTRAINT report_sources_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.reports (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  is_anonymous boolean NOT NULL DEFAULT false,
  status text NOT NULL DEFAULT 'PENDING_REVIEW'::text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  slug text UNIQUE,
  translations jsonb,
  published_at timestamp with time zone,
  image_url text,
  mandate_id uuid,
  government_entity_id uuid,
  CONSTRAINT reports_pkey PRIMARY KEY (id),
  CONSTRAINT reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id),
  CONSTRAINT reports_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id),
  CONSTRAINT reports_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id)
);
CREATE TABLE agora.role_assignments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  person_id uuid NOT NULL,
  role_id uuid NOT NULL,
  mandate_id uuid NOT NULL,
  status_id text NOT NULL,
  start_date date NOT NULL,
  end_date date,
  CONSTRAINT role_assignments_pkey PRIMARY KEY (id),
  CONSTRAINT role_assignments_person_id_fkey FOREIGN KEY (person_id) REFERENCES agora.people(id),
  CONSTRAINT role_assignments_role_id_fkey FOREIGN KEY (role_id) REFERENCES agora.government_roles(id),
  CONSTRAINT role_assignments_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id),
  CONSTRAINT role_assignments_status_id_fkey FOREIGN KEY (status_id) REFERENCES agora.assignment_statuses(id)
);
CREATE TABLE agora.source_ai_analysis (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  model_version text NOT NULL,
  analysis_data jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT source_ai_analysis_pkey PRIMARY KEY (id),
  CONSTRAINT source_ai_analysis_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.source_entities (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  parent_entity_id uuid,
  logo_url text,
  website_url text,
  overall_credibility_score numeric DEFAULT 0.0,
  is_official_source boolean NOT NULL DEFAULT false,
  CONSTRAINT source_entities_pkey PRIMARY KEY (id),
  CONSTRAINT source_entities_parent_entity_id_fkey FOREIGN KEY (parent_entity_id) REFERENCES agora.source_entities(id)
);
CREATE TABLE agora.source_entity_type_assignments (
  source_entity_id uuid NOT NULL,
  type_id text NOT NULL,
  CONSTRAINT source_entity_type_assignments_pkey PRIMARY KEY (type_id, source_entity_id),
  CONSTRAINT source_entity_type_assignments_source_entity_id_fkey FOREIGN KEY (source_entity_id) REFERENCES agora.source_entities(id),
  CONSTRAINT source_entity_type_assignments_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.source_entity_types(id)
);
CREATE TABLE agora.source_entity_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT source_entity_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.source_relationship_types (
  id text NOT NULL,
  effect integer NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT source_relationship_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.source_relationships (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  target_source_id uuid NOT NULL,
  relationship_type_id text NOT NULL,
  user_id uuid NOT NULL,
  credibility_score numeric DEFAULT 0.0,
  translations jsonb,
  CONSTRAINT source_relationships_pkey PRIMARY KEY (id),
  CONSTRAINT source_relationships_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id),
  CONSTRAINT source_relationships_target_source_id_fkey FOREIGN KEY (target_source_id) REFERENCES agora.sources(id),
  CONSTRAINT source_relationships_relationship_type_id_fkey FOREIGN KEY (relationship_type_id) REFERENCES agora.source_relationship_types(id),
  CONSTRAINT source_relationships_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id)
);
CREATE TABLE agora.source_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT source_types_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.source_urls (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  url text NOT NULL,
  url_type text NOT NULL,
  translations jsonb,
  CONSTRAINT source_urls_pkey PRIMARY KEY (id),
  CONSTRAINT source_urls_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.sources (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  source_entity_id uuid,
  type_id text NOT NULL,
  author text,
  published_at timestamp with time zone,
  main_url text,
  credibility_score numeric DEFAULT 0.0,
  is_official_document boolean NOT NULL DEFAULT false,
  translations jsonb,
  is_active boolean NOT NULL DEFAULT true,
  internal_storage_path text,
  internal_file_metadata jsonb,
  archived_url text,
  archive_status text,
  slug text,
  CONSTRAINT sources_pkey PRIMARY KEY (id),
  CONSTRAINT sources_source_entity_id_fkey FOREIGN KEY (source_entity_id) REFERENCES agora.source_entities(id),
  CONSTRAINT sources_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.source_types(id)
);
CREATE TABLE agora.tags (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  CONSTRAINT tags_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.urls (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  url text NOT NULL UNIQUE,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT urls_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.user_filters (
  user_id uuid NOT NULL,
  filter_preferences jsonb,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT user_filters_pkey PRIMARY KEY (user_id),
  CONSTRAINT user_filters_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE agora.user_interests (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  interest_type_id text NOT NULL,
  target_id uuid NOT NULL,
  target_table text NOT NULL,
  CONSTRAINT user_interests_pkey PRIMARY KEY (id),
  CONSTRAINT user_interests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id),
  CONSTRAINT user_interests_interest_type_id_fkey FOREIGN KEY (interest_type_id) REFERENCES agora.interest_types(id)
);
CREATE TABLE agora.votes (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  target_id uuid NOT NULL,
  target_table text NOT NULL,
  vote_type text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT votes_pkey PRIMARY KEY (id),
  CONSTRAINT votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id)
);

--RLS POLICIES
-- ====================================================================
-- SCRIPT: AGORA SCHEMA RLS POLICY CONFIGURATION
-- Purpose: Creates a helper function and all necessary RLS policies for
--          the Agora application, implementing the "Safety Net" model.
-- ====================================================================

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

--agora functions (do not use)
is_admin_or_moderator()={
  BEGIN
    RETURN EXISTS (
      SELECT 1
      FROM public.app_user_roles
      WHERE
        user_id = auth.uid() AND
        (role_id = 'agora_admin' OR role_id = 'agora_moderator')
    );
  END;
}

-- ====================================================================
-- SCRIPT: SOURCING SYSTEM DATA-FETCHING FUNCTIONS
-- Purpose: Creates two performant RPC functions to fetch data for the
--          source entity list and detail pages.
-- ====================================================================

-- ====================================================================
-- FUNCTION 1: Get Source Entities for the List/Gallery View
-- Description: Fetches all source entities with their parent's details
--              and a count of their associated sources.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_source_entities_with_details()
RETURNS TABLE (
    id uuid,
    name text,
    logo_url text,
    website_url text,
    parent_entity_id uuid,
    parent_name text,
    sources_count bigint
) AS $$
BEGIN
    RETURN QUERY
    WITH source_counts AS (
        SELECT
            se.id AS entity_id,
            COUNT(s.id) AS count
        FROM
            agora.source_entities se
        LEFT JOIN
            agora.sources s ON se.id = s.source_entity_id
        GROUP BY
            se.id
    )
    SELECT
        se.id,
        se.name,
        se.logo_url,
        se.website_url,
        se.parent_entity_id,
        parent.name AS parent_name,
        COALESCE(sc.count, 0) AS sources_count
    FROM
        agora.source_entities AS se
    LEFT JOIN
        agora.source_entities AS parent ON se.parent_entity_id = parent.id
    LEFT JOIN
        source_counts AS sc ON se.id = sc.entity_id
    ORDER BY
        se.name;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_source_entities_with_details() IS 'Returns all source entities with their parent''s name and a count of their associated sources.';


-- ====================================================================
-- FUNCTION 2: Get a Single Source Entity with ALL Related Data
-- Description: Fetches one source entity by its ID and aggregates all
--              its children and sources (with filtering) into JSON arrays.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_source_entity_full_by_id(
    entity_id uuid,
    search_text text DEFAULT NULL,
    related_entity_id uuid DEFAULT NULL
)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    SELECT
        jsonb_build_object(
            'id', se.id,
            'name', se.name,
            'logo_url', se.logo_url,
            'website_url', se.website_url,
            'is_official_source', se.is_official_source,
            'parent',
                CASE
                    WHEN parent.id IS NOT NULL THEN jsonb_build_object('id', parent.id, 'name', parent.name)
                    ELSE null
                END,
            'children', (
                SELECT COALESCE(jsonb_agg(
                    jsonb_build_object('id', child.id, 'name', child.name)
                ), '[]'::jsonb)
                FROM agora.source_entities child
                WHERE child.parent_entity_id = se.id
            ),
            'sources', (
                SELECT COALESCE(jsonb_agg(
                    jsonb_build_object(
                        'id', s.id,
                        'title', s.translations->'en'->>'title', -- Example for one language
                        'published_at', s.published_at,
                        'credibility_score', s.credibility_score,
                        'source_type', st.translations->'en'->>'name' -- Example
                    )
                ), '[]'::jsonb)
                FROM agora.sources s
                LEFT JOIN agora.source_types st ON s.type_id = st.id
                WHERE
                    (s.source_entity_id = se.id OR s.source_entity_id = related_entity_id) AND
                    (search_text IS NULL OR (s.translations->'en'->>'title') ILIKE '%' || search_text || '%')
            )
        )
    INTO result
    FROM
        agora.source_entities se
    LEFT JOIN
        agora.source_entities AS parent ON se.parent_entity_id = parent.id
    WHERE
        se.id = entity_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_source_entity_full_by_id(uuid, text, uuid) IS 'Returns a single source entity and all its children and filterable sources as a single JSONB object.';

-- ====================================================================
-- FUNCTION: Get Unassociated Government Actions for a Promise
-- Description: Fetches a paginated and filtered list of government actions
--              that are NOT already linked to a specific promise.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_unassociated_gov_actions_for_promise(
    p_government_entity_id uuid,
    p_promise_id uuid,
    p_ministry_id uuid DEFAULT NULL,
    p_action_type_id text DEFAULT NULL,
    p_status_id text DEFAULT NULL,
    p_is_active boolean DEFAULT NULL,
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    -- Define the columns to be returned, matching your select statement
    id uuid,
    slug text,
    action_type_id text,
    status_id text,
    responsible_role_id uuid,
    government_entity_id uuid,
    ministry_id uuid,
    timeline_proposal_date date,
    timeline_implementation_date date,
    translations jsonb,
    is_active boolean,
    -- We can even pre-join the related data right here in the function
    action_types jsonb,
    action_statuses jsonb,
    total_count bigint
) AS $$
BEGIN
    RETURN QUERY
    WITH filtered_actions AS (
        SELECT
            ga.*,
            -- Pre-build the JSON for related tables
            jsonb_build_object('translations', atype.translations) AS action_types_json,
            jsonb_build_object('translations', astat.translations, 'color_hex', astat.color_hex) AS action_statuses_json,
            COUNT(*) OVER() AS full_count -- Window function to get total count before pagination
        FROM
            agora.government_actions ga
        LEFT JOIN agora.action_types atype ON ga.action_type_id = atype.id
        LEFT JOIN agora.action_statuses astat ON ga.status_id = astat.id
        WHERE
            ga.government_entity_id = p_government_entity_id
            -- The core logic: action must NOT EXIST in the junction table for this promise
            AND NOT EXISTS (
                SELECT 1
                FROM agora.action_promises ap
                WHERE ap.action_id = ga.id AND ap.promise_id = p_promise_id
            )
            -- Apply optional filters
            AND (p_ministry_id IS NULL OR ga.ministry_id = p_ministry_id)
            AND (p_action_type_id IS NULL OR ga.action_type_id = p_action_type_id)
            AND (p_status_id IS NULL OR ga.status_id = p_status_id)
            AND (p_is_active IS NULL OR ga.is_active = p_is_active)
    )
    SELECT
        fa.id,
        fa.slug,
        fa.action_type_id,
        fa.status_id,
        fa.responsible_role_id,
        fa.government_entity_id,
        fa.ministry_id,
        fa.timeline_proposal_date,
        fa.timeline_implementation_date,
        fa.translations,
        fa.is_active,
        fa.action_types_json,
        fa.action_statuses_json,
        fa.full_count
    FROM
        filtered_actions fa
    ORDER BY
        fa.timeline_proposal_date DESC NULLS LAST
    LIMIT
        p_limit
    OFFSET
        p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

-- ====================================================================
-- FUNCTION: Get Unassociated Sources for a Government Action
-- Description: Fetches a paginated and filtered list of sources that
--              are NOT already linked to a specific government action.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_unassociated_sources_for_action(
    p_action_id uuid,
    p_search_text text DEFAULT NULL,
    p_source_type_id text DEFAULT NULL,
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    -- Define the columns to be returned to build a "Source Card"
    id uuid,
    translations jsonb,
    author text,
    published_at timestamp with time zone,
    main_url text,
    credibility_score numeric,
    -- Pre-joined related data as JSON for efficiency
    source_entity jsonb,
    source_type jsonb,
    -- Total count for pagination
    total_count bigint
) AS $$
BEGIN
    RETURN QUERY
    WITH filtered_sources AS (
        SELECT
            s.*,
            -- Pre-build the JSON for related tables
            jsonb_build_object('id', se.id, 'name', se.name) AS source_entity_json,
            jsonb_build_object('id', st.id, 'translations', st.translations) AS source_type_json,
            -- Window function to get total count before pagination
            COUNT(*) OVER() AS full_count
        FROM
            agora.sources s
        LEFT JOIN agora.source_entities se ON s.source_entity_id = se.id
        LEFT JOIN agora.source_types st ON s.type_id = st.id
        WHERE
            s.is_active = true
            -- The core logic: source must NOT EXIST in the junction table for this action
            AND NOT EXISTS (
                SELECT 1
                FROM agora.action_sources asrc
                WHERE asrc.source_id = s.id AND asrc.action_id = p_action_id
            )
            -- Apply optional filters
            AND (p_search_text IS NULL OR (s.translations->'en'->>'title') ILIKE '%' || p_search_text || '%')
            AND (p_source_type_id IS NULL OR s.type_id = p_source_type_id)
    )
    SELECT
        fs.id,
        fs.translations,
        fs.author,
        fs.published_at,
        fs.main_url,
        fs.credibility_score,
        fs.source_entity_json,
        fs.source_type_json,
        fs.full_count
    FROM
        filtered_sources fs
    ORDER BY
        fs.published_at DESC NULLS LAST
    LIMIT
        p_limit
    OFFSET
        p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_unassociated_sources_for_action(uuid, text, text, integer, integer) IS 'Fetches a list of sources not yet associated with a given government action, with filtering and pagination.';

-- ====================================================================
-- FUNCTION: Get Unassociated Sources for a Promise
-- Description: Fetches a paginated and filtered list of sources that
--              are NOT already linked to a specific promise.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_unassociated_sources_for_promise(
    p_promise_id uuid,
    p_search_text text DEFAULT NULL,
    p_source_type_id text DEFAULT NULL,
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    -- Define the columns to be returned to build a "Source Card"
    id uuid,
    translations jsonb,
    author text,
    published_at timestamp with time zone,
    main_url text,
    credibility_score numeric,
    -- Pre-joined related data as JSON for efficiency
    source_entity jsonb,
    source_type jsonb,
    -- Total count for pagination
    total_count bigint
) AS $$
BEGIN
    RETURN QUERY
    WITH filtered_sources AS (
        SELECT
            s.*,
            -- Pre-build the JSON for related tables
            jsonb_build_object('id', se.id, 'name', se.name) AS source_entity_json,
            jsonb_build_object('id', st.id, 'translations', st.translations) AS source_type_json,
            -- Window function to get total count before pagination
            COUNT(*) OVER() AS full_count
        FROM
            agora.sources s
        LEFT JOIN agora.source_entities se ON s.source_entity_id = se.id
        LEFT JOIN agora.source_types st ON s.type_id = st.id
        WHERE
            s.is_active = true
            -- The core logic: source must NOT EXIST in the junction table for this promise
            AND NOT EXISTS (
                SELECT 1
                FROM agora.promise_sources psrc
                WHERE psrc.source_id = s.id AND psrc.promise_id = p_promise_id
            )
            -- Apply optional filters
            AND (p_search_text IS NULL OR (s.translations->'en'->>'title') ILIKE '%' || p_search_text || '%')
            AND (p_source_type_id IS NULL OR s.type_id = p_source_type_id)
    )
    SELECT
        fs.id,
        fs.translations,
        fs.author,
        fs.published_at,
        fs.main_url,
        fs.credibility_score,
        fs.source_entity_json,
        fs.source_type_json,
        fs.full_count
    FROM
        filtered_sources fs
    ORDER BY
        fs.published_at DESC NULLS LAST
    LIMIT
        p_limit
    OFFSET
        p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_unassociated_sources_for_promise(uuid, text, text, integer, integer) IS 'Fetches a list of sources not yet associated with a given promise, with filtering and pagination.';

-- ====================================================================
-- SCRIPT: CREATE FUNCTION FOR ORDERED FILTERABLE GOVERNMENTS
-- Purpose: Creates a performant RPC function that fetches all government
--          entities and their mandates, ordered by the user's country
--          and with a flag for the current active mandate.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_ordered_filterable_governments(
    p_country_code text
)
RETURNS TABLE (
    government_id uuid,
    government_slug text,
    government_translations jsonb,
    country_code character(2),
    mandate_id uuid,
    mandate_slug text,
    mandate_translations jsonb,
    is_current_mandate boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ge.id AS government_id,
        ge.slug AS government_slug,
        ge.translations AS government_translations,
        ge.country_code,
        m.id AS mandate_id,
        m.slug AS mandate_slug,
        m.translations AS mandate_translations,
        -- This CASE statement dynamically determines if the mandate is currently active.
        CASE
            WHEN (m.end_date IS NULL OR m.end_date >= NOW()) THEN true
            ELSE false
        END AS is_current_mandate
    FROM
        agora.government_entities AS ge
    -- INNER JOIN ensures we only get entities that have at least one mandate.
    INNER JOIN
        agora.mandates AS m ON ge.id = m.government_entity_id
    WHERE
        ge.is_active = true
    ORDER BY
        -- 1. Prioritize entities that match the user's detected country code.
        CASE WHEN ge.country_code = UPPER(p_country_code) THEN 0 ELSE 1 END,
        -- 2. Then, sort by the government's name alphabetically.
        ge.name ASC,
        -- 3. Finally, sort the mandates for each government by start date, newest first.
        m.start_date DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ====================================================================
-- FUNCTION: Get Complete Budget Details for UI (V3 - Corrected Totals & Allocations)
-- Description: Corrects all aggregation logic for budgeted, allocated, and spent totals
--              at both the budget-wide and per-category level.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_budget_dashboard_data(p_budget_slug text)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
    v_budget_id uuid;
BEGIN
    SELECT id INTO v_budget_id FROM agora.budgets WHERE slug = p_budget_slug;
    IF NOT FOUND THEN RETURN NULL; END IF;

    SELECT
        jsonb_build_object(
            'id', b.id,
            'slug', b.slug,
            'year', b.year,
            'translations', b.translations,
            'status', (SELECT jsonb_build_object('id', bs.id, 'translations', bs.translations) FROM agora.budget_statuses bs WHERE bs.id = b.status_id),
            'government_entity', (SELECT jsonb_build_object('id', ge.id, 'name', ge.name, 'slug', ge.slug) FROM agora.government_entities ge WHERE ge.id = b.government_entity_id),

            -- SECTION: Aggregated Totals for Header Cards (All calculations are now live)
            'totals', jsonb_build_object(
                'total_budgeted', (SELECT COALESCE(SUM(bsi.budgeted_amount), 0) FROM agora.budget_spending_items bsi WHERE bsi.budget_id = v_budget_id),
                'total_allocated', (
                    SELECT COALESCE(SUM(ba.allocated_amount), 0)
                    FROM agora.budget_allocations ba
                    WHERE ba.spending_item_id IN (SELECT id FROM agora.budget_spending_items WHERE budget_id = v_budget_id)
                ),
                'total_spent', (
                    SELECT COALESCE(SUM(bse.amount), 0)
                    FROM agora.budget_spending_events bse
                    WHERE bse.spending_item_id IN (SELECT id FROM agora.budget_spending_items WHERE budget_id = v_budget_id)
                )
            ),

            -- SECTION: Data grouped by category
            'categories', (
                SELECT COALESCE(jsonb_agg(category_data ORDER BY total_budgeted_in_category DESC), '[]'::jsonb)
                FROM (
                    SELECT
                        cat.id AS category_id,
                        cat.translations AS category_translations,
                        -- Aggregated totals for this specific category
                        SUM(bsi.budgeted_amount) AS total_budgeted_in_category,
                        (
                            SELECT COALESCE(SUM(ba.allocated_amount), 0)
                            FROM agora.budget_allocations ba
                            WHERE ba.spending_item_id IN (SELECT id FROM agora.budget_spending_items WHERE budget_id = v_budget_id AND category_id = cat.id)
                        ) AS total_allocated_in_category,
                        (
                            SELECT COALESCE(SUM(bse.amount), 0)
                            FROM agora.budget_spending_events bse
                            WHERE bse.spending_item_id IN (SELECT id FROM agora.budget_spending_items WHERE budget_id = v_budget_id AND category_id = cat.id)
                        ) AS total_spent_in_category,
                        -- Nested list of spending items within this category
                        jsonb_agg(
                            jsonb_build_object(
                                'id', bsi.id,
                                'slug', bsi.slug,
                                'translations', bsi.translations,
                                'budgeted_amount', bsi.budgeted_amount,
                                'total_allocated', (SELECT COALESCE(SUM(allocated_amount), 0) FROM agora.budget_allocations WHERE spending_item_id = bsi.id),
                                'total_spent', (SELECT COALESCE(SUM(amount), 0) FROM agora.budget_spending_events WHERE spending_item_id = bsi.id),
                                'ministry', (SELECT jsonb_build_object('id', min.id, 'translations', min.translations) FROM agora.ministries min WHERE min.id = bsi.ministry_id)
                            ) ORDER BY bsi.budgeted_amount DESC
                        ) AS spending_items
                    FROM
                        agora.budget_spending_items bsi
                    JOIN
                        agora.budget_categories cat ON bsi.category_id = cat.id
                    WHERE
                        bsi.budget_id = v_budget_id
                    GROUP BY
                        cat.id, cat.translations
                ) AS category_data
            )
        )
    INTO result
    FROM
        agora.budgets b
    WHERE
        b.id = v_budget_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;
-- ====================================================================
-- FUNCTION 2 (NEW): Compare Two Budgets by Slug
-- Description: Fetches aggregated spending data for two budgets,
--              grouped by category, for a side-by-side comparison view.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.compare_budgets_by_slug(p_slug_a text, p_slug_b text)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    WITH
    budget_a AS (SELECT id, year FROM agora.budgets WHERE slug = p_slug_a),
    budget_b AS (SELECT id, year FROM agora.budgets WHERE slug = p_slug_b),
    -- Aggregate data for all categories across both budgets
    all_categories AS (
        SELECT
            cat.id AS category_id,
            cat.translations AS category_translations,
            -- Totals for Budget A
            COALESCE(SUM(bsi.budgeted_amount) FILTER (WHERE bsi.budget_id = (SELECT id FROM budget_a)), 0) AS budgeted_a,
            COALESCE(SUM((SELECT SUM(amount) FROM agora.budget_spending_events WHERE spending_item_id = bsi.id)) FILTER (WHERE bsi.budget_id = (SELECT id FROM budget_a)), 0) AS spent_a,
            -- Totals for Budget B
            COALESCE(SUM(bsi.budgeted_amount) FILTER (WHERE bsi.budget_id = (SELECT id FROM budget_b)), 0) AS budgeted_b,
            COALESCE(SUM((SELECT SUM(amount) FROM agora.budget_spending_events WHERE spending_item_id = bsi.id)) FILTER (WHERE bsi.budget_id = (SELECT id FROM budget_b)), 0) AS spent_b
        FROM
            agora.budget_spending_items bsi
        JOIN
            agora.budget_categories cat ON bsi.category_id = cat.id
        WHERE
            bsi.budget_id IN ((SELECT id FROM budget_a), (SELECT id FROM budget_b))
        GROUP BY
            cat.id, cat.translations
    )
    SELECT
        jsonb_build_object(
            'budget_a', (SELECT jsonb_build_object('slug', p_slug_a, 'year', year) FROM budget_a),
            'budget_b', (SELECT jsonb_build_object('slug', p_slug_b, 'year', year) FROM budget_b),
            'comparison_data', (SELECT jsonb_agg(ac) FROM all_categories ac)
        )
    INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- ====================================================================
-- FUNCTION: Get Sources by Mandate Association (Corrected with Slug)
-- Description: Fetches a paginated list of all sources that are directly
--              or indirectly associated with a given set of mandates.
-- FIX:         Adds the 'slug' column to the return data.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_sources_by_mandate(
    p_mandate_ids uuid[] DEFAULT NULL,
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    -- Define the columns to be returned for a "Source Card"
    id uuid,
    slug text,
    translations jsonb,
    author text,
    published_at timestamp with time zone,
    main_url text,
    credibility_score numeric,
    -- Pre-joined related data as JSON for efficiency
    source_entity jsonb,
    source_type jsonb,
    -- Association counts
    promise_count bigint,
    action_count bigint,
    total_associations bigint,
    -- Total count for pagination
    total_count bigint
) AS $$
BEGIN
    RETURN QUERY
    WITH filtered_sources AS (
        SELECT
            s.*,
            jsonb_build_object('id', se.id, 'name', se.name) AS source_entity_json,
            jsonb_build_object('id', st.id, 'translations', st.translations) AS source_type_json,
            COUNT(*) OVER() AS full_count
        FROM
            agora.sources s
        LEFT JOIN agora.source_entities se ON s.source_entity_id = se.id
        LEFT JOIN agora.source_types st ON s.type_id = st.id
        WHERE
            s.is_active = true
            AND (
                p_mandate_ids IS NULL OR
                EXISTS (
                    SELECT 1 FROM agora.promise_sources ps JOIN agora.promises p ON ps.promise_id = p.id WHERE ps.source_id = s.id AND p.mandate_id = ANY(p_mandate_ids)
                    UNION ALL
                    SELECT 1 FROM agora.action_sources acs JOIN agora.government_actions ga ON acs.action_id = ga.id WHERE acs.source_id = s.id AND ga.mandate_id = ANY(p_mandate_ids)
                    UNION ALL
                    SELECT 1 FROM agora.report_sources rs JOIN agora.reports r ON rs.report_id = r.id WHERE rs.source_id = s.id AND r.mandate_id = ANY(p_mandate_ids)
                    UNION ALL
                    SELECT 1 FROM agora.budget_spending_events bse JOIN agora.budget_spending_items bsi ON bse.spending_item_id = bsi.id JOIN agora.budgets b ON bsi.budget_id = b.id WHERE bse.source_id = s.id AND b.mandate_id = ANY(p_mandate_ids)
                )
            )
    )
    SELECT
        fs.id,
        fs.slug,
        fs.translations,
        fs.author,
        fs.published_at,
        fs.main_url,
        fs.credibility_score,
        fs.source_entity_json,
        fs.source_type_json,
        -- Count promises associated with this source
        COALESCE((
            SELECT COUNT(*) FROM agora.promise_sources ps 
            JOIN agora.promises p ON ps.promise_id = p.id 
            WHERE ps.source_id = fs.id
        ), 0) as promise_count,
        -- Count actions associated with this source
        COALESCE((
            SELECT COUNT(*) FROM agora.action_sources acs 
            JOIN agora.government_actions ga ON acs.action_id = ga.id 
            WHERE acs.source_id = fs.id
        ), 0) as action_count,
        -- Total associations (promises + actions + reports + budget events)
        COALESCE((
            SELECT COUNT(*) FROM agora.promise_sources ps WHERE ps.source_id = fs.id
        ), 0) + COALESCE((
            SELECT COUNT(*) FROM agora.action_sources acs WHERE acs.source_id = fs.id
        ), 0) + COALESCE((
            SELECT COUNT(*) FROM agora.report_sources rs WHERE rs.source_id = fs.id
        ), 0) + COALESCE((
            SELECT COUNT(*) FROM agora.budget_spending_events bse WHERE bse.source_id = fs.id
        ), 0) as total_associations,
        fs.full_count
    FROM
        filtered_sources fs
    ORDER BY
        fs.published_at DESC NULLS LAST
    LIMIT
        p_limit
    OFFSET
        p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_sources_by_mandate(uuid[], integer, integer) IS 'Fetches all sources linked to content within a specific set of mandates, now including the source slug.';
-- ====================================================================
-- FUNCTION: Get Full Source Details and All Linked Items by Slug
-- Description: Fetches a single source by its slug and aggregates all
--              promises, actions, and reports that link to it into
--              a single, comprehensive JSONB object.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_source_details_by_slug(p_source_slug text)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
    v_source_id uuid;
BEGIN
    -- First, find the source ID from the slug to use in subqueries
    SELECT id INTO v_source_id FROM agora.sources WHERE slug = p_source_slug;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    -- Now, build the comprehensive JSON object
    SELECT
        jsonb_build_object(
            'id', s.id,
            'slug', s.slug,
            'translations', s.translations,
            'author', s.author,
            'published_at', s.published_at,
            'main_url', s.main_url,
            'credibility_score', s.credibility_score,
            'is_official_document', s.is_official_document,
            'archived_url', s.archived_url,
            'archive_status', s.archive_status,
            'source_entity', (
                SELECT jsonb_build_object(
                    'id', se.id,
                    'name', se.name,
                    'logo_url', se.logo_url,
                    'website_url', se.website_url
                )
                FROM agora.source_entities se WHERE se.id = s.source_entity_id
            ),
            'source_type', (
                SELECT t.translations FROM agora.source_types t WHERE t.id = s.type_id
            ),

            -- SECTION: Aggregate all items linked to this source
            'linked_items', jsonb_build_object(
                'promises', (
                    SELECT COALESCE(jsonb_agg(
                        jsonb_build_object(
                            'id', p.id,
                            'slug', p.slug,
                            'translations', p.translations,
                            'mandate_id', p.mandate_id
                        )
                    ), '[]'::jsonb)
                    FROM agora.promise_sources ps
                    JOIN agora.promises p ON ps.promise_id = p.id
                    WHERE ps.source_id = v_source_id AND p.is_active = true
                ),
                'actions', (
                    SELECT COALESCE(jsonb_agg(
                        jsonb_build_object(
                            'id', ga.id,
                            'slug', ga.slug,
                            'translations', ga.translations,
                            'mandate_id', ga.mandate_id
                        )
                    ), '[]'::jsonb)
                    FROM agora.action_sources acs
                    JOIN agora.government_actions ga ON acs.action_id = ga.id
                    WHERE acs.source_id = v_source_id AND ga.is_active = true
                ),
                'reports', ( 
                    SELECT COALESCE(jsonb_agg(
                        jsonb_build_object(
                            'id', r.id,
                            'slug', r.slug,
                            'translations', r.translations,
                            'mandate_id', r.mandate_id
                        )
                    ), '[]'::jsonb)
                    FROM agora.report_sources rs
                    JOIN agora.reports r ON rs.report_id = r.id
                    WHERE rs.source_id = v_source_id AND r.is_active = true
                ),
                'urls', (
                    SELECT COALESCE(jsonb_agg(
                        jsonb_build_object(
                            'id', su.id,
                            'url', su.url,
                            'title', su.title,
                            'is_main', su.is_main
                        )
                    ), '[]'::jsonb)
                    FROM agora.source_urls su
                    WHERE su.source_id = v_source_id
                    ORDER BY su.is_main DESC, su.created_at ASC
                )
            )
        )
    INTO result
    FROM
        agora.sources s
    WHERE
        s.id = v_source_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_source_details_by_slug(text) IS 'Returns a full, nested JSONB object for a single source by its SLUG, including all promises, actions, and reports that reference it.';

-- CHANGE: Update the function comment to reflect the new parameter type.
COMMENT ON FUNCTION agora.get_budget_dashboard_data(text) IS 'Returns a full, nested JSONB object for a single budget by its SLUG, including all its children and aggregated totals.';

-- SCRIPT 1B: CREATE SEARCH INDEX AUTOMATION

-- Function to update the index for a PROMISE
CREATE OR REPLACE FUNCTION agora.update_search_index_for_promise()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO agora.search_index (target_id, target_table, government_entity_id, mandate_id, content)
    VALUES (
        NEW.id,
        'promises',
        NEW.government_entity_id,
        NEW.mandate_id,
        -- Combine all relevant text into a single field
        concat_ws(' ', NEW.translations->'en'->>'wording', NEW.translations->'en'->>'context_description')
    )
    ON CONFLICT (target_id, target_table) DO UPDATE
    SET content = EXCLUDED.content,
        government_entity_id = EXCLUDED.government_entity_id,
        mandate_id = EXCLUDED.mandate_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for the PROMISE table
CREATE OR REPLACE TRIGGER on_promise_change
    AFTER INSERT OR UPDATE ON agora.promises
    FOR EACH ROW EXECUTE FUNCTION agora.update_search_index_for_promise();

-- INSTRUCTION FOR AI: You must now create similar functions and triggers for:
-- agora.government_actions (using its title and description)
-- agora.reports (using its title and brief description)
-- agora.people (using their full_name, preferred_name, and bio)

-- SCRIPT: CREATE FUNCTION TO GET SOURCE INGESTION STATUS
-- ====================================================================
-- FUNCTION: Get Source Ingestion Status (Corrected)
-- Description: Fetches all sources and provides a status on whether
--              their content has been chunked.
-- FIX:         Uses the now-existing 'created_at' column for sorting.
-- ====================================================================

CREATE OR REPLACE FUNCTION agora.get_sources_with_chunk_status()
RETURNS TABLE (
    id uuid,
    main_url text,
    translations jsonb,
    source_entity_name text,
    created_at timestamptz,
    chunk_count bigint,
    is_processed boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.main_url,
        s.translations,
        se.name AS source_entity_name,
        s.created_at,
        COUNT(dc.id) AS chunk_count,
        (COUNT(dc.id) > 0) AS is_processed
    FROM
        agora.sources s
    LEFT JOIN
        agora.source_entities se ON s.source_entity_id = se.id
    LEFT JOIN
        agora.document_chunks dc ON s.id = dc.source_id
    GROUP BY
        s.id, se.name
    ORDER BY
        s.created_at DESC; -- Now correctly orders by the creation date
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_sources_with_chunk_status() IS 'Returns all sources with their document chunk processing status.';

-- Supabase buckets
agora_source_documents
agora_report_attachments

-- RLS Policies for the bucket:
DROP POLICY IF EXISTS "Allow authenticated read access to documents" ON storage.objects;
CREATE POLICY "Allow all read access to documents" ON storage.objects
    FOR SELECT USING (bucket_id = 'agora_source_documents');

CREATE POLICY "Allow authenticated insert documents" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'agora_source_documents' AND auth.role() = 'authenticated');

--Schema grants
GRANT USAGE ON SCHEMA agora TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA agora TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA agora TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA agora TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA agora GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA agora GRANT ALL ON ROUTINES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA agora GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;


--Lookup table data
-- ====================================================================
-- SCRIPT: POPULATE AGORA GOVERNMENT LEVELS
-- Purpose: Inserts the hierarchical government levels into the lookup table
--          with their respective English and Portuguese translations.
-- ====================================================================
INSERT INTO agora.government_levels (id, parent_level_id, translations)
VALUES
    -- Top Level
    ('country', NULL, '{
        "en": {"name": "Country"},
        "pt": {"name": "País"}
    }'),

    -- Children of 'country'
    ('region', 'country', '{
        "en": {"name": "Region"},
        "pt": {"name": "Região"}
    }'),

    -- Children of 'region'
    ('district', 'region', '{
        "en": {"name": "District"},
        "pt": {"name": "Distrito"}
    }'),

    -- Children of 'district'
    ('municipality', 'district', '{
        "en": {"name": "Municipality"},
        "pt": {"name": "Concelho"}
    }'),

    -- Children of 'municipality'
    ('parish', 'municipality', '{
        "en": {"name": "Parish"},
        "pt": {"name": "Freguesia"}
    }')
END $$;

-- ====================================================================
-- SCRIPT: POPULATE AGORA PROMISE STATUSES (with Icons)
-- Purpose: Inserts/updates the lookup values for promise statuses,
--          including emoji icons, color codes, and translations.
-- ====================================================================

DO $$
BEGIN

-- promises_statuses
INSERT INTO agora.promise_statuses (id, color_hex, icon, translations)
VALUES
    -- Neutral / Starting Status
    ('NOT_STARTED', '#6c757d', '⏳', '{
        "en": {"name": "Not Started"},
        "pt": {"name": "Não Iniciada"}
    }'),

    -- Active / In-Progress Status
    ('IN_PROGRESS', '#007bff', '⚙️', '{
        "en": {"name": "In Progress"},
        "pt": {"name": "Em Andamento"}
    }'),

    -- Warning / At-Risk Status
    ('STALLED', '#ffc107', '⚠️', '{
        "en": {"name": "Stalled"},
        "pt": {"name": "Parada"}
    }'),

    -- Success Statuses
    ('FULFILLED', '#28a745', '✅', '{
        "en": {"name": "Fulfilled"},
        "pt": {"name": "Cumprida"}
    }'),
    ('PARTIALLY_FULFILLED', '#17a2b8', '🟢', '{
        "en": {"name": "Partially Fulfilled"},
        "pt": {"name": "Parcialmente Cumprida"}
    }'),

    -- Failure Status
    ('BROKEN', '#dc3545', '❌', '{
        "en": {"name": "Broken"},
        "pt": {"name": "Não Cumprida"}
    }'),

    -- Archived / Irrelevant Status
    ('OBSOLETE', '#343a40', '🗄️', '{
        "en": {"name": "Obsolete"},
        "pt": {"name": "Obsoleta"}
    }')

INSERT INTO agora.source_entity_types (id, translations)
VALUES
    ('MEDIA_GROUP',         '{"en": {"name": "Media Group"}, "pt": {"name": "Grupo de Média"}}'),
    ('TV_CHANNEL',          '{"en": {"name": "TV Channel"}, "pt": {"name": "Canal de TV"}}'),
    ('NEWSPAPER',           '{"en": {"name": "Newspaper"}, "pt": {"name": "Jornal"}}'),
    ('RADIO_STATION',       '{"en": {"name": "Radio Station"}, "pt": {"name": "Estação de Rádio"}}'),
    ('WEBSITE',             '{"en": {"name": "Website"}, "pt": {"name": "Website"}}'),
    ('GOVERNMENT_BODY',     '{"en": {"name": "Government Body"}, "pt": {"name": "Orgão Governamental"}}'),
    ('ACADEMIC_INSTITUTION','{"en": {"name": "Academic Institution"}, "pt": {"name": "Instituição Académica"}}'),
    ('NGO',                 '{"en": {"name": "Non-Governmental Organization"}, "pt": {"name": "Organização Não Governamental (ONG)"}}')

INSERT INTO agora.source_types (id, translations)
VALUES
    ('ARTICLE',             '{"en": {"name": "News Article"}, "pt": {"name": "Artigo de Notícias"}}'),
    ('INTERVIEW',           '{"en": {"name": "Interview"}, "pt": {"name": "Entrevista"}}'),
    ('VIDEO',               '{"en": {"name": "Video"}, "pt": {"name": "Vídeo"}}'),
    ('AUDIO',               '{"en": {"name": "Audio / Podcast"}, "pt": {"name": "Áudio / Podcast"}}'),
    ('OFFICIAL_PUBLICATION','{"en": {"name": "Official Publication"}, "pt": {"name": "Publicação Oficial"}}'),
    ('ACADEMIC_PAPER',      '{"en": {"name": "Academic Paper"}, "pt": {"name": "Artigo Académico"}}'),
    ('PRESS_RELEASE',       '{"en": {"name": "Press Release"}, "pt": {"name": "Comunicado de Imprensa"}}'),
    ('REPORT',              '{"en": {"name": "Report"}, "pt": {"name": "Relatório"}}'),
    ('SOCIAL_MEDIA_POST',   '{"en": {"name": "Social Media Post"}, "pt": {"name": "Publicação em Rede Social"}}'),
    ('PHOTO',               '{"en": {"name": "Photograph"}, "pt": {"name": "Fotografia"}}')

INSERT INTO agora.source_relationship_types (id, effect, translations)
VALUES
    -- Effect: 1=Positive, 0=Neutral, -1=Negative
    ('CONFIRMS', 1,  '{"en": {"name": "Confirms", "description": "Provides evidence that supports the claim."}, "pt": {"name": "Confirma", "description": "Fornece evidências que apoiam a alegação."}}'),
    ('DISPUTES', -1, '{"en": {"name": "Disputes", "description": "Provides evidence that contradicts the claim."}, "pt": {"name": "Contesta", "description": "Fornece evidências que contradizem a alegação."}}'),
    ('PROVIDES_CONTEXT', 0, '{"en": {"name": "Provides Context", "description": "Gives background information without confirming or denying."}, "pt": {"name": "Fornece Contexto", "description": "Dá informação de fundo sem confirmar ou negar."}}'),
    ('CITES', 0, '{"en": {"name": "Cites as Source", "description": "Explicitly cites the other item as a source for its information."}, "pt": {"name": "Cita como Fonte", "description": "Cita explicitamente o outro item como fonte da sua informação."}}'),
    ('UPDATES', 0, '{"en": {"name": "Updates", "description": "Provides newer or updated information on the same topic."}, "pt": {"name": "Atualiza", "description": "Fornece informação mais recente ou atualizada sobre o mesmo tópico."}}')

INSERT INTO agora.action_statuses (id, color_hex, translations)
VALUES
    ('PROPOSED', '#6c757d', '{
        "en": {"name": "Proposed"},
        "pt": {"name": "Proposta"}
    }'),
    ('IN_DEBATE', '#007bff', '{
        "en": {"name": "In Debate"},
        "pt": {"name": "Em Debate"}
    }'),
    ('APPROVED', '#17a2b8', '{
        "en": {"name": "Approved"},
        "pt": {"name": "Aprovada"}
    }'),
    ('IMPLEMENTED', '#28a745', '{
        "en": {"name": "Implemented"},
        "pt": {"name": "Implementada"}
    }'),
    ('REJECTED', '#dc3545', '{
        "en": {"name": "Rejected"},
        "pt": {"name": "Rejeitada"}
    }'),
    ('VETOED', '#b02a37', '{
        "en": {"name": "Vetoed"},
        "pt": {"name": "Vetada"}
    }'),
    ('CANCELED', '#343a40', '{
        "en": {"name": "Canceled"},
        "pt": {"name": "Cancelada"}
    }')

INSERT INTO agora.action_types (id, translations)
VALUES
    ('LAW', '{
        "en": {"name": "Law"},
        "pt": {"name": "Lei"}
    }'),
    ('DECREE_LAW', '{
        "en": {"name": "Decree-Law"},
        "pt": {"name": "Decreto-Lei"}
    }'),
    ('RESOLUTION', '{
        "en": {"name": "Resolution"},
        "pt": {"name": "Resolução"}
    }'),
    ('BUDGET', '{
        "en": {"name": "Budget"},
        "pt": {"name": "Orçamento"}
    }'),
    ('REGULATION', '{
        "en": {"name": "Regulation"},
        "pt": {"name": "Regulamento"}
    }'),
    ('INTERNATIONAL_AGREEMENT', '{
        "en": {"name": "International Agreement"},
        "pt": {"name": "Acordo Internacional"}
    }'),
    ('MINISTERIAL_ORDER', '{
        "en": {"name": "Ministerial Order"},
        "pt": {"name": "Despacho Ministerial"}
    }'),
    ('CONSTITUTIONAL_REVISION', '{
        "en": {"name": "Constitutional Revision"},
        "pt": {"name": "Revisão Constitucional"}
    }')
DO $$
BEGIN

-- ====================================================================
-- SECTION 2.1: POPULATE BUDGET STATUSES
-- ====================================================================
INSERT INTO agora.budget_statuses (id, translations)
VALUES
    ('PROPOSED',        '{"en": {"name": "Proposed"}, "pt": {"name": "Proposto"}}'),
    ('IN_DEBATE',       '{"en": {"name": "In Debate"}, "pt": {"name": "Em Debate"}}'),
    ('APPROVED',        '{"en": {"name": "Approved"}, "pt": {"name": "Aprovado"}}'),
    ('IN_EXECUTION',    '{"en": {"name": "In Execution"}, "pt": {"name": "Em Execução"}}'),
    ('CLOSED',          '{"en": {"name": "Closed"}, "pt": {"name": "Fechado"}}'),
    ('AUDITED',         '{"en": {"name": "Audited"}, "pt": {"name": "Auditado"}}')
ON CONFLICT (id) DO UPDATE SET translations = EXCLUDED.translations;

-- ====================================================================
-- STEP 1: POPULATE FUNDING SOURCE TYPES
-- ====================================================================
INSERT INTO agora.funding_source_types (id, translations)
VALUES
    ('PRIMARY_REVENUE', '{"en": {"name": "Primary Revenue"}, "pt": {"name": "Receita Primária"}}'),
    ('DEDICATED_TAX', '{"en": {"name": "Dedicated Tax"}, "pt": {"name": "Imposto Consignado"}}'),
    ('EXTERNAL_FUND', '{"en": {"name": "External Fund"}, "pt": {"name": "Fundo Externo"}}'),
    ('INTERGOVERNMENTAL_TRANSFER', '{"en": {"name": "Inter-Governmental Transfer"}, "pt": {"name": "Transferência Intergovernamental"}}'),
    ('LOAN', '{"en": {"name": "Loan"}, "pt": {"name": "Empréstimo"}}'),
    ('STATE_ASSET', '{"en": {"name": "State Asset Revenue"}, "pt": {"name": "Receita de Ativos do Estado"}}')
ON CONFLICT (id) DO NOTHING;


-- ====================================================================
-- STEP 2: POPULATE FUNDING SOURCES
-- Description: Creates a master catalog of reusable funding sources.
-- ====================================================================
-- Add a unique constraint to ensure data integrity
ALTER TABLE agora.funding_sources ADD CONSTRAINT funding_sources_type_id_translations_key UNIQUE (type_id, translations);

INSERT INTO agora.funding_sources (type_id, translations)
VALUES
    -- EU Level External Funds
    ('EXTERNAL_FUND', '{"en": {"name": "EU Recovery and Resilience Facility (RRF)"}, "pt": {"name": "Mecanismo de Recuperação e Resiliência (MRR) da UE"}}'::jsonb),
    ('EXTERNAL_FUND', '{"en": {"name": "European Regional Development Fund (ERDF)"}, "pt": {"name": "Fundo Europeu de Desenvolvimento Regional (FEDER)"}}'::jsonb),
    ('EXTERNAL_FUND', '{"en": {"name": "European Social Fund Plus (ESF+)"}, "pt": {"name": "Fundo Social Europeu Mais (FSE+)"}}'::jsonb),
    ('EXTERNAL_FUND', '{"en": {"name": "Cohesion Fund"}, "pt": {"name": "Fundo de Coesão"}}'::jsonb),
    ('EXTERNAL_FUND', '{"en": {"name": "Common Agricultural Policy (CAP) Fund"}, "pt": {"name": "Fundo da Política Agrícola Comum (PAC)"}}'::jsonb),

    -- National Level Primary Revenue
    ('PRIMARY_REVENUE', '{"en": {"name": "Personal Income Tax (IRS)"}, "pt": {"name": "Imposto sobre o Rendimento das Pessoas Singulares (IRS)"}}'::jsonb),
    ('PRIMARY_REVENUE', '{"en": {"name": "Corporate Income Tax (IRC)"}, "pt": {"name": "Imposto sobre o Rendimento das Pessoas Coletivas (IRC)"}}'::jsonb),
    ('PRIMARY_REVENUE', '{"en": {"name": "Value-Added Tax (VAT / IVA)"}, "pt": {"name": "Imposto sobre o Valor Acrescentado (IVA)"}}'::jsonb),
    ('PRIMARY_REVENUE', '{"en": {"name": "Fuel & Petroleum Tax (ISP)"}, "pt": {"name": "Imposto sobre os Produtos Petrolíferos e Energéticos (ISP)"}}'::jsonb),
    ('PRIMARY_REVENUE', '{"en": {"name": "Social Contributions"}, "pt": {"name": "Contribuições Sociais"}}'::jsonb),
    ('PRIMARY_REVENUE', '{"en": {"name": "General Government Revenue"}, "pt": {"name": "Receita Geral do Estado"}}'::jsonb),

    -- National Level Dedicated Taxes
    ('DEDICATED_TAX', '{"en": {"name": "Non-Alcoholic Beverages Tax"}, "pt": {"name": "Imposto sobre Bebidas Não Alcoólicas"}}'::jsonb),
    ('DEDICATED_TAX', '{"en": {"name": "Extraordinary Energy Sector Contribution (CESE)"}, "pt": {"name": "Contribuição Extraordinária sobre o Setor Energético (CESE)"}}'::jsonb),
    ('DEDICATED_TAX', '{"en": {"name": "Contribution on Banking Sector"}, "pt": {"name": "Contribuição sobre o Setor Bancário"}}'::jsonb),

    -- National Level Transfers (as a source type)
    ('INTERGOVERNMENTAL_TRANSFER', '{"en": {"name": "National Transfer to Municipalities"}, "pt": {"name": "Transferência Nacional para Municípios"}}'::jsonb),
    ('INTERGOVERNMENTAL_TRANSFER', '{"en": {"name": "National Transfer to Autonomous Regions"}, "pt": {"name": "Transferência Nacional para Regiões Autónomas"}}'::jsonb)

-- ====================================================================
-- SCRIPT 1: FIX AND POPULATE AGORA MASTER BUDGET CATEGORIES (Corrected)
-- Purpose: Populates the dependency table 'budget_category_types' and
--          then inserts the hierarchical chart of accounts.
-- ====================================================================

-- Use a DO block to ensure the prerequisite data is inserted transactionally.
DO $$
BEGIN

-- ====================================================================
-- STEP 1: SCHEMA FIX
-- ====================================================================
-- Add a UNIQUE constraint on the combination of parent_id and translations.
-- A category name should only appear once under a given parent.
ALTER TABLE agora.budget_categories
    ADD CONSTRAINT budget_categories_parent_id_translations_key UNIQUE NULLS NOT DISTINCT (parent_category_id, translations);
EXCEPTION
    WHEN duplicate_object THEN
        RAISE NOTICE 'Constraint budget_categories_parent_id_translations_key already exists, skipping.';
END
$$;

-- ====================================================================
-- STEP 2: DATA POPULATION
-- ====================================================================
WITH
-- This is the critical first step: populate the dependency table.
inserted_types AS (
    INSERT INTO agora.budget_category_types (id, translations)
    VALUES
        ('SPENDING', '{"en": {"name": "Spending"}, "pt": {"name": "Despesa"}}'::jsonb),
        ('FUNDING', '{"en": {"name": "Funding"}, "pt": {"name": "Receita"}}'::jsonb)
    ON CONFLICT (id) DO NOTHING
),
spending_parents AS (
    INSERT INTO agora.budget_categories (type_id, translations)
    VALUES
        ('SPENDING', '{"en": {"name": "General Public Services"}, "pt": {"name": "Serviços Públicos Gerais"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Defence"}, "pt": {"name": "Defesa"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Public Order and Safety"}, "pt": {"name": "Ordem e Segurança Pública"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Economic Affairs"}, "pt": {"name": "Assuntos Económicos"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Environmental Protection"}, "pt": {"name": "Proteção Ambiental"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Housing and Community Amenities"}, "pt": {"name": "Habitação e Serviços Comunitários"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Health"}, "pt": {"name": "Saúde"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Recreation, Culture and Religion"}, "pt": {"name": "Lazer, Cultura e Religião"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Education"}, "pt": {"name": "Educação"}}'::jsonb),
        ('SPENDING', '{"en": {"name": "Social Protection"}, "pt": {"name": "Proteção Social"}}'::jsonb)
    ON CONFLICT (parent_category_id, translations) DO NOTHING
    RETURNING id, (translations->'en'->>'name') as name
),
spending_children AS (
    INSERT INTO agora.budget_categories (type_id, parent_category_id, translations)
    SELECT
        'SPENDING',
        (SELECT id FROM spending_parents WHERE name = v.parent_name),
        v.translations
    FROM (VALUES
        ('General Public Services', '{"en": {"name": "Executive and Legislative Organs"}, "pt": {"name": "Órgãos Executivos e Legislativos"}}'::jsonb),
        ('General Public Services', '{"en": {"name": "Financial and Fiscal Affairs"}, "pt": {"name": "Assuntos Financeiros e Fiscais"}}'::jsonb),
        ('General Public Services', '{"en": {"name": "Foreign Affairs"}, "pt": {"name": "Relações Externas"}}'::jsonb),
        ('General Public Services', '{"en": {"name": "Public Debt Transactions"}, "pt": {"name": "Transações da Dívida Pública"}}'::jsonb),
        ('General Public Services', '{"en": {"name": "Transfers between Government Levels"}, "pt": {"name": "Transferências entre Níveis de Governo"}}'::jsonb),
        ('Defence', '{"en": {"name": "Military Defence"}, "pt": {"name": "Defesa Militar"}}'::jsonb),
        ('Public Order and Safety', '{"en": {"name": "Police Services"}, "pt": {"name": "Serviços de Polícia"}}'::jsonb),
        ('Public Order and Safety', '{"en": {"name": "Fire-Protection Services"}, "pt": {"name": "Serviços de Proteção Civil (Incêndios)"}}'::jsonb),
        ('Public Order and Safety', '{"en": {"name": "Law Courts"}, "pt": {"name": "Tribunais"}}'::jsonb),
        ('Public Order and Safety', '{"en": {"name": "Prisons"}, "pt": {"name": "Prisões"}}'::jsonb),
        ('Economic Affairs', '{"en": {"name": "General Economic and Labour Affairs"}, "pt": {"name": "Assuntos Económicos e Laborais Gerais"}}'::jsonb),
        ('Economic Affairs', '{"en": {"name": "Agriculture, Forestry, Fishing"}, "pt": {"name": "Agricultura, Florestas e Pescas"}}'::jsonb),
        ('Economic Affairs', '{"en": {"name": "Fuel and Energy"}, "pt": {"name": "Combustíveis e Energia"}}'::jsonb),
        ('Economic Affairs', '{"en": {"name": "Transport"}, "pt": {"name": "Transportes"}}'::jsonb),
        ('Health', '{"en": {"name": "Hospital Services"}, "pt": {"name": "Serviços Hospitalares"}}'::jsonb),
        ('Health', '{"en": {"name": "Out-patient and Primary Care"}, "pt": {"name": "Serviços Ambulatórios e Cuidados Primários"}}'::jsonb),
        ('Health', '{"en": {"name": "Public Health Services"}, "pt": {"name": "Serviços de Saúde Pública"}}'::jsonb),
        ('Education', '{"en": {"name": "Pre-primary and Primary Education"}, "pt": {"name": "Educação Pré-escolar e Ensino Básico"}}'::jsonb),
        ('Education', '{"en": {"name": "Secondary Education"}, "pt": {"name": "Ensino Secundário"}}'::jsonb),
        ('Education', '{"en": {"name": "Tertiary Education (Higher Education)"}, "pt": {"name": "Ensino Superior"}}'::jsonb),
        ('Education', '{"en": {"name": "Science and Research"}, "pt": {"name": "Ciência e Investigação"}}'::jsonb),
        ('Social Protection', '{"en": {"name": "Sickness and Disability"}, "pt": {"name": "Doença e Incapacidade"}}'::jsonb),
        ('Social Protection', '{"en": {"name": "Old Age (Pensions)"}, "pt": {"name": "Terceira Idade (Pensões)"}}'::jsonb),
        ('Social Protection', '{"en": {"name": "Family and Children"}, "pt": {"name": "Família e Crianças"}}'::jsonb),
        ('Social Protection', '{"en": {"name": "Unemployment"}, "pt": {"name": "Desemprego"}}'::jsonb),
        ('Social Protection', '{"en": {"name": "Social Exclusion n.e.c."}, "pt": {"name": "Exclusão Social n.e."}}'::jsonb)
    ) AS v(parent_name, translations)
    ON CONFLICT (parent_category_id, translations) DO NOTHING
),
funding_parents AS (
    INSERT INTO agora.budget_categories (type_id, translations)
    VALUES
        ('FUNDING', '{"en": {"name": "Tax Revenue"}, "pt": {"name": "Receita de Impostos"}}'::jsonb),
        ('FUNDING', '{"en": {"name": "Non-Tax Revenue"}, "pt": {"name": "Receita Não Fiscal"}}'::jsonb),
        ('FUNDING', '{"en": {"name": "External & Financial Revenue"}, "pt": {"name": "Receita Externa e Financeira"}}'::jsonb)
    ON CONFLICT (parent_category_id, translations) DO UPDATE SET type_id = EXCLUDED.type_id
    RETURNING id, (translations->'en'->>'name') as name
)
INSERT INTO agora.budget_categories (type_id, parent_category_id, translations)
SELECT
    'FUNDING',
    (SELECT id FROM funding_parents WHERE name = v.parent_name),
    v.translations
FROM (VALUES
    ('Tax Revenue', '{"en": {"name": "Taxes on Income, Profits and Capital Gains"}, "pt": {"name": "Impostos sobre o Rendimento, Lucros e Mais-valias"}}'::jsonb),
    ('Tax Revenue', '{"en": {"name": "Taxes on Goods and Services (VAT, etc.)"}, "pt": {"name": "Impostos sobre Bens e Serviços (IVA, etc.)"}}'::jsonb),
    ('Tax Revenue', '{"en": {"name": "Taxes on Property"}, "pt": {"name": "Impostos sobre a Propriedade"}}'::jsonb),
    ('Non-Tax Revenue', '{"en": {"name": "Social Contributions"}, "pt": {"name": "Contribuições Sociais"}}'::jsonb),
    ('Non-Tax Revenue', '{"en": {"name": "Sales of Goods and Services"}, "pt": {"name": "Venda de Bens e Serviços"}}'::jsonb),
    ('Non-Tax Revenue', '{"en": {"name": "Fines, Penalties and Forfeits"}, "pt": {"name": "Multas, Penalidades e Confiscos"}}'::jsonb),
    ('External & Financial Revenue', '{"en": {"name": "EU Funds"}, "pt": {"name": "Fundos da UE"}}'::jsonb),
    ('External & Financial Revenue', '{"en": {"name": "Loans and Debt Issuance"}, "pt": {"name": "Empréstimos e Emissão de Dívida"}}'::jsonb)
) AS v(parent_name, translations)
ON CONFLICT (parent_category_id, translations) DO NOTHING;

UPDATE agora.budget_statuses
SET
    color_hex = CASE id
        WHEN 'PROPOSED'     THEN '#6c757d' -- Neutral Grey
        WHEN 'IN_DEBATE'    THEN '#0d6efd' -- Standard Blue
        WHEN 'APPROVED'     THEN '#17a2b8' -- Informational Teal
        WHEN 'IN_EXECUTION' THEN '#ffc107' -- Warning/In-Progress Yellow
        WHEN 'CLOSED'       THEN '#28a745' -- Success Green
        WHEN 'AUDITED'      THEN '#8342f5' -- Distinct Purple
        ELSE color_hex -- Keep existing value if no match
    END,
    icon_name = CASE id
        WHEN 'PROPOSED'     THEN 'lightbulb'
        WHEN 'IN_DEBATE'    THEN 'gavel'
        WHEN 'APPROVED'     THEN 'how_to_vote'
        WHEN 'IN_EXECUTION' THEN 'trending_up'
        WHEN 'CLOSED'       THEN 'check_circle'
        WHEN 'AUDITED'      THEN 'fact_check'
        ELSE icon_name -- Keep existing value if no match
    END;

END $$;
-- ====================================================================
-- SECTION 1: POPULATE LAW TYPES
-- ====================================================================
INSERT INTO agora.law_types (id, translations)
VALUES
    ('CONSTITUTION',            '{"en": {"name": "Constitution"}, "pt": {"name": "Constituição"}}'),
    ('PARLIAMENTARY_LAW',       '{"en": {"name": "Parliamentary Law"}, "pt": {"name": "Lei da Assembleia"}}'),
    ('DECREE_LAW',              '{"en": {"name": "Decree-Law"}, "pt": {"name": "Decreto-Lei"}}'),
    ('REGULATION',              '{"en": {"name": "Regulation"}, "pt": {"name": "Regulamento"}}'),
    ('RESOLUTION',              '{"en": {"name": "Resolution"}, "pt": {"name": "Resolução"}}'),
    ('INTERNATIONAL_TREATY',    '{"en": {"name": "International Treaty"}, "pt": {"name": "Tratado Internacional"}}')
ON CONFLICT (id) DO UPDATE SET translations = EXCLUDED.translations;


-- ====================================================================
-- SECTION 2: POPULATE LAW CATEGORIES
-- ====================================================================
INSERT INTO agora.law_categories (id, translations)
VALUES
    ('FISCAL',          '{"en": {"name": "Fiscal & Tax"}, "pt": {"name": "Fiscal e Impostos"}}'),
    ('LABOR',           '{"en": {"name": "Labor & Employment"}, "pt": {"name": "Trabalho e Emprego"}}'),
    ('HEALTH',          '{"en": {"name": "Health"}, "pt": {"name": "Saúde"}}'),
    ('ENVIRONMENTAL',   '{"en": {"name": "Environmental"}, "pt": {"name": "Ambiente"}}'),
    ('JUDICIAL',        '{"en": {"name": "Judicial"}, "pt": {"name": "Judicial"}}'),
    ('ADMINISTRATIVE',  '{"en": {"name": "Public Administration"}, "pt": {"name": "Administração Pública"}}'),
    ('CIVIL',           '{"en": {"name": "Civil Law"}, "pt": {"name": "Direito Civil"}}'),
    ('CRIMINAL',        '{"en": {"name": "Criminal Law"}, "pt": {"name": "Direito Penal"}}'),
    ('SOCIAL_SECURITY', '{"en": {"name": "Social Security"}, "pt": {"name": "Segurança Social"}}')
ON CONFLICT (id) DO UPDATE SET translations = EXCLUDED.translations;


-- ====================================================================
-- SECTION 3: POPULATE LAW VERSION STATUSES
-- ====================================================================
INSERT INTO agora.law_version_statuses (id, translations)
VALUES
    ('ACTIVE',      '{"en": {"name": "Active"}, "pt": {"name": "Ativo"}}'),
    ('SUPERSEDED',  '{"en": {"name": "Superseded"}, "pt": {"name": "Substituído"}}'),
    ('REVOKED',     '{"en": {"name": "Revoked"}, "pt": {"name": "Revogado"}}'),
    ('DRAFT',       '{"en": {"name": "Draft"}, "pt": {"name": "Proposta"}}')
ON CONFLICT (id) DO UPDATE SET translations = EXCLUDED.translations;


-- ====================================================================
-- SECTION 4: POPULATE GLOSSARY
-- Description: Adds key acronyms and terms to provide context to the AI.
-- ====================================================================
INSERT INTO agora.glossary (term, translations)
VALUES
    ('FEFSS',   '{"en": {"definition": "Social Security Financial Stabilization Fund"}, "pt": {"definition": "Fundo de Estabilização Financeira da Segurança Social"}}'),
    ('SNS',     '{"en": {"definition": "National Health Service"}, "pt": {"definition": "Serviço Nacional de Saúde"}}'),
    ('PRR',     '{"en": {"definition": "Recovery and Resilience Plan"}, "pt": {"definition": "Plano de Recuperação e Resiliência"}}'),
    ('DGAL',    '{"en": {"definition": "General Directorate of Local Authorities"}, "pt": {"definition": "Direção-Geral das Autarquias Locais"}}'),
    ('IVA',     '{"en": {"definition": "Value-Added Tax (VAT)"}, "pt": {"definition": "Imposto sobre o Valor Acrescentado"}}'),
    ('IRS',     '{"en": {"definition": "Personal Income Tax"}, "pt": {"definition": "Imposto sobre o Rendimento de Pessoas Singulares"}}'),
    ('IRC',     '{"en": {"definition": "Corporate Income Tax"}, "pt": {"definition": "Imposto sobre o Rendimento de Pessoas Coletivas"}}')
ON CONFLICT (term) DO UPDATE SET translations = EXCLUDED.translations;


-- ====================================================================
-- SECTION 5: POPULATE INITIAL TAGS
-- Description: Adds a base set of conceptual tags for the AI to use.
-- ====================================================================
INSERT INTO agora.tags (name)
VALUES
    ('Just Cause for Dismissal'),
    ('Tax Incentive'),
    ('Environmental Regulation'),
    ('Public Health Measure'),
    ('Labor Rights'),
    ('Decentralization'),
    ('Digital Transition'),
    ('Social Housing')
ON CONFLICT (name) DO NOTHING;