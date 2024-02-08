import psycopg2
from datetime import date
conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="12345678abcD&", port=5432)
cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(50),
        password VARCHAR(50)
    )
''')

# Création de la table Article
cur.execute('''
    CREATE TABLE IF NOT EXISTS article (
        article_id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        article_date DATE,
        admin_id INT REFERENCES admin(id) 
        
    )
''')
cur.execute('''
    ALTER TABLE article
    ADD COLUMN image_path VARCHAR(255);
 
''')


cur.execute('''
    INSERT INTO article  (name, email, password) VALUES
    ('John Doe', 'john.doe@example.com', 'johns_password'),
    ('Jane Smith', 'jane.smith@example.com', 'janes_password'),
    ('Bob Johnson', 'bob.johnson@example.com', 'bobs_password')
''')
cur.execute('''
    INSERT INTO article (title, description, image_data, article_date, admin_id) VALUES
    ('Premier Article', 'Ceci est le premier article.', NULL, CURRENT_DATE, 1),
    ('Deuxième Article', 'Ceci est le deuxième article.', NULL, CURRENT_DATE, 2),
    ('Troisième Article', 'Ceci est le troisième article.', NULL, CURRENT_DATE, 3)
''')





conn.commit()
cur.close()
conn.close()