CREATE TABLE IF NOT EXISTS trading
(
    platform character varying(4) not null,
    hour timestamp with time zone not null,
    igpcode character varying(32) not null,
    gamecode character varying(32) not null,
    country character varying(3) not null,
    ccycode character varying(6) not null,
    mode character varying(4) not null,
    channel character varying(12) not null DEFAULT 'web',
    jurisdiction character varying(12) not null DEFAULT 'unknown',
    maxstake numeric(20,2) not null DEFAULT 0.00,
    unique_players integer not null,
    num_rm_plays integer not null,
    rm_bet numeric(20,2) not null,
    rm_win numeric(20,2) not null,
    num_dm_plays integer not null,
    dm_bet numeric(20,2) not null,
    dm_win numeric(20,2) not null,
    num_fr_op_plays integer not null,
    fr_op_bet numeric(20,2) not null,
    fr_op_win numeric(20,2) not null,
    num_fr_rgs_plays integer not null,
    fr_rgs_bet numeric(20,2) not null,
    fr_rgs_win numeric(20,2) not null,
    PRIMARY KEY(platform, hour, igpcode, gamecode, country, ccycode, mode, channel, jurisdiction, maxstake)
);

CREATE INDEX trading_datamart_idx_hour ON trading (hour);

CREATE TABLE IF NOT EXISTS archive_partitions
(
    p_prefix character varying(10) not null,
    p_version character varying(2) not null,
    p_table character varying(13) not null,
    p_year character varying(4) not null,
    p_month character varying(2) not null,
    p_day character varying(2) not null,
    p_hour character varying(2) not null,
    p_platform character varying(4) not null,
    processed character varying(5) not null,
    PRIMARY KEY(p_prefix, p_version, p_table, p_year, p_month, p_day, p_hour, p_platform)
);

CREATE INDEX idx_processed_false ON archive_partitions(processed, p_version) WHERE processed = 'false';

CREATE TABLE historical_data_load_control
(
    status        VARCHAR(16) NOT NULL CHECK (status IN ('active', 'suspended')),
    glue_job_name VARCHAR(71) NOT NULL CHECK (glue_job_name LIKE '%-gameplay-pipeline-historical-data-load-v1' OR
                                              glue_job_name LIKE '%-gameplay-pipeline-historical-data-load-v2')
)