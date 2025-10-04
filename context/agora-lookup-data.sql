-- Agora Schema - Lookup Data
-- Index:
-- 1. government_levels
-- 2. promise_statuses
-- 3. source_entity_types
-- 4. source_types
-- 5. source_relationship_types
-- 6. action_statuses
-- 7. action_types
-- 8. budget_statuses
-- 9. funding_source_types
-- 10. funding_sources
-- 11. budget_categories (with types and hierarchy)
-- 12. law_types
-- 13. law_categories
-- 14. law_version_statuses
-- 15. glossary
-- 16. tags

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