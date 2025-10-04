-- Agora Schema - Tables
-- Index:
-- 1. action_funding_links
-- 2. action_promises
-- 3. action_sources
-- 4. action_spending_links
-- 5. action_statuses
-- 6. action_types
-- 7. assembly_item_outcomes
-- 8. assignment_statuses
-- 9. budget_allocations
-- 10. budget_amendments
-- 11. budget_categories
-- 12. budget_category_types
-- 13. budget_spending_events
-- 14. budget_spending_items
-- 15. budget_statuses
-- 16. budgets
-- 17. comments
-- 18. contributions
-- 19. document_chunks
-- 20. emitting_entities
-- 21. emitting_entity_types
-- 22. funding_entries
-- 23. funding_source_types
-- 24. funding_sources
-- 25. glossary
-- 26. government_actions
-- 27. government_entities
-- 28. government_levels
-- 29. government_roles
-- 30. ingestion_logs
-- 31. interest_types
-- 32. law_article_references
-- 33. law_article_versions
-- 34. law_categories
-- 35. law_emitting_entities
-- 36. law_relationships
-- 37. law_types
-- 38. law_version_statuses
-- 39. laws
-- 40. mandate_party_results
-- 41. mandates
-- 42. ministries
-- 43. pending_extractions
-- 44. pending_ingestions
-- 45. people
-- 46. person_party_affiliations
-- 47. person_types
-- 48. political_parties
-- 49. promise_sources
-- 50. promise_spending_links
-- 51. promise_statuses
-- 52. promises
-- 53. prompts
-- 54. report_attachments
-- 55. report_author_anonymity
-- 56. report_content
-- 57. report_links
-- 58. report_sources
-- 59. reports
-- 60. role_assignments
-- 61. search_index
-- 62. source_ai_analysis
-- 63. source_entities
-- 64. source_entity_type_assignments
-- 65. source_entity_types
-- 66. source_relationship_types
-- 67. source_relationships
-- 68. source_types
-- 69. source_urls
-- 70. sources
-- 71. urls
-- 72. user_filters
-- 73. user_interests
-- 74. votes

