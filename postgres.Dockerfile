FROM postgres:9.6
ADD schema.sh /docker-entrypoint-initdb.d/init.sh
RUN chmod 0755 /docker-entrypoint-initdb.d/init.sh
RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/pg_hba.conf
RUN echo "listen_addresses='*'" >> /var/lib/postgresql/postgresql.conf
EXPOSE 5432