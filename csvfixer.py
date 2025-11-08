import pandas as pd
from pathlib import Path

# ---------------- CONFIG ---------------- #
CSV_DIR = Path("./csv_files")
PLAYER_CSV = CSV_DIR / "player_cleaned.csv"
SHOT_CSV = CSV_DIR / "shot_data_cleaned.csv"
OUTPUT_CSV = CSV_DIR / "player_cleaned2.csv"  # Will overwrite original
# ---------------------------------------- #


def add_best_shot_to_player_csv():
    """
    Add best_shot_id column to player CSV based on highest xG shot per player
    """
    
    # Check if files exist
    if not PLAYER_CSV.exists():
        print(f"❌ File not found: {PLAYER_CSV}")
        return
    
    if not SHOT_CSV.exists():
        print(f"❌ File not found: {SHOT_CSV}")
        return
    
    print("📊 Reading player_cleaned.csv...")
    df_player = pd.read_csv(PLAYER_CSV)
    
    print("📊 Reading shot_data_cleaned.csv...")
    df_shots = pd.read_csv(SHOT_CSV)
    
    # Find xG column (handle case variations)
    xg_col = None
    for col in df_shots.columns:
        if col.lower() == 'xg':
            xg_col = col
            break
    
    if xg_col is None:
        print("❌ Could not find xG column in shot_data")
        return
    
    print(f"🎯 Finding best shot (highest {xg_col}) for each player...")
    
    # Group by player_id and find the shot with max xG
    best_shots = df_shots.loc[df_shots.groupby('player_id')[xg_col].idxmax()]
    best_shots = best_shots[['player_id', 'shot_id', xg_col]].rename(columns={'shot_id': 'best_shot_id'})
    
    print(f"📈 Found best shots for {len(best_shots)} unique players.")
    
    # Merge with player data
    df_player_updated = df_player.merge(
        best_shots[['player_id', 'best_shot_id']], 
        on='player_id', 
        how='left'
    )
    
    # Convert to integer where not null
    df_player_updated['best_shot_id'] = df_player_updated['best_shot_id'].astype('Int64')
    
    # Remove any unnamed columns that might have been created
    df_player_updated = df_player_updated.loc[:, ~df_player_updated.columns.str.contains('^Unnamed', case=False, na=False)]
    
    # Save back to CSV (without index to avoid creating Unnamed columns)
    df_player_updated.to_csv(OUTPUT_CSV, index=False)
    
    print(f"✅ Updated player CSV saved to: {OUTPUT_CSV}")
    print(f"   Total players: {len(df_player_updated)}")
    print(f"   Players with best_shot_id: {df_player_updated['best_shot_id'].notna().sum()}")
    print(f"   Players without best_shot_id: {df_player_updated['best_shot_id'].isna().sum()}")
    
    # Show a sample
    print("\n📋 Sample of updated data:")
    sample = df_player_updated[['player_id', 'player_name', 'best_shot_id']].head(10)
    print(sample.to_string(index=False))


if __name__ == "__main__":
    print("🚀 Adding best_shot_id to player_cleaned.csv...\n")
    add_best_shot_to_player_csv()
    print("\n✅ Done! You can now run the database initializer.")