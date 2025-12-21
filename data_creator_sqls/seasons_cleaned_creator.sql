CREATE TABLE season (
    seasonentryid BIGINT PRIMARY KEY,
    team_id BIGINT,
    title VARCHAR(255),
    year INT,
    xG DOUBLE,
    xGA DOUBLE,
    npxG DOUBLE,
    npxGA DOUBLE,
    deep INT,
    deep_allowed INT,
    scored INT,
    missed INT,
    xpts DOUBLE,
    result CHAR(1),
    wins INT,
    draws INT,
    loses INT,
    -- pts INT,  -- REMOVED: calculated as (wins * 3 + draws * 1)
    npxGD DOUBLE,
    ppda_att INT,
    ppda_def INT,
    ppda_allowed_att INT,
    ppda_allowed_def INT,
    CONSTRAINT uq_season_team_year UNIQUE (team_id, year),
    CONSTRAINT fk_season_team
        FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;