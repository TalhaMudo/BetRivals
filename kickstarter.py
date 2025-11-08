import mysql.connector
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
# ---------------- CONFIG ---------------- #
DB_NAME = "betrivals"
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
}
CSV_DIR = Path("./csv_files")
# ---------------------------------------- #

TABLES = {
    "teams": """
        CREATE TABLE IF NOT EXISTS teams (
            team_id BIGINT PRIMARY KEY,
            team_name VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    "match_info": """
        CREATE TABLE IF NOT EXISTS match_info (
            match_id BIGINT PRIMARY KEY,
            fid BIGINT, h BIGINT, a BIGINT,
            date DATETIME,
            league_id INT, season INT,
            h_goals INT, a_goals INT,
            team_h VARCHAR(255), team_a VARCHAR(255),
            h_xg DOUBLE, a_xg DOUBLE,
            h_w DOUBLE, h_d DOUBLE, h_l DOUBLE,
            league VARCHAR(128),
            h_shot INT, a_shot INT,
            h_shotOnTarget INT, a_shotOnTarget INT,
            h_deep INT, a_deep INT,
            a_ppda DOUBLE, h_ppda DOUBLE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    "shot_data": """
        CREATE TABLE IF NOT EXISTS shot_data (
            shot_id BIGINT PRIMARY KEY,
            minute INT,
            result VARCHAR(64),
            X DOUBLE, Y DOUBLE, xG DOUBLE,
            player VARCHAR(255),
            h_a CHAR(1),
            player_id BIGINT,
            situation VARCHAR(64),
            season INT,
            shotType VARCHAR(64),
            match_id BIGINT,
            h_team VARCHAR(255), a_team VARCHAR(255),
            h_goals INT, a_goals INT,
            date DATETIME,
            player_assisted VARCHAR(255),
            lastAction VARCHAR(64),
            FOREIGN KEY (match_id) REFERENCES match_info(match_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    "season": """
        CREATE TABLE IF NOT EXISTS season (
            seasonentryid BIGINT PRIMARY KEY,
            team_id BIGINT,
            title VARCHAR(255),
            year INT,
            h_a CHAR(1),
            xG DOUBLE, xGA DOUBLE, npxG DOUBLE, npxGA DOUBLE,
            deep INT, deep_allowed INT,
            scored INT, missed INT, xpts DOUBLE,
            result CHAR(1), date DATETIME,
            wins INT, draws INT, loses INT, pts INT,
            npxGD DOUBLE,
            ppda_att INT, ppda_def INT,
            ppda_allowed_att INT, ppda_allowed_def INT,
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    "player": """
        CREATE TABLE IF NOT EXISTS player (
            season_player_id BIGINT PRIMARY KEY,
            player_id BIGINT,
            player_name VARCHAR(255),
            games INT, time INT,
            goals INT, xG DOUBLE,
            assists INT, xA DOUBLE,
            shots INT, key_passes INT,
            yellow_cards INT, red_cards INT,
            position VARCHAR(32),
            team_title VARCHAR(255),
            npg INT, npxG DOUBLE,
            xGChain DOUBLE, xGBuildup DOUBLE,
            year INT,
            best_shot_id BIGINT,
            FOREIGN KEY (best_shot_id) REFERENCES shot_data(shot_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    "match_data": """
        CREATE TABLE IF NOT EXISTS match_data (
            match_id BIGINT PRIMARY KEY,
            isResult BOOLEAN,
            datetime DATETIME,
            h_id BIGINT, h_title VARCHAR(255), h_short_title VARCHAR(32),
            a_id BIGINT, a_title VARCHAR(255), a_short_title VARCHAR(32),
            goals_h INT, goals_a INT,
            xG_h DOUBLE, xG_a DOUBLE,
            forecast_w DOUBLE, forecast_d DOUBLE, forecast_l DOUBLE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    "fut23": """
        CREATE TABLE IF NOT EXISTS fut23 (
            Name VARCHAR(255),
            player_id BIGINT PRIMARY KEY,
            Team VARCHAR(255),
            team_id BIGINT,
            Country VARCHAR(128),
            League VARCHAR(128),
            Rating INT,
            Position VARCHAR(64),
            Other_Positions VARCHAR(255),
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
            FOREIGN KEY (team_id) REFERENCES teams(team_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
}

# CRITICAL: Insert parent tables first, then child tables
# Order matters for foreign key constraints!
CSV_MAP_ORDERED = [
    ("teams", "teams_cleaned.csv"),           # No dependencies
    ("match_info", "match_info_cleaned.csv"), # No dependencies
    ("shot_data", "shot_data_cleaned.csv"),   # Depends on match_info
    ("season", "season_cleaned.csv"),         # Depends on teams
    ("player", "player_cleaned.csv"),         # Depends on shot_data (best_shot_id)
    ("match_data", "match_data_cleaned.csv"), # No FK constraints
    ("fut23", "fut23_cleaned.csv"),           # Depends on teams
]


def connect_db(include_db=False):
    cfg = MYSQL_CONFIG.copy()
    if include_db:
        cfg["database"] = DB_NAME
    return mysql.connector.connect(**cfg)


def create_database():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cur.close()
    conn.close()
    print(f"✅ Database '{DB_NAME}' ensured.")


def create_tables():
    conn = connect_db(True)
    cur = conn.cursor()
    
    # Disable foreign key checks during table creation
    cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    
    for name, ddl in TABLES.items():
        print(f"🧱 Creating table: {name}")
        cur.execute(ddl)
    
    # Re-enable foreign key checks
    cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tables created successfully.")


def insert_from_csv(table, filename):
    path = CSV_DIR / filename
    if not path.exists():
        print(f"⚠️ Missing file: {path}")
        return
    
    df = pd.read_csv(path, keep_default_na=True, na_values=['', 'nan', 'NaN', 'NA'])
    
    # Clean column names - replace dots with underscores and strip whitespace
    df.columns = [str(c).replace(".", "_").strip() for c in df.columns]
    
    # Remove columns with 'Unnamed' or that are literally 'nan' string
    cols_to_keep = []
    for col in df.columns:
        col_lower = str(col).lower()
        if not col_lower.startswith('unnamed') and col_lower != 'nan':
            cols_to_keep.append(col)
    
    df = df[cols_to_keep]
    
    # Replace NaN with None for MySQL NULL
    df = df.where(pd.notnull(df), None)

    conn = connect_db(True)
    cur = conn.cursor()

    cols = ",".join(f"`{c}`" for c in df.columns)
    placeholders = ",".join(["%s"] * len(df.columns))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

    data = [tuple(row) for row in df.itertuples(index=False, name=None)]
    
    try:
        cur.executemany(sql, data)
        conn.commit()
        print(f"✅ Inserted {len(df)} rows into {table}")
    except mysql.connector.Error as err:
        print(f"❌ Error inserting into {table}: {err}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def verify_foreign_keys():
    """Verify that foreign key constraints are properly set up"""
    conn = connect_db(True)
    cur = conn.cursor()
    
    query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            CONSTRAINT_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s 
        AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME;
    """
    
    cur.execute(query, (DB_NAME,))
    results = cur.fetchall()
    
    print("\n🔗 Foreign Key Constraints:")
    if results:
        for row in results:
            print(f"   {row[0]}.{row[1]} -> {row[3]}.{row[4]} (constraint: {row[2]})")
    else:
        print("   ⚠️ No foreign key constraints found!")
    
    cur.close()
    conn.close()


if __name__ == "__main__":
    print("""
! - - - - - - - - - !
          
Make sure that:
- There is no database called 'betrivals' in your system // if you want a clean setup
- You provided below parameters in your root folder in a ".env" file:
          
MYSQL_HOST=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DB=
MYSQL_PORT=

- You have run 'update_player_csv.py' to add best_shot_id to player_cleaned.csv

# # # # # 
          
If you want to continue, press ENTER or stop via CTRL^C
          
         
""")
    input("->")
    print("🚀 Initializing database from CSVs ...")
    create_database()
    create_tables()
    
    # Insert data in correct order (parent tables before child tables)
    for table, file in CSV_MAP_ORDERED:
        insert_from_csv(table, file)
    
    # Verify foreign keys were created
    verify_foreign_keys()
    
    print("\n✅ Database fully created and populated with foreign key relationships.")