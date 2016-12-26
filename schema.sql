CREATE TABLE agdq_timeseries(
    time timestamp with time zone PRIMARY KEY,
    num_viewers integer default -1,
    num_tweets integer default -1,
    num_chats integer default -1,
    num_emotes integer default -1,
    num_donations integer default -1,
    total_donations numeric(20, 2) default -1,
    max_donation numeric(20, 2) default -1
);

CREATE TABLE agdq_schedule(
    name text PRIMARY KEY,
    start_time timestamp, 
    duration interval,
    runners text
);