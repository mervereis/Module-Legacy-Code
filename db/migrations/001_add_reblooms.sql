CREATE TABLE IF NOT EXISTS reblooms (
    id SERIAL PRIMARY KEY,
    rebloomer_id INT NOT NULL REFERENCES users(id),
    bloom_id BIGINT NOT NULL REFERENCES blooms(id),
    rebloom_timestamp TIMESTAMP NOT NULL,
    UNIQUE(rebloomer_id, bloom_id)
);