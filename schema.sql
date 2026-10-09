CREATE DATABASE IF NOT EXISTS sevaqueue
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'sevaqueue'@'localhost' IDENTIFIED BY 'CHANGE_THIS_DB_PASSWORD';
GRANT ALL PRIVILEGES ON sevaqueue.* TO 'sevaqueue'@'localhost';
FLUSH PRIVILEGES;

USE sevaqueue;

-- Flask-SQLAlchemy creates the user and appointment tables with:
--   flask --app app init-db
-- This file creates the database and a dedicated local development user.
