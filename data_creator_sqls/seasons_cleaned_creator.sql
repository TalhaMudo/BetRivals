CREATE TABLE season (
    seasonentryid INT PRIMARY KEY,
    team_id INT,
    title VARCHAR(100),
    year INT,
    h_a CHAR(1),
    xG FLOAT,
    xGA FLOAT,
    npxG FLOAT,
    npxGA FLOAT,
    deep INT,
    deep_allowed INT,
    scored INT,
    missed INT,
    xpts FLOAT,
    result VARCHAR(10),
    date DATETIME,
    wins INT,
    draws INT,
    loses INT,
    pts INT,
    npxGD FLOAT,
    ppda_att INT,
    ppda_def INT,
    ppda_allowed_att INT,
    ppda_allowed_def INT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
      ON UPDATE RESTRICT
      ON DELETE RESTRICT,
    -- veri kontrolleri
    CONSTRAINT chk_ha     CHECK (h_a IN ('H','A') OR h_a IS NULL),
    CONSTRAINT chk_result CHECK (result IN ('W','D','L') OR result IS NULL),
    CONSTRAINT chk_year   CHECK (year BETWEEN 1900 AND 2100)
);

