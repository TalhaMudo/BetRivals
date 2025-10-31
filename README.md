# 🏆 BetRivals — ITU BLG 317E Database Project

Welcome to our humble repository 👋  
We are using a **multibranch structure** for development.

.
.
├── Osman
│   ├── osman_sub_branches
│
├── Bilge
│   ├── bilge_sub_branches
│
├── Abdullah
│   ├── abdullah_sub_branches
│
├── Talha
│   ├── talha_sub_branches
│
└── main

### 👨‍💻 Contributors

- **Osman Yahya Akıncı** — `osman-yahya`  
- **Bilge Bostanbaşı** — `bilgebos`  
- **Abdullah Akcan** — `itu-itis23-akcana22`  
- **Talha Müderrisoğlu** — `TalhaMudo`

# About Datasets

## 📦 1) player_cleaned.csv
### Columns
- season_player_id (PK)
- player_id
- player_name
- games, time, goals, xG, assists, shots, key_passes, cards, position...
- team_title
- year

### Foreign Keys
| Column | → Table.Column |
|--------|----------------|
| player_id | fut23_cleaned.player_id |
| player_id | shot_data_cleaned.player_id |
| team_title | teams_cleaned.team_name |

---

## ⚽ 2) match_info_cleaned.csv
### Columns
- match_id
- h, a (team ids text form)
- date, league, season
- h_goals, a_goals
- h_xg, a_xg
- h_ppda, a_ppda

### Foreign Keys
| Column | → Table.Column |
|--------|----------------|
| match_id | match_data_cleaned.match_id |
| team_h / team_a | teams_cleaned.team_name |

---

## 🏟️ 3) teams_cleaned.csv
### Columns
- team_id (PK)
- team_name

### References (other tables refer here)
| From Table | Column |
|------------|--------|
| season_cleaned | team_id |
| match_data_cleaned | h_id, a_id |
| match_info_cleaned | team_h, team_a |
| shot_data_cleaned | h_team, a_team |
| player_cleaned | team_title |

---

## 🧾 4) match_data_cleaned.csv
### Columns
- match_id (PK)
- h_id, a_id (team IDs)
- goals_h, goals_a
- xG_h, xG_a

### Foreign Keys
| Column | → Table.Column |
|--------|----------------|
| match_id | match_info_cleaned.match_id |
| match_id | shot_data_cleaned.match_id |
| h_id / a_id | teams_cleaned.team_id |

---

## 🎮 5) fut23_cleaned.csv
### Columns
- player_id (PK)
- Name
- team_id, Team
- Rating, Pace, Shoot, Pass, Dribble, Defense, Physical, etc.

### Foreign Keys
| Column | → Table.Column |
|--------|----------------|
| player_id | player_cleaned.player_id |
| player_id | shot_data_cleaned.player_id |
| team_id | teams_cleaned.team_id |

---

## 📊 6) season_cleaned.csv
### Columns
- seasonentryid (PK)
- team_id
- year
- xG, xGA, npxG, npxGA, pts, wins, draws, losses...

### Foreign Keys
| Column | → Table.Column |
|--------|----------------|
| team_id | teams_cleaned.team_id |

---

## 🎯 7) shot_data_cleaned.csv
### Columns
- shot_id (PK)
- match_id
- player_id
- minute
- X, Y
- xG
- h_team, a_team
- result, situation, season, date

### Foreign Keys
| Column | → Table.Column |
|--------|----------------|
| player_id | player_cleaned.player_id |
| player_id | fut23_cleaned.player_id |
| match_id | match_data_cleaned.match_id |
| h_team / a_team | teams_cleaned.team_name |

---

## 🔗 ERD Summary
| Table | Connects To |
|-------|-------------|
| player_cleaned | fut23_cleaned, shot_data_cleaned, teams_cleaned |
| match_info_cleaned | match_data_cleaned, teams_cleaned |
| match_data_cleaned | match_info_cleaned, shot_data_cleaned, teams_cleaned |
| fut23_cleaned | player_cleaned, shot_data_cleaned, teams_cleaned |
| season_cleaned | teams_cleaned |
| shot_data_cleaned | player_cleaned, fut23_cleaned, match_data_cleaned, teams_cleaned |
| teams_cleaned | **central reference table** |