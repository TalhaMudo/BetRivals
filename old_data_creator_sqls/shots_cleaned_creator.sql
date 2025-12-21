CREATE TABLE shot_data (
    shot_id BIGINT PRIMARY KEY,
    minute INT,
    result VARCHAR(64),
    X DOUBLE,
    Y DOUBLE,
    xG DOUBLE,
    h_a CHAR(1),
    player_id BIGINT,
    situation VARCHAR(64),
    season INT,
    shotType VARCHAR(64),
    match_id BIGINT,
    player_assisted BIGINT,
    lastAction VARCHAR(64),
    CONSTRAINT fk_shot_match
        FOREIGN KEY (match_id)
        REFERENCES match_info(match_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_shot_player
        FOREIGN KEY (player_id)
        REFERENCES fut23(player_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_shot_assist_player
        FOREIGN KEY (player_assisted)
        REFERENCES fut23(player_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