-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE agora.action_funding_links (
  action_id uuid NOT NULL,
  funding_entry_id uuid NOT NULL,
  influence_type text NOT NULL,
  predicted_impact_amount numeric,
  translations jsonb,
  CONSTRAINT action_funding_links_pkey PRIMARY KEY (action_id, funding_entry_id),
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
  CONSTRAINT action_sources_pkey PRIMARY KEY (source_id, action_id),
  CONSTRAINT action_sources_action_id_fkey FOREIGN KEY (action_id) REFERENCES agora.government_actions(id),
  CONSTRAINT action_sources_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.action_spending_links (
  action_id uuid NOT NULL,
  spending_item_id uuid NOT NULL,
  allocated_amount numeric NOT NULL,
  translations jsonb,
  CONSTRAINT action_spending_links_pkey PRIMARY KEY (spending_item_id, action_id),
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
CREATE TABLE agora.emitting_entities (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  type_id text NOT NULL,
  current_ministry_id uuid,
  is_active boolean NOT NULL DEFAULT true,
  CONSTRAINT emitting_entities_pkey PRIMARY KEY (id),
  CONSTRAINT emitting_entities_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.emitting_entity_types(id),
  CONSTRAINT emitting_entities_current_ministry_id_fkey FOREIGN KEY (current_ministry_id) REFERENCES agora.ministries(id)
);
CREATE TABLE agora.emitting_entity_types (
  id text NOT NULL,
  translations jsonb NOT NULL,
  CONSTRAINT emitting_entity_types_pkey PRIMARY KEY (id)
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
  CONSTRAINT law_article_references_pkey PRIMARY KEY (target_article_version_id, source_article_version_id),
  CONSTRAINT law_article_references_source_article_version_id_fkey FOREIGN KEY (source_article_version_id) REFERENCES agora.law_article_versions(id),
  CONSTRAINT law_article_references_target_article_version_id_fkey FOREIGN KEY (target_article_version_id) REFERENCES agora.law_article_versions(id)
);
CREATE TABLE agora.law_article_versions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  mandate_id uuid NOT NULL,
  status_id text NOT NULL,
  valid_from date NOT NULL,
  valid_to date,
  official_text text NOT NULL,
  translations jsonb,
  law_id uuid,
  article_order integer,
  tags jsonb,
  summary_embedding USER-DEFINED,
  CONSTRAINT law_article_versions_pkey PRIMARY KEY (id),
  CONSTRAINT law_article_versions_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id),
  CONSTRAINT law_article_versions_status_id_fkey FOREIGN KEY (status_id) REFERENCES agora.law_version_statuses(id),
  CONSTRAINT law_article_versions_law_id_fkey FOREIGN KEY (law_id) REFERENCES agora.laws(id)
);
CREATE TABLE agora.law_categories (
  id text NOT NULL,
  translations jsonb,
  CONSTRAINT law_categories_pkey PRIMARY KEY (id)
);
CREATE TABLE agora.law_emitting_entities (
  law_id uuid NOT NULL,
  emitting_entity_id uuid NOT NULL,
  CONSTRAINT law_emitting_entities_pkey PRIMARY KEY (law_id, emitting_entity_id),
  CONSTRAINT law_emitting_entities_law_id_fkey FOREIGN KEY (law_id) REFERENCES agora.laws(id),
  CONSTRAINT law_emitting_entities_emitting_entity_id_fkey FOREIGN KEY (emitting_entity_id) REFERENCES agora.emitting_entities(id)
);
CREATE TABLE agora.law_relationships (
  source_law_id uuid NOT NULL,
  target_law_id uuid NOT NULL,
  relationship_type text NOT NULL,
  CONSTRAINT law_relationships_pkey PRIMARY KEY (target_law_id, source_law_id),
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
  source_id uuid UNIQUE,
  tags jsonb,
  CONSTRAINT laws_pkey PRIMARY KEY (id),
  CONSTRAINT laws_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT laws_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.law_types(id),
  CONSTRAINT laws_category_id_fkey FOREIGN KEY (category_id) REFERENCES agora.law_categories(id),
  CONSTRAINT laws_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
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
  CONSTRAINT promise_sources_pkey PRIMARY KEY (promise_id, source_id),
  CONSTRAINT promise_sources_promise_id_fkey FOREIGN KEY (promise_id) REFERENCES agora.promises(id),
  CONSTRAINT promise_sources_source_id_fkey FOREIGN KEY (source_id) REFERENCES agora.sources(id)
);
CREATE TABLE agora.promise_spending_links (
  promise_id uuid NOT NULL,
  spending_item_id uuid NOT NULL,
  allocated_amount numeric NOT NULL,
  translations jsonb,
  CONSTRAINT promise_spending_links_pkey PRIMARY KEY (spending_item_id, promise_id),
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
  CONSTRAINT report_links_pkey PRIMARY KEY (report_id, target_table, target_id),
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
CREATE TABLE agora.search_index (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  target_id uuid NOT NULL,
  target_table text NOT NULL,
  government_entity_id uuid,
  mandate_id uuid,
  content text,
  search_vector tsvector DEFAULT to_tsvector('english'::regconfig, COALESCE(content, ''::text)),
  embedding USER-DEFINED,
  CONSTRAINT search_index_pkey PRIMARY KEY (id),
  CONSTRAINT search_index_government_entity_id_fkey FOREIGN KEY (government_entity_id) REFERENCES agora.government_entities(id),
  CONSTRAINT search_index_mandate_id_fkey FOREIGN KEY (mandate_id) REFERENCES agora.mandates(id)
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
  CONSTRAINT source_entity_type_assignments_pkey PRIMARY KEY (source_entity_id, type_id),
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
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT sources_pkey PRIMARY KEY (id),
  CONSTRAINT sources_source_entity_id_fkey FOREIGN KEY (source_entity_id) REFERENCES agora.source_entities(id),
  CONSTRAINT sources_type_id_fkey FOREIGN KEY (type_id) REFERENCES agora.source_types(id)
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