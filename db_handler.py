import psycopg2
from psycopg2 import sql
import json
import os
from dotenv import load_dotenv

load_dotenv()


class PostgresHandler:
    def __init__(self):
        self.pg_user = os.getenv("PG_USER")
        self.pg_pwd = os.getenv("PG_PWD")
        self.pg_host = os.getenv("PG_HOST")
        self.pg_port = os.getenv("PG_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.conn = None
        self.cursor = None

    def create_database(self):
        conn = psycopg2.connect(
            dbname="postgres",
            user=self.pg_user,
            password=self.pg_pwd,
            host=self.pg_host,
            port=self.pg_port,
        )
        conn.autocommit = True
        cursor = conn.cursor()
        try:
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name))
            )
            print(f"[INFO] Database '{self.db_name}' created.")
        except psycopg2.errors.DuplicateDatabase:
            print(f"[WARN] Database '{self.db_name}' already exists.")
        cursor.close()
        conn.close()

    def connect(self):
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.pg_user,
                password=self.pg_pwd,
                host=self.pg_host,
                port=self.pg_port,
            )
            self.cursor = self.conn.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_articles_table(self):
        self.connect()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            url TEXT,
            title TEXT,
            date TEXT,
            markdown TEXT,
            text TEXT,
            images TEXT[]
        )
        """)
        self.conn.commit()
        print("[INFO] Bảng 'articles' đã sẵn sàng.")

    def create_chunks_table(self):
        self.connect()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            doc_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            chunk_id INTEGER,
            title TEXT,
            content TEXT,
            vector JSONB,
            PRIMARY KEY (doc_id, chunk_id)
        )
        """)
        self.conn.commit()
        print("[INFO] Bảng 'chunks' đã sẵn sàng (vector dạng JSON).")

    def insert_article(self, data):
        self.connect()
        self.cursor.execute("""
            INSERT INTO articles (url, title, date, markdown, text, images)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get("url", ""),
            data.get("title", ""),
            data.get("date", ""),
            data.get("markdown", ""),
            data.get("text", ""),
            data.get("images", []),
        ))
        article_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return article_id

    def insert_chunks(self, doc_id, chunks):
        self.connect()
        for chunk in chunks:
            self.cursor.execute("""
            INSERT INTO chunks (doc_id, chunk_id, title, content, vector)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (doc_id, chunk_id) DO NOTHING
            """, (
                chunk.get("doc_id", doc_id),
                chunk.get("chunk_id"),
                chunk.get("title", ""),
                chunk.get("content", ""),
                json.dumps(chunk.get("vector")) if chunk.get("vector") else None
            ))
        self.conn.commit()
        print(f"[INFO] Đã lưu {len(chunks)} chunks cho doc_id={doc_id}")

    def export_to_json(self, filename="result.json"):
        self.connect()
        self.cursor.execute("SELECT * FROM articles")
        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        result = [dict(zip(columns, row)) for row in rows]

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Đã lưu dữ liệu vào file {filename}")

    def fetch_all_articles(self):
        self.connect()
        self.cursor.execute("SELECT * FROM articles ORDER BY id")
        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def fetch_article_by_id(self, article_id):
        self.connect()
        self.cursor.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def fetch_chunks_by_doc_id(self, doc_id):
        self.connect()
        self.cursor.execute("SELECT * FROM chunks WHERE doc_id = %s ORDER BY chunk_id", (doc_id,))
        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
