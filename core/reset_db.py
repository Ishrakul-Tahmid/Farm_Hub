from django.db import connection; cursor = connection.cursor(); cursor.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
