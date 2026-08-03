from werkzeug.security import generate_password_hash
from backend.db import get_connection
from backend.core.config import Config
from backend.users.uid import format_user_uid, make_pending_user_uid


def create_database():
    print(f"Creating database if needed: {Config.DB_NAME}")
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
    print("Creating tables if needed")
    conn = get_connection(use_database=True)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                uid VARCHAR(20) NOT NULL UNIQUE,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'normal') NOT NULL DEFAULT 'normal',
                status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
                last_login_at DATETIME NULL,
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

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS flight_scripts (
                id INT PRIMARY KEY AUTO_INCREMENT,
                script_code VARCHAR(20) NOT NULL UNIQUE,
                owner_user_id INT NULL,
                name VARCHAR(100) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                scope ENUM('private', 'public') NOT NULL DEFAULT 'private',
                status ENUM('active', 'disabled', 'deleted') NOT NULL DEFAULT 'active',
                description TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                KEY idx_flight_scripts_owner (owner_user_id),
                KEY idx_flight_scripts_scope (scope),
                KEY idx_flight_scripts_status (status)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_tasks (
                id INT PRIMARY KEY AUTO_INCREMENT,
                task_code VARCHAR(20) NOT NULL UNIQUE,
                user_id INT NOT NULL,
                user_uid VARCHAR(20) NOT NULL,
                script_code VARCHAR(20) NOT NULL,
                subject VARCHAR(100) NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                report_template_code VARCHAR(50) NOT NULL DEFAULT 'standard',
                output_parameters_json TEXT,
                output_directory VARCHAR(500) NOT NULL,
                status ENUM(
                    'queued',
                    'running',
                    'reporting',
                    'succeeded',
                    'succeeded_with_warnings',
                    'failed',
                    'cancelled'
                ) NOT NULL DEFAULT 'queued',
                progress INT NOT NULL DEFAULT 0,
                failed_points INT NOT NULL DEFAULT 0,
                message VARCHAR(255) NOT NULL DEFAULT 'Simulation task queued',
                error_message TEXT,
                submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME NULL,
                finished_at DATETIME NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                KEY idx_simulation_tasks_user (user_id),
                KEY idx_simulation_tasks_script (script_code),
                KEY idx_simulation_tasks_status (status),
                KEY idx_simulation_tasks_submitted_at (submitted_at)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_artifacts (
                id INT PRIMARY KEY AUTO_INCREMENT,
                artifact_code VARCHAR(100) NOT NULL UNIQUE,
                task_code VARCHAR(20) NOT NULL,
                artifact_type VARCHAR(50) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                KEY idx_simulation_artifacts_task (task_code),
                KEY idx_simulation_artifacts_type (artifact_type)
            );
            """)

        conn.commit()
    finally:
        conn.close()


def create_default_admin():
    print(f"Ensuring default admin exists: {Config.DEFAULT_ADMIN_USERNAME}")
    conn = get_connection(use_database=True)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (Config.DEFAULT_ADMIN_USERNAME,))
            admin = cursor.fetchone()

            if admin is None:
                password_hash = generate_password_hash(Config.DEFAULT_ADMIN_PASSWORD)
                pending_uid = make_pending_user_uid()
                cursor.execute("""
                INSERT INTO users (uid, username, password_hash, role, status)
                VALUES (%s, %s, %s, %s, %s)
                """, (pending_uid, Config.DEFAULT_ADMIN_USERNAME, password_hash, "admin", "active"))

                user_id = cursor.lastrowid
                cursor.execute("""
                UPDATE users
                SET uid = %s
                WHERE id = %s
                """, (format_user_uid(user_id), user_id))
                print("Default admin created")
            else:
                print("Default admin already exists")

        conn.commit()
    finally:
        conn.close()


def init_database():
    create_database()
    create_tables()
    create_default_admin()
    print("Database initialization complete")


if __name__ == "__main__":
    init_database()
