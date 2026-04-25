

-- [login]
SELECT * FROM users WHERE username = %s AND password = %s;

-- [register]
INSERT INTO users (username, password, email, is_developer) VALUES (%s, %s, %s, %s);

-- [browse_games]
SELECT g.*, d.name AS developer_name,
       CASE WHEN og.game_id IS NOT NULL THEN 1 ELSE 0 END AS is_owned,
       CASE WHEN fg.game_id IS NOT NULL THEN 1 ELSE 0 END AS is_favorite
FROM games g
LEFT JOIN developers d ON g.developer_id = d.developer_id
LEFT JOIN owned_games og ON g.game_id = og.game_id AND og.user_id = %s
LEFT JOIN favorite_games fg ON g.game_id = fg.game_id AND fg.user_id = %s;

-- [library_games]
SELECT g.*, d.name AS developer_name, 1 AS is_owned,
       CASE WHEN fg.game_id IS NOT NULL THEN 1 ELSE 0 END AS is_favorite
FROM games g
JOIN owned_games og ON g.game_id = og.game_id AND og.user_id = %s
LEFT JOIN developers d ON g.developer_id = d.developer_id
LEFT JOIN favorite_games fg ON g.game_id = fg.game_id AND fg.user_id = %s;

-- [favorite_games]
SELECT g.*, d.name AS developer_name, 1 AS is_favorite,
       CASE WHEN og.game_id IS NOT NULL THEN 1 ELSE 0 END AS is_owned
FROM games g
JOIN favorite_games fg ON g.game_id = fg.game_id AND fg.user_id = %s
LEFT JOIN developers d ON g.developer_id = d.developer_id
LEFT JOIN owned_games og ON g.game_id = og.game_id AND og.user_id = %s;

-- [add_to_favorites]
INSERT INTO favorite_games (user_id, game_id) VALUES (%s, %s);

-- [remove_from_favorites]
DELETE FROM favorite_games WHERE user_id = %s AND game_id = %s;

-- [add_to_library]
INSERT INTO owned_games (user_id, game_id) VALUES (%s, %s);

-- [get_reviews]
SELECT r.review_text, r.review_date, u.username
FROM reviews r
JOIN users u ON r.user_id = u.user_id
WHERE r.game_id = %s
ORDER BY r.review_date DESC;

-- [insert_review]
INSERT INTO reviews (user_id, game_id, review_text) VALUES (%s, %s, %s);

-- [get_developer_by_name]
SELECT developer_id FROM developers WHERE name = %s;

-- [insert_developer]
INSERT INTO developers (name) VALUES (%s);

-- [insert_game]
INSERT INTO games (title, genre, price, developer_id, link) VALUES (%s, %s, %s, %s, %s);

-- [get_user_email]
SELECT email FROM users WHERE user_id = %s;

-- [update_user_with_password]
UPDATE users SET username=%s, email=%s, password=%s WHERE user_id=%s;

-- [update_user_without_password]
UPDATE users SET username=%s, email=%s WHERE user_id=%s;
