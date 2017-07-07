CREATE TABLE gdq_timeseries(
    time TIMESTAMP WITH TIME ZONE PRIMARY KEY,
    num_viewers INTEGER DEFAULT -1,
    num_tweets INTEGER DEFAULT -1,
    num_chats INTEGER DEFAULT -1,
    num_emotes INTEGER DEFAULT -1,
    num_donations INTEGER DEFAULT -1,
    total_donations NUMERIC(20, 2) DEFAULT -1
);

CREATE TABLE gdq_schedule(
    name TEXT PRIMARY KEY,
    start_time TIMESTAMP, 
    duration INTERVAL,
    runners TEXT
);

CREATE TABLE gdq_tweets(
    id BIGINT PRIMARY KEY,
    user_id BIGINT,
    created_at TIMESTAMP,
    username TEXT,
    content TEXT
);

CREATE TABLE gdq_chats(
    id SERIAL PRIMARY KEY,
    content TEXT,
    username TEXT,
    created_at TIMESTAMP
);

CREATE TABLE gdq_animals(
    kill NUMERIC(20, 2),
    save NUMERIC(20, 2),
    time TIMESTAMP
);

CREATE TABLE gdq_donations(
    created_at TIMESTAMP,
    donation_id BIGINT PRIMARY KEY,
    donor_name TEXT,
    amount NUMERIC(20, 2),
    donor_id BIGINT,
    has_comment BOOLEAN,
    comment TEXT
);
