import sqlite3

# Connect to database
conn = sqlite3.connect('predictions.db')
cur = conn.cursor()

# Check feedback data
print("=== Recent Feedback ===")
try:
    cur.execute('SELECT id, domain, vote, created_at FROM feedbacks ORDER BY id DESC LIMIT 5')
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"ID: {row[0]}, Domain: '{row[1]}', Vote: {row[2]}, Time: {row[3]}")
    else:
        print("No feedback data found")
except Exception as e:
    print(f"Error reading feedbacks: {e}")

# Check predictions for mail.google.com specifically
print("\n=== Mail.Google.com Predictions ===")
try:
    cur.execute("SELECT domain, label, score, created_at FROM predictions WHERE domain LIKE '%google%' ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"Domain: '{row[0]}', Label: {row[1]}, Score: {row[2]}, Time: {row[3]}")
    else:
        print("No Google-related predictions found")
except Exception as e:
    print(f"Error reading Google predictions: {e}")

# Check retraining log
print("\n=== Retraining Log ===")
try:
    cur.execute('SELECT timestamp, success, training_samples, reason FROM retraining_log ORDER BY id DESC LIMIT 3')
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"Time: {row[0]}, Success: {row[1]}, Samples: {row[2]}, Reason: {row[3]}")
    else:
        print("No retraining log found")
except Exception as e:
    print(f"Error reading retraining_log: {e}")

# Check feedback count by vote
print("\n=== Feedback Summary ===")
try:
    cur.execute('SELECT vote, COUNT(*) FROM feedbacks GROUP BY vote')
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"{row[0]}: {row[1]} votes")
    else:
        print("No feedback votes found")
except Exception as e:
    print(f"Error reading feedback summary: {e}")

conn.close()
