import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='aml', password='aml123', database='aml')
cursor = conn.cursor()
cursor.execute("DELETE FROM agents WHERE agent_code LIKE 'STAGE8%'")
conn.commit()
print('Test agents cleaned up')
cursor.execute("SELECT COUNT(*) FROM agents")
print(f'Agents count: {cursor.fetchone()[0]}')
conn.close()
