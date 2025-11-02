CREATE TABLE match_data ( 
    match_id INT,
    isResult BOOLEAN,
    datetime DATETIME,
    h_id INT, -- home team id
    h_title VARCHAR(20),
    h_short_title VARCHAR(5),
    a_id INT, -- away team id
    a_title VARCHAR(20),
    a_short_title VARCHAR(5),
    goals_h INT,
    goals_a INT,
    xG_h FLOAT,
    xG_a FLOAT,
    forecast_w FLOAT,
    forecast_d FLOAT,
    forecast_l FLOAT,
    FOREIGN KEY (h_id) REFERENCES teams(team_id),
    FOREIGN KEY (a_id) REFERENCES teams(team_id)
);