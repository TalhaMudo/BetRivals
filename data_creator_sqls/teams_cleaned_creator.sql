CREATE TABLE teams (
    team_id BIGINT PRIMARY KEY,
    team_name VARCHAR(255),
    league VARCHAR(128), -- Added: if team belongs to one league
    CONSTRAINT uq_teams_team_name UNIQUE (team_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;