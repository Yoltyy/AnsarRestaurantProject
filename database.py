import sqlite3


def save_to_db(user_id, date, time, guests, preference):
    conn = sqlite3.connect('rest_booking.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            time TEXT,
            guests INTEGER,
            preference TEXT
        )
    ''')

    cursor.execute('''
        INSERT INTO reservations (user_id, date, time, guests, preference)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, date, time, guests, preference))

    conn.commit()
    conn.close()


def get_reservations(user_id):
    conn = sqlite3.connect('rest_booking.db')
    cursor = conn.cursor()

    cursor.execute('SELECT date, time, guests, preference FROM reservations WHERE user_id = ?', (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def del_from_db(user_id):
    conn = sqlite3.connect('rest_booking.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM reservations WHERE user_id = ?', (user_id,))

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count