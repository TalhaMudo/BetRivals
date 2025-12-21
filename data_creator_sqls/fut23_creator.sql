-- Table 1: Player master data (attributes that don't change across seasons)
CREATE TABLE player (
    player_id BIGINT PRIMARY KEY,
    Name VARCHAR(255),
    Country VARCHAR(128),
    Body_type VARCHAR(64),
    Height_cm INT,
    Weight DOUBLE,
    CONSTRAINT uq_players_name UNIQUE (Name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table 2: Player seasonal statistics (attributes that change each season)
CREATE TABLE fut23 (
    player_id BIGINT,
    year INT,
    team_id BIGINT,
    -- League removed: derive from team_id
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
    Popularity INT,
    -- Base_Stats INT, -- REMOVED: calculated from Pace+Shoot+Pass+Drible+Defense+Physical
    -- In_Game_Stats INT, -- REMOVED: if calculated/derived
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
    best_shot_id BIGINT,
    PRIMARY KEY (player_id, year),
    CONSTRAINT fk_player_seasons_player
        FOREIGN KEY (player_id)
        REFERENCES players(player_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_player_seasons_team
        FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_player_seasons_best_shot
        FOREIGN KEY (best_shot_id)
        REFERENCES shot_data(shot_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Update shot_data foreign keys to reference the correct table
-- The player_id and player_assisted should reference the players table
ALTER TABLE shot_data
DROP FOREIGN KEY fk_shot_player,
DROP FOREIGN KEY fk_shot_assist_player;

ALTER TABLE shot_data
ADD CONSTRAINT fk_shot_player
    FOREIGN KEY (player_id)
    REFERENCES players(player_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,
ADD CONSTRAINT fk_shot_assist_player
    FOREIGN KEY (player_assisted)
    REFERENCES players(player_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL;