CREATE TABLE agdq_timeseries(
    time timestamp PRIMARY KEY,
    num_tweets integer,
    num_chats integer,
    num_emotes integer,
    num_donations integer,
    total_donations numeric(20, 2),
    max_donation numeric(20, 2)
);

CREATE TABLE agdq_schedule(
    name text PRIMARY KEY,
    start_time timestamp, 
    duration interval,
    runners text
);