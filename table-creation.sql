CREATE DATABASE game_library_db;
USE game_library_db;

CREATE TABLE users (
    user_id      INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(50)  UNIQUE NOT NULL,
    password     VARCHAR(255) NOT NULL,
    email        VARCHAR(100) UNIQUE,
    is_developer BOOLEAN DEFAULT FALSE
);

CREATE TABLE developers (
    developer_id INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE games (
    game_id      INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(150) NOT NULL,
    genre        VARCHAR(80),
    price        DECIMAL(6,2) DEFAULT 0.00,
    developer_id INT,
    link         VARCHAR(500),
    FOREIGN KEY (developer_id) REFERENCES developers(developer_id)
);

CREATE TABLE owned_games (
    user_id INT,
    game_id INT,
    PRIMARY KEY (user_id, game_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

CREATE TABLE favorite_games (
    user_id INT,
    game_id INT,
    PRIMARY KEY (user_id, game_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

CREATE TABLE reviews (
    review_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    game_id     INT,
    review_text TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);
