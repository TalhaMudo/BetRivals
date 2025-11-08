CREATE TABLE match_info ( 
    match_id INT,
    fid INT,
    h INT, -- home team id
    a INT, -- away team id
    date DATETIME,
    league_id INT,
    season INT,
    h_goals INT,
    a_goals INT,
    team_h VARCHAR(30), -- team name
    team_a VARCHAR(30),
    h_xg FLOAT,
    a_xg FLOAT,
    h_w FLOAT,
    h_d FLOAT,
    h_l FLOAT,
    league VARCHAR(10),
    h_shot INT,
    a_shot INT,
    h_shotOnTarget INT,
    a_shotOnTarget INT,
    h_deep INT,
    a_deep INT,
    a_ppda FLOAT,
    h_ppda FLOAT
    FOREIGN KEY (h) REFERENCES teams(team_id),
    FOREIGN KEY (a) REFERENCES teams(team_id)
    FOREIGN KEY (match_id) REFERENCES match_data(match_id)
)