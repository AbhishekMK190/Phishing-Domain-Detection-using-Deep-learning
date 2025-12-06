"""
Script to clear cache for specific domains that should be trusted
"""
import sqlite3
import os

def clear_domain_cache(domain):
    """Clear cache and predictions for a specific domain"""
    db_path = 'predictions.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # Check current predictions for this domain
        cur.execute("SELECT id, domain, label, score FROM predictions WHERE domain = ?", (domain,))
        rows = cur.fetchall()
        
        if rows:
            print(f"Found {len(rows)} predictions for {domain}:")
            for row in rows:
                print(f"  ID: {row[0]}, Domain: {row[1]}, Label: {row[2]}, Score: {row[3]}")
            
            # Delete predictions for this domain
            cur.execute("DELETE FROM predictions WHERE domain = ?", (domain,))
            deleted_count = cur.rowcount
            print(f"Deleted {deleted_count} predictions for {domain}")
            
            conn.commit()
        else:
            print(f"No predictions found for {domain}")
            
        # Also check with trailing slash
        domain_with_slash = domain + '/'
        cur.execute("SELECT id, domain, label, score FROM predictions WHERE domain = ?", (domain_with_slash,))
        rows = cur.fetchall()
        
        if rows:
            print(f"Found {len(rows)} predictions for {domain_with_slash}:")
            for row in rows:
                print(f"  ID: {row[0]}, Domain: {row[1]}, Label: {row[2]}, Score: {row[3]}")
            
            # Delete predictions for this domain
            cur.execute("DELETE FROM predictions WHERE domain = ?", (domain_with_slash,))
            deleted_count = cur.rowcount
            print(f"Deleted {deleted_count} predictions for {domain_with_slash}")
            
            conn.commit()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Clear cache for Google domains that should be trusted
    domains_to_clear = [
        'mail.google.com',
        'mail.google.com/',
        'google.com',
        'gmail.com'
    ]
    
    for domain in domains_to_clear:
        print(f"\n=== Clearing cache for {domain} ===")
        clear_domain_cache(domain)
