CREATE TABLE match_info (
    match_id BIGINT PRIMARY KEY,
    fid BIGINT,
    h BIGINT,
    a BIGINT,
    date DATETIME,
    season BIGINT,
    h_goals INT,
    a_goals INT,
    h_xg DOUBLE,
    a_xg DOUBLE,
    h_w DOUBLE,
    h_d DOUBLE,
    h_l DOUBLE,
    league VARCHAR(128),
    h_shot INT,
    a_shot INT,
    h_shotOnTarget INT,
    a_shotOnTarget INT,
    h_deep INT,
    a_deep INT,
    a_ppda DOUBLE,
    h_ppda DOUBLE,
    CONSTRAINT fk_match_home_team
        FOREIGN KEY (h)
        REFERENCES teams(team_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_match_away_team
        FOREIGN KEY (a)
        REFERENCES teams(team_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_match_season
        FOREIGN KEY (season)
        REFERENCES season(seasonentryid)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
