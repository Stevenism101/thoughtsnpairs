"""
Run this once to:
  1. Add new columns (item_3..item_7, prep_note) to the pairing table
  2. Delete duplicate pairings (keeping the oldest by id)
  3. Reset all ratings to avg_rating=0 and delete all Rating rows
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'foodpairing.db')

def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # # 1. Add new columns if they don't exist
    # existing = {row[1] for row in cur.execute("PRAGMA table_info(pairing)")}
    # new_cols = {
    #     'item_3': "VARCHAR(100) DEFAULT ''",
    #     'item_4': "VARCHAR(100) DEFAULT ''",
    #     'item_5': "VARCHAR(100) DEFAULT ''",
    #     'item_6': "VARCHAR(100) DEFAULT ''",
    #     'item_7': "VARCHAR(100) DEFAULT ''",
    #     'prep_note': "TEXT DEFAULT ''",
    # }
    # for col, col_def in new_cols.items():
    #     if col not in existing:
    #         cur.execute(f"ALTER TABLE pairing ADD COLUMN {col} {col_def}")
    #         print(f"  + Added column: {col}")
    #     else:
    #         print(f"  · Column already exists: {col}")

    # 2. Delete duplicates — keep lowest id per title
    cur.execute("""
        DELETE FROM pairing
        WHERE id NOT IN (
            SELECT MIN(id) FROM pairing GROUP BY title
        )
    """)
    deleted = conn.total_changes
    print(f"  - Deleted {deleted} duplicate pairing(s)")

    # # 3. Delete all ratings and reset avg_rating to 0
    # cur.execute("DELETE FROM rating")
    # cur.execute("UPDATE pairing SET avg_rating = 0.0")
    # print("  - Deleted all ratings, reset avg_rating to 0")

    conn.commit()
    conn.close()
    print("Done.")

if __name__ == '__main__':
    run()
