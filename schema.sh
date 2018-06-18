#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE TABLE gdq_timeseries(
      time TIMESTAMP WITH TIME ZONE PRIMARY KEY,
      num_viewers INTEGER,
      num_tweets INTEGER,
      num_chats INTEGER,
      num_emotes INTEGER,
      num_donations INTEGER,
      total_donations NUMERIC(20, 2)
  );

  CREATE TABLE gdq_schedule(
      name TEXT NOT NULL,
      category TEXT NOT NULL,
      start_time TIMESTAMP, 
      duration INTERVAL,
      runners TEXT,
      host TEXT,
      id SERIAL,
      PRIMARY KEY(name, category)
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

  /* Custom Aggregations 
   * Median from https://wiki.postgresql.org/wiki/Aggregate_Median
   * */

  CREATE OR REPLACE FUNCTION _final_median(NUMERIC[])
     RETURNS NUMERIC AS
  \$\$
     SELECT AVG(val)
     FROM (
       SELECT val
       FROM unnest(\$1) val
       ORDER BY 1
       LIMIT  2 - MOD(array_upper(\$1, 1), 2)
       OFFSET CEIL(array_upper(\$1, 1) / 2.0) - 1
     ) sub;
  \$\$
  LANGUAGE 'sql' IMMUTABLE;
   
  CREATE AGGREGATE median(NUMERIC) (
    SFUNC=array_append,
    STYPE=NUMERIC[],
    FINALFUNC=_final_median,
    INITCOND='{}'
  );

  /* Custom search dictionary settings from https://stackoverflow.com/a/42063785/2421634 */
  CREATE TEXT SEARCH DICTIONARY simple_english
     (TEMPLATE = pg_catalog.simple, STOPWORDS = english);

  CREATE TEXT SEARCH CONFIGURATION simple_english
     (copy = english);
  ALTER TEXT SEARCH CONFIGURATION simple_english
     ALTER MAPPING FOR asciihword, asciiword, hword, hword_asciipart, hword_part, word
     WITH simple_english;
EOSQL