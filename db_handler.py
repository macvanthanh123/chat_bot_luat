import psycopg2
from psycopg2 import sql
import json
import os
from dotenv import load_dotenv
from logger import logger  

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
        logger.info("Khởi tạo PostgresHandler cho database: {}", self.db_name)

    def create_database(self):
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=self.pg_user,
                password=self.pg_pwd,
                host=self.pg_host,
                port=self.pg_port,
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name))
            )
            logger.info("Đã tạo database '{}'", self.db_name)
        except psycopg2.errors.DuplicateDatabase:
            logger.warning("Database '{}' đã tồn tại", self.db_name)
        except Exception as e:
            logger.exception("Lỗi khi tạo database: {}", e)
        finally:
            cursor.close()
            conn.close()

    def connect(self):
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(
                    dbname=self.db_name,
                    user=self.pg_user,
                    password=self.pg_pwd,
                    host=self.pg_host,
                    port=self.pg_port,
                )
                self.cursor = self.conn.cursor()
                logger.debug("Kết nối đến database thành công")
        except Exception as e:
            logger.exception("Lỗi khi kết nối database: {}", e)
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.debug("🔌 Đã đóng kết nối đến database")

    def create_articles_table(self):
        try:
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
            logger.info("Bảng 'articles' đã sẵn sàng")
        except Exception as e:
            logger.exception("Lỗi khi tạo bảng articles: {}", e)

    def create_chunks_table(self):
        try:
            self.connect()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    doc_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
                    chunk_id INTEGER,
                    title TEXT,
                    markdown TEXT,
                    vector JSONB,
                    PRIMARY KEY (doc_id, chunk_id)
                )
            """)
            self.conn.commit()
            logger.info("Bảng 'chunks' đã sẵn sàng (dùng vector dạng JSON)")
        except Exception as e:
            logger.exception("Lỗi khi tạo bảng chunks: {}", e)

    def insert_article(self, data):
        try:
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
            logger.info("Đã chèn article với id={}", article_id)
            return article_id
        except Exception as e:
            logger.exception("Lỗi khi insert article: {}", e)
            raise

    def insert_chunks(self, doc_id, chunks):
        try:
            self.connect()
            for chunk in chunks:
                self.cursor.execute("""
                    INSERT INTO chunks (doc_id, chunk_id, title, markdown, vector)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (doc_id, chunk_id) DO NOTHING
                """, (
                    chunk.get("doc_id", doc_id),
                    chunk.get("chunk_id"),
                    chunk.get("title", ""),
                    chunk.get("markdown", ""),
                    json.dumps(chunk.get("vector")) if chunk.get("vector") else None
                ))
            self.conn.commit()
            logger.info("Đã lưu {} chunks cho doc_id={}", len(chunks), doc_id)
        except Exception as e:
            logger.exception("Lỗi khi insert chunks: {}", e)
            raise

    def export_to_json(self, filename="result.json"):
        try:
            self.connect()
            self.cursor.execute("SELECT * FROM articles")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            result = [dict(zip(columns, row)) for row in rows]

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info("Đã xuất dữ liệu articles ra file {}", filename)
        except Exception as e:
            logger.exception("Lỗi khi export dữ liệu: {}", e)

    def fetch_all_articles(self):
        try:
            self.connect()
            self.cursor.execute("SELECT * FROM articles ORDER BY id")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            logger.debug("Đã fetch {} articles", len(rows))
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.exception("Lỗi khi lấy tất cả articles: {}", e)
            return []

    def fetch_article_by_id(self, article_id):
        try:
            self.connect()
            self.cursor.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
            row = self.cursor.fetchone()
            if row:
                columns = [desc[0] for desc in self.cursor.description]
                logger.debug("Đã tìm thấy article id={}", article_id)
                return dict(zip(columns, row))
            logger.warning("Không tìm thấy article id={}", article_id)
            return None
        except Exception as e:
            logger.exception("Lỗi khi lấy article theo id: {}", e)
            return None

    def fetch_chunks_by_doc_id(self, doc_id):
        try:
            self.connect()
            self.cursor.execute("SELECT * FROM chunks WHERE doc_id = %s ORDER BY chunk_id", (doc_id,))
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            logger.debug("Đã fetch {} chunks cho doc_id={}", len(rows), doc_id)
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.exception("Lỗi khi lấy chunks theo doc_id: {}", e)
            return []
