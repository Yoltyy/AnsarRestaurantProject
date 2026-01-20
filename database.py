import sqlite3


def init_db():
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

    conn.commit()
    conn.close()


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


def check_table_availability(date: str, time: str, table_type: str) -> bool:
    conn = sqlite3.connect('rest_booking.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 1 FROM reservations 
        WHERE date = ? AND time = ? AND preference = ?
    ''', (date, time, table_type))

    result = cursor.fetchone()
    conn.close()

    return result is None

def is_time_available(date: str, time: str) -> bool:
    conn = sqlite3.connect('rest_booking.db')
    cursor = conn.cursor()

    cursor.execute('SELECT 1 FROM reservations WHERE date = ? AND time = ?',
                   (date, time))
    result = cursor.fetchone()

    conn.close()
    return result is None