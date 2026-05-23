-- KPI Portal Schema

CREATE TABLE pillars (
    id   SERIAL PRIMARY KEY,
    code VARCHAR(10)  NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE teams (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE kpis (
    id          SERIAL PRIMARY KEY,
    kpi_code    VARCHAR(50)  NOT NULL UNIQUE,
    pillar_id   INT          NOT NULL REFERENCES pillars(id),
    team_id     INT          NOT NULL REFERENCES teams(id),
    header_code VARCHAR(50)  NOT NULL,
    header_name VARCHAR(200) NOT NULL,
    kpi_name    VARCHAR(200) NOT NULL
);

CREATE TABLE report_periods (
    id          SERIAL PRIMARY KEY,
    period_date DATE         NOT NULL,
    label       VARCHAR(50)  NOT NULL
);

CREATE TABLE status_lookup (
    id    SERIAL PRIMARY KEY,
    value VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE task_type_lookup (
    id    SERIAL PRIMARY KEY,
    value VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE tasks (
    id               SERIAL PRIMARY KEY,
    kpi_id           INT            NOT NULL REFERENCES kpis(id),
    report_period_id INT            NOT NULL REFERENCES report_periods(id),
    task_code        VARCHAR(50),
    task_name        VARCHAR(200)   NOT NULL,
    task_type_id     INT            NOT NULL REFERENCES task_type_lookup(id),
    start_date       DATE,
    due_date         DATE,
    status_id        INT            NOT NULL REFERENCES status_lookup(id),
    pct_complete     NUMERIC(4,2)   NOT NULL DEFAULT 0.0,
    effort_days      NUMERIC(6,2),
    actual_days      NUMERIC(6,2),
    blockers         TEXT,
    notes            TEXT,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ───────────────────────────────────────────
-- SEED: Pillars
-- ───────────────────────────────────────────
INSERT INTO pillars (code, name) VALUES
    ('STB', 'Stability'),
    ('CST', 'Cost'),
    ('SEC', 'Security'),
    ('AUT', 'Automation');

-- ───────────────────────────────────────────
-- SEED: Teams
-- ───────────────────────────────────────────
INSERT INTO teams (name, description) VALUES
    ('SRE',             'Site Reliability Engineering'),
    ('DBOps',           'Database Operations'),
    ('CloudOps',        'Cloud Operations'),
    ('SecOps',          'Security Operations'),
    ('App-Engineering', 'Application Engineering'),
    ('AIOps',           'AI Operations');

-- ───────────────────────────────────────────
-- SEED: Report Period
-- ───────────────────────────────────────────
INSERT INTO report_periods (period_date, label) VALUES
    ('2026-04-30', 'Apr 2026');

-- ───────────────────────────────────────────
-- SEED: Status Lookup
-- ───────────────────────────────────────────
INSERT INTO status_lookup (value) VALUES
    ('Not Started'),
    ('In Progress'),
    ('Done'),
    ('Blocked');

-- ───────────────────────────────────────────
-- SEED: Task Type Lookup
-- ───────────────────────────────────────────
INSERT INTO task_type_lookup (value) VALUES
    ('Planning'),
    ('Execution');

-- ───────────────────────────────────────────
-- SEED: KPIs
-- ───────────────────────────────────────────
INSERT INTO kpis (kpi_code, pillar_id, team_id, header_code, header_name, kpi_name) VALUES
    ('KPI.STB.1.1', (SELECT id FROM pillars WHERE code='STB'), (SELECT id FROM teams WHERE name='SRE'),
        'KPI.STB.1', 'Infrastructure Stability', 'Observability consolidated to 1 platform'),

    ('KPI.STB.2.1', (SELECT id FROM pillars WHERE code='STB'), (SELECT id FROM teams WHERE name='SRE'),
        'KPI.STB.2', 'Uptime & SLA', 'Improve infrastructure stability to 99.9%'),

    ('KPI.STB.2.2', (SELECT id FROM pillars WHERE code='STB'), (SELECT id FROM teams WHERE name='SRE'),
        'KPI.STB.2', 'Uptime & SLA', 'Reduce platform major incidents by 70%'),

    ('KPI.STB.1.2', (SELECT id FROM pillars WHERE code='STB'), (SELECT id FROM teams WHERE name='DBOps'),
        'KPI.STB.1', 'Infrastructure Stability', 'Migrate Mongo Atlas to open-source'),

    ('KPI.CST.1.1', (SELECT id FROM pillars WHERE code='CST'), (SELECT id FROM teams WHERE name='CloudOps'),
        'KPI.CST.1', 'Cloud Cost Savings', 'Achieve $1M savings in CloudOps'),

    ('KPI.SEC.1.1', (SELECT id FROM pillars WHERE code='SEC'), (SELECT id FROM teams WHERE name='SecOps'),
        'KPI.SEC.1', 'Security Coverage', 'Cloud & platform security coverage 60%→75%'),

    ('KPI.STB.3.1', (SELECT id FROM pillars WHERE code='STB'), (SELECT id FROM teams WHERE name='App-Engineering'),
        'KPI.STB.3', 'Resilience Testing', '100% DR tested – AOS, STAQ & Op1'),

    ('KPI.AUT.1.1', (SELECT id FROM pillars WHERE code='AUT'), (SELECT id FROM teams WHERE name='AIOps'),
        'KPI.AUT.1', 'Automate Man-days Saved', 'AI automation – man-days saved'),

    ('KPI.AUT.1.2', (SELECT id FROM pillars WHERE code='AUT'), (SELECT id FROM teams WHERE name='AIOps'),
        'KPI.AUT.1', 'Automate Man-days Saved', 'AI Agents deployed into CloudOps');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.STB.1.1 (SRE)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.1.1'), 1,
     'Define observability platform requirements',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 3, 3, NULL, 'Requirements doc completed'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.1.1'), 1,
     'Evaluate Grafana vs Datadog',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.5, 5, 2, 'Pending vendor pricing', 'Grafana shortlisted'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.1.1'), 1,
     'Deploy platform in dev env',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Not Started'),
     0.0, 10, 0, 'Waiting platform selection', 'Planned Q2');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.STB.2.1 (SRE)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.2.1'), 1,
     'Complete GP migration',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.3, 8, 3, 'ELK upgrade pending', '30% migrated'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.2.1'), 1,
     'OS upgrades on deprecated servers',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.75, 5, 4, NULL, '75% done'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.2.1'), 1,
     'Implement APM alerts',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 3, 3, NULL, '100% coverage');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.STB.2.2 (SRE)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.2.2'), 1,
     'Implement change review process',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 3, 3, NULL, 'Internal review process live'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.2.2'), 1,
     'Improve monitoring coverage',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 4, 4, NULL, '100% coverage achieved');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.STB.1.2 (DBOps)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.1.2'), 1,
     'Build Mongo Community platform',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 5, 5, NULL, 'Community platform built'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.1.2'), 1,
     'Validate 1 service in dev env',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 3, 3, NULL, 'AOS service validated'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.1.2'), 1,
     'Validate remaining AOS services',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.2, 10, 2, 'Needs Engineering support', 'In progress');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.CST.1.1 (CloudOps)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.CST.1.1'), 1,
     'Identify unused cloud resources',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 3, 3, NULL, '$65K savings identified'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.CST.1.1'), 1,
     'Decommission unused servers',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 5, 4, NULL, '$63K saved'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.CST.1.1'), 1,
     'Optimize cloud/platform licensing',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.45, 15, 7, 'Vendor negotiations', '$537K target'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.CST.1.1'), 1,
     'Review DB cleanup opportunities',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 4, 3, NULL, '$65K saved');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.SEC.1.1 (SecOps)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.SEC.1.1'), 1,
     'Audit current CrowdStrike coverage',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 2, 2, NULL, 'Baseline 60% established'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.SEC.1.1'), 1,
     'Deploy to remaining infrastructure',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.75, 8, 6, NULL, '75% coverage achieved'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.SEC.1.1'), 1,
     'Complete remaining infra coverage',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Not Started'),
     0.0, 4, 0, 'Target end of May', 'Planned');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.STB.3.1 (App-Engineering)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.3.1'), 1,
     'Complete AOS DR test in QA',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 4, 4, NULL, 'AOS DR test completed'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.3.1'), 1,
     'Plan DR test in prod-facing env',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.3, 3, 1, NULL, 'May planning'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.3.1'), 1,
     'Complete STAQ DR test',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Not Started'),
     0.0, 5, 0, 'Pending QA completion', 'Planned Q2'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.STB.3.1'), 1,
     'Complete Op1 DR test',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Not Started'),
     0.0, 5, 0, 'Pending QA completion', 'Planned Q2');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.AUT.1.1 (AIOps)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.AUT.1.1'), 1,
     'Identify automation candidates',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 2, 2, NULL, '8 candidates identified'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.AUT.1.1'), 1,
     'Build DM migration automation',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 5, 4, NULL, '45 man-days/month saved'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.AUT.1.1'), 1,
     'Build log purge automation',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.3, 4, 1, NULL, 'In development'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.AUT.1.1'), 1,
     'Build S3 cleanup automation',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='In Progress'),
     0.2, 3, 1, NULL, 'In development');

-- ───────────────────────────────────────────
-- SEED: Tasks — KPI.AUT.1.2 (AIOps)
-- ───────────────────────────────────────────
INSERT INTO tasks (kpi_id, report_period_id, task_name, task_type_id, status_id, pct_complete, effort_days, actual_days, blockers, notes)
VALUES
    ((SELECT id FROM kpis WHERE kpi_code='KPI.AUT.1.2'), 1,
     'TOC Agent – HLD & LLD',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 3, 3, NULL, 'Complete'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.AUT.1.2'), 1,
     'FinOps Agent – HLD & LLD',
     (SELECT id FROM task_type_lookup WHERE value='Planning'),
     (SELECT id FROM status_lookup WHERE value='Done'),
     1.0, 3, 3, NULL, 'Complete'),

    ((SELECT id FROM kpis WHERE kpi_code='KPI.AUT.1.2'), 1,
     'SRE Agent – SLO Monitoring',
     (SELECT id FROM task_type_lookup WHERE value='Execution'),
     (SELECT id FROM status_lookup WHERE value='Not Started'),
     0.0, 5, 0, NULL, 'Planned Q3');
