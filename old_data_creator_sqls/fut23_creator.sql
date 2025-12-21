CREATE TABLE fut23 (
    player_id BIGINT PRIMARY KEY,
    team_id BIGINT,
    Name VARCHAR(255),
    Country VARCHAR(128),
    League VARCHAR(128),
    Rating INT,
    Position VARCHAR(64),
    Run_type VARCHAR(64),
    Price VARCHAR(64),
    Skill INT,
    Weak_foot INT,
    Attack_rate CHAR(2),
    Defense_rate CHAR(2),
    Pace DOUBLE,
    Shoot DOUBLE,
    Pass DOUBLE,
    Drible DOUBLE,
    Defense DOUBLE,
    Physical DOUBLE,
    Body_type VARCHAR(64),
    Height_cm INT,
    Weight DOUBLE,
    Popularity INT,
    Base_Stats INT,
    In_Game_Stats INT,

    -- merged player statistics
    time INT,
    goals INT,
    xG DOUBLE,
    assists INT,
    xA DOUBLE,
    yellow_cards INT,
    red_cards INT,
    npg INT,
    npxG DOUBLE,
    xGChain DOUBLE,
    xGBuildup DOUBLE,
    year INT,
    best_shot_id BIGINT,

    CONSTRAINT fk_fut23_team
        FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Below is executed after shot_data table is created.

ALTER TABLE fut23
ADD CONSTRAINT fk_fut23_best_shot
FOREIGN KEY (best_shot_id)
REFERENCES shot_data(shot_id)
ON UPDATE CASCADE
ON DELETE SET NULL;
