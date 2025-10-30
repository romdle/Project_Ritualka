import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Добавляем новую колонку
cursor.execute('ALTER TABLE database ADD COLUMN image_path TEXT')

# Сохраняем изменения
conn.commit()

# Закрываем соединение
conn.close()