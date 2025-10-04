-- Agora Schema - Functions
-- Index:
-- 1. get_source_entities_with_details
-- 2. get_source_entity_full_by_id
-- 3. get_unassociated_gov_actions_for_promise
-- 4. get_unassociated_sources_for_action
-- 5. get_unassociated_sources_for_promise
-- 6. get_ordered_filterable_governments
-- 7. get_budget_dashboard_data
-- 8. compare_budgets_by_slug
-- 9. get_sources_by_mandate
-- 10. get_source_details_by_slug
-- 11. update_search_index_for_promise
-- 12. get_sources_with_chunk_status
-- 13. get_law_details_by_slug
-- 14. krita_rag_retriever
-- 15. get_sources_with_ingestion_status
-- 16. get_filtered_laws_list
-- 17. get_law_details_by_slug_v2

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
                        'title', s.translations->'en'->>'title',
                        'published_at', s.published_at,
                        'credibility_score', s.credibility_score,
                        'source_type', st.translations->'en'->>'name'
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
    action_types jsonb,
    action_statuses jsonb,
    total_count bigint
) AS $$
BEGIN
    RETURN QUERY
    WITH filtered_actions AS (
        SELECT
            ga.*,
            jsonb_build_object('translations', atype.translations) AS action_types_json,
            jsonb_build_object('translations', astat.translations, 'color_hex', astat.color_hex) AS action_statuses_json,
            COUNT(*) OVER() AS full_count
        FROM
            agora.government_actions ga
        LEFT JOIN agora.action_types atype ON ga.action_type_id = atype.id
        LEFT JOIN agora.action_statuses astat ON ga.status_id = astat.id
        WHERE
            ga.government_entity_id = p_government_entity_id
            AND NOT EXISTS (
                SELECT 1
                FROM agora.action_promises ap
                WHERE ap.action_id = ga.id AND ap.promise_id = p_promise_id
            )
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

CREATE OR REPLACE FUNCTION agora.get_unassociated_sources_for_action(
    p_action_id uuid,
    p_search_text text DEFAULT NULL,
    p_source_type_id text DEFAULT NULL,
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    id uuid,
    translations jsonb,
    author text,
    published_at timestamp with time zone,
    main_url text,
    credibility_score numeric,
    source_entity jsonb,
    source_type jsonb,
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
            AND NOT EXISTS (
                SELECT 1
                FROM agora.action_sources asrc
                WHERE asrc.source_id = s.id AND asrc.action_id = p_action_id
            )
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

CREATE OR REPLACE FUNCTION agora.get_unassociated_sources_for_promise(
    p_promise_id uuid,
    p_search_text text DEFAULT NULL,
    p_source_type_id text DEFAULT NULL,
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    id uuid,
    translations jsonb,
    author text,
    published_at timestamp with time zone,
    main_url text,
    credibility_score numeric,
    source_entity jsonb,
    source_type jsonb,
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
            AND NOT EXISTS (
                SELECT 1
                FROM agora.promise_sources psrc
                WHERE psrc.source_id = s.id AND psrc.promise_id = p_promise_id
            )
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
        CASE
            WHEN (m.end_date IS NULL OR m.end_date >= NOW()) THEN true
            ELSE false
        END AS is_current_mandate
    FROM
        agora.government_entities AS ge
    INNER JOIN
        agora.mandates AS m ON ge.id = m.government_entity_id
    WHERE
        ge.is_active = true
    ORDER BY
        CASE WHEN ge.country_code = UPPER(p_country_code) THEN 0 ELSE 1 END,
        ge.name ASC,
        m.start_date DESC;
END;
$$ LANGUAGE plpgsql STABLE;

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

            'categories', (
                SELECT COALESCE(jsonb_agg(category_data ORDER BY total_budgeted_in_category DESC), '[]'::jsonb)
                FROM (
                    SELECT
                        cat.id AS category_id,
                        cat.translations AS category_translations,
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

CREATE OR REPLACE FUNCTION agora.compare_budgets_by_slug(p_slug_a text, p_slug_b text)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    WITH
    budget_a AS (SELECT id, year FROM agora.budgets WHERE slug = p_slug_a),
    budget_b AS (SELECT id, year FROM agora.budgets WHERE slug = p_slug_b),
    all_categories AS (
        SELECT
            cat.id AS category_id,
            cat.translations AS category_translations,
            COALESCE(SUM(bsi.budgeted_amount) FILTER (WHERE bsi.budget_id = (SELECT id FROM budget_a)), 0) AS budgeted_a,
            COALESCE(SUM((SELECT SUM(amount) FROM agora.budget_spending_events WHERE spending_item_id = bsi.id)) FILTER (WHERE bsi.budget_id = (SELECT id FROM budget_a)), 0) AS spent_a,
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

CREATE OR REPLACE FUNCTION agora.get_sources_by_mandate(
    p_mandate_ids uuid[] DEFAULT NULL,
    p_limit integer DEFAULT 50,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    id uuid,
    slug text,
    translations jsonb,
    author text,
    published_at timestamp with time zone,
    main_url text,
    credibility_score numeric,
    source_entity jsonb,
    source_type jsonb,
    promise_count bigint,
    action_count bigint,
    total_associations bigint,
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
        COALESCE((
            SELECT COUNT(*) FROM agora.promise_sources ps 
            JOIN agora.promises p ON ps.promise_id = p.id 
            WHERE ps.source_id = fs.id
        ), 0) as promise_count,
        COALESCE((
            SELECT COUNT(*) FROM agora.action_sources acs 
            JOIN agora.government_actions ga ON acs.action_id = ga.id 
            WHERE acs.source_id = fs.id
        ), 0) as action_count,
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

CREATE OR REPLACE FUNCTION agora.get_source_details_by_slug(p_source_slug text)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
    v_source_id uuid;
BEGIN
    SELECT id INTO v_source_id FROM agora.sources WHERE slug = p_source_slug;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

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

COMMENT ON FUNCTION agora.get_budget_dashboard_data(text) IS 'Returns a full, nested JSONB object for a single budget by its SLUG, including all its children and aggregated totals.';

CREATE OR REPLACE FUNCTION agora.update_search_index_for_promise()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO agora.search_index (target_id, target_table, government_entity_id, mandate_id, content)
    VALUES (
        NEW.id,
        'promises',
        NEW.government_entity_id,
        NEW.mandate_id,
        concat_ws(' ', NEW.translations->'en'->>'wording', NEW.translations->'en'->>'context_description')
    )
    ON CONFLICT (target_id, target_table) DO UPDATE
    SET content = EXCLUDED.content,
        government_entity_id = EXCLUDED.government_entity_id,
        mandate_id = EXCLUDED.mandate_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER on_promise_change
    AFTER INSERT OR UPDATE ON agora.promises
    FOR EACH ROW EXECUTE FUNCTION agora.update_search_index_for_promise();

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
        s.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_sources_with_chunk_status() IS 'Returns all sources with their document chunk processing status.';

CREATE OR REPLACE FUNCTION agora.get_law_details_by_slug(p_law_slug text)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
    v_law_id uuid;
BEGIN
    SELECT id INTO v_law_id FROM agora.laws WHERE slug = p_law_slug;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    SELECT
        jsonb_build_object(
            'id', l.id,
            'slug', l.slug,
            'official_number', l.official_number,
            'official_title', l.official_title,
            'enactment_date', l.enactment_date,
            'tags', l.tags,
            'translations', l.translations,
            'type', (SELECT lt.translations FROM agora.law_types lt WHERE lt.id = l.type_id),
            'category', (SELECT lc.translations FROM agora.law_categories lc WHERE lc.id = l.category_id),
            'government_entity', (SELECT jsonb_build_object('id', ge.id, 'name', ge.name, 'slug', ge.slug) FROM agora.government_entities ge WHERE ge.id = l.government_entity_id),

            'articles', (
                SELECT COALESCE(jsonb_agg(
                    jsonb_build_object(
                        'id', lav.id,
                        'article_order', lav.article_order,
                        'official_text', lav.official_text,
                        'translations', lav.translations,
                        'tags', lav.tags,
                        'valid_from', lav.valid_from,
                        'valid_to', lav.valid_to,
                        'status', (SELECT lvs.translations FROM agora.law_version_statuses lvs WHERE lvs.id = lav.status_id)
                    ) ORDER BY lav.article_order ASC
                ), '[]'::jsonb)
                FROM agora.law_article_versions lav
                WHERE lav.law_id = v_law_id
            )
        )
    INTO result
    FROM
        agora.laws l
    WHERE
        l.id = v_law_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_law_details_by_slug(text) IS 'Returns a full, nested JSONB object for a single law by its SLUG, including all its article versions.';

CREATE OR REPLACE FUNCTION agora.krita_rag_retriever(
    p_law_id uuid,
    p_query_embedding vector(1536),
    p_mode text,
    p_match_count integer
)
RETURNS TABLE (
    content text,
    similarity_score float
) AS $$
BEGIN
    IF p_mode = 'simple' THEN
        RETURN QUERY
        SELECT
            lav.translations->'en'->>'informal_summary' AS content,
            (lav.summary_embedding <=> p_query_embedding)::float AS similarity_score
        FROM
            agora.law_article_versions lav
        WHERE
            lav.law_id = p_law_id
        ORDER BY
            lav.summary_embedding <=> p_query_embedding
        LIMIT
            p_match_count;

    ELSIF p_mode = 'complete' THEN
        RETURN QUERY
        SELECT
            dc.content,
            (dc.embedding <=> p_query_embedding)::float AS similarity_score
        FROM
            agora.document_chunks dc
        JOIN
            agora.sources s ON dc.source_id = s.id
        JOIN
            agora.laws l ON s.id = l.source_id
        WHERE
            l.id = p_law_id
        ORDER BY
            dc.embedding <=> p_query_embedding
        LIMIT
            p_match_count;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.krita_rag_retriever(uuid, vector, text, integer) IS 'Retrieves relevant text context for the Krita AI assistant using either summaries (simple mode) or raw chunks (complete mode).';

CREATE OR REPLACE FUNCTION agora.get_sources_with_ingestion_status()
RETURNS TABLE (
    source_id uuid,
    main_url text,
    translations jsonb,
    created_at timestamptz,
    chunk_count bigint,
    law_id uuid,
    law_slug text,
    has_chunks boolean,
    has_analysis boolean,
    has_law boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id AS source_id,
        s.main_url,
        s.translations,
        s.created_at,
        COUNT(DISTINCT dc.id) AS chunk_count,
        l.id AS law_id,
        l.slug AS law_slug,
        (COUNT(DISTINCT dc.id) > 0) AS has_chunks,
        EXISTS (SELECT 1 FROM agora.source_ai_analysis saa WHERE saa.source_id = s.id) AS has_analysis,
        (l.id IS NOT NULL) AS has_law
    FROM
        agora.sources s
    LEFT JOIN
        agora.document_chunks dc ON s.id = dc.source_id
    LEFT JOIN
        agora.laws l ON s.id = l.source_id
    GROUP BY
        s.id, l.id
    ORDER BY
        s.created_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION agora.get_filtered_laws_list(
    p_search_text text DEFAULT NULL,
    p_category_ids text[] DEFAULT NULL,
    p_type_ids text[] DEFAULT NULL,
    p_government_entity_id uuid DEFAULT NULL,
    p_limit integer DEFAULT 20,
    p_offset integer DEFAULT 0
)
RETURNS TABLE (
    id uuid,
    slug text,
    official_number text,
    official_title text,
    enactment_date date,
    translations jsonb,
    government_entity_id uuid,
    type_id text,
    category_id text,
    government_entity jsonb,
    law_type jsonb,
    law_category jsonb,
    total_count bigint
) AS $$
DECLARE
    total_records bigint;
BEGIN
    SELECT COUNT(*) INTO total_records
    FROM agora.laws l
    WHERE 
        (p_search_text IS NULL OR 
         l.official_title ILIKE '%' || p_search_text || '%' OR
         l.translations->'en'->>'informal_summary' ILIKE '%' || p_search_text || '%')
    AND (p_category_ids IS NULL OR l.category_id = ANY(p_category_ids))
    AND (p_type_ids IS NULL OR l.type_id = ANY(p_type_ids))
    AND (p_government_entity_id IS NULL OR l.government_entity_id = p_government_entity_id);

    RETURN QUERY
    SELECT 
        l.id,
        l.slug,
        l.official_number,
        l.official_title,
        l.enactment_date,
        l.translations,
        l.government_entity_id,
        l.type_id,
        l.category_id,
        jsonb_build_object(
            'id', ge.id,
            'name', ge.name,
            'slug', ge.slug
        ) as government_entity,
        lt.translations as law_type,
        lc.translations as law_category,
        total_records as total_count
    FROM agora.laws l
    LEFT JOIN agora.government_entities ge ON l.government_entity_id = ge.id
    LEFT JOIN agora.law_types lt ON l.type_id = lt.id
    LEFT JOIN agora.law_categories lc ON l.category_id = lc.id
    WHERE 
        (p_search_text IS NULL OR 
         l.official_title ILIKE '%' || p_search_text || '%' OR
         l.translations->'en'->>'informal_summary' ILIKE '%' || p_search_text || '%')
    AND (p_category_ids IS NULL OR l.category_id = ANY(p_category_ids))
    AND (p_type_ids IS NULL OR l.type_id = ANY(p_type_ids))
    AND (p_government_entity_id IS NULL OR l.government_entity_id = p_government_entity_id)
    ORDER BY l.enactment_date DESC NULLS LAST
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_filtered_laws_list(text, text[], text[], uuid, integer, integer) 
IS 'Returns a paginated and filtered list of laws with their related entities';

CREATE OR REPLACE FUNCTION agora.get_law_details_by_slug_v2(p_law_slug text)
RETURNS jsonb AS $$
DECLARE
    result jsonb;
    v_law_id uuid;
BEGIN
    SELECT id INTO v_law_id FROM agora.laws WHERE slug = p_law_slug;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    SELECT
        jsonb_build_object(
            'id', l.id,
            'slug', l.slug,
            'official_number', l.official_number,
            'official_title', l.official_title,
            'enactment_date', l.enactment_date,
            'translations', l.translations,
            'type', (SELECT lt.translations FROM agora.law_types lt WHERE lt.id = l.type_id),
            'category', (SELECT lc.translations FROM agora.law_categories lc WHERE lc.id = l.category_id),
            'government_entity', (SELECT jsonb_build_object('id', ge.id, 'name', ge.name, 'slug', ge.slug) FROM agora.government_entities ge WHERE ge.id = l.government_entity_id),

            'articles', (
                SELECT COALESCE(jsonb_agg(
                    jsonb_build_object(
                        'id', la.id,
                        'article_number', la.article_number,
                        'article_order', COALESCE(la.article_number, 'Article ' || ROW_NUMBER() OVER (ORDER BY la.article_number)),
                        'official_text', 'Official text not available yet - schema update required',
                        'translations', '{"en": {"informal_summary": "Article analysis not available yet", "informal_summary_title": "' || la.article_number || '"}}'::jsonb,
                        'tags', '[]'::jsonb
                    )
                ), '[]'::jsonb)
                FROM agora.law_articles la
                WHERE la.law_id = v_law_id
                ORDER BY la.article_number
            )
        )
    INTO result
    FROM
        agora.laws l
    WHERE
        l.id = v_law_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION agora.get_law_details_by_slug_v2(text) 
IS 'Returns a full, nested JSONB object for a single law by its SLUG - compatible with current schema';