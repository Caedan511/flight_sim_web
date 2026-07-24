from werkzeug.security import generate_password_hash
from backend.db import get_connection
from config import Config


def create_database():
    conn = get_connection(use_database=False)
    try:
        with conn.cursor() as cursor:
            sql = f"""
            CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}`
            DEFAULT CHARACTER SET utf8mb4
            DEFAULT COLLATE utf8mb4_unicode_ci;
            """
            cursor.execute(sql)
        conn.commit()
    finally:
        conn.close()


def create_tables():
    conn = get_connection(use_database=True)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'normal') NOT NULL DEFAULT 'normal',
                status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_versions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                version VARCHAR(50) NOT NULL UNIQUE,
                model_name VARCHAR(100) NOT NULL,
                model_path VARCHAR(255) NOT NULL,
                description TEXT,
                status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
                access_scope ENUM('private', 'all_users') NOT NULL DEFAULT 'private',
                created_by INT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                KEY idx_model_versions_created_by (created_by)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_version_permissions (
                id INT PRIMARY KEY AUTO_INCREMENT,
                model_version_id INT NOT NULL,
                user_id INT NOT NULL,
                can_use TINYINT NOT NULL DEFAULT 1,
                granted_by INT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_model_version_user (model_version_id, user_id),
                KEY idx_model_permission_user (user_id),
                KEY idx_model_permission_granted_by (granted_by)
            );
            """)

            # cursor.execute("""
            # CREATE TABLE IF NOT EXISTS simulation_tasks (
            #     id INT PRIMARY KEY AUTO_INCREMENT,
            #     task_id VARCHAR(100) NOT NULL UNIQUE,
            #     username VARCHAR(50) NOT NULL,
            #     model_version VARCHAR(50) NOT NULL,
            #     status ENUM('queued', 'running', 'success', 'failed') NOT NULL DEFAULT 'queued',
            #     queue_position INT DEFAULT NULL,
            #     script_path VARCHAR(255),
            #     result_path VARCHAR(255),
            #     report_path VARCHAR(255),
            #     error_message TEXT,
            #     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            #     started_at DATETIME NULL,
            #     finished_at DATETIME NULL
            # );
            # """)

        conn.commit()
    finally:
        conn.close()


def create_default_admin():
    conn = get_connection(use_database=True)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
            admin = cursor.fetchone()

            if admin is None:
                password_hash = generate_password_hash("admin123")
                cursor.execute("""
                INSERT INTO users (username, password_hash, role, status)
                VALUES (%s, %s, %s, %s)
                """, ("admin", password_hash, "admin", "active"))

        conn.commit()
    finally:
        conn.close()


def init_database():
    create_database()
    create_tables()
    create_default_admin()
    print("Database initialization complete. Default administrator: admin / admin123")


if __name__ == "__main__":
    init_database()
