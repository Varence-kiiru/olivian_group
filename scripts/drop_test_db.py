import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so Django settings package can be imported
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olivian_solar.settings')
import django
django.setup()
from django.conf import settings

db = settings.DATABASES.get('default', {})
engine = db.get('ENGINE', '')

if 'mysql' not in engine:
    print('Default DB is not MySQL, nothing to drop.')
    sys.exit(0)

name = db.get('NAME', '')
if not name:
    print('No database name found in settings.')
    sys.exit(1)

if name.startswith('test_'):
    test_db = name
else:
    test_db = f"test_{name}"

user = db.get('USER', 'root')
password = db.get('PASSWORD', '')
host = db.get('HOST', 'localhost') or 'localhost'
port = int(db.get('PORT') or 3306)

print(f"Dropping test database: {test_db} (host={host} user={user})")

# Try MySQLdb first, fall back to pymysql
conn = None
try:
    import MySQLdb
    conn = MySQLdb.connect(host=host, user=user, passwd=password, port=port)
except Exception:
    try:
        import pymysql
        conn = pymysql.connect(host=host, user=user, password=password, port=port)
    except Exception as e:
        print('Could not connect to MySQL:', e)
        sys.exit(1)

try:
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS `{test_db}`;")
    print('Dropped database:', test_db)
    conn.commit()
except Exception as e:
    print('Error dropping database:', e)
    sys.exit(1)
finally:
    try:
        conn.close()
    except Exception:
        pass
