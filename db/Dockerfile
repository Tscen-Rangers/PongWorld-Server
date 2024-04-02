FROM postgres:14.10 

COPY ./start_postgres.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/start_postgres.sh

EXPOSE 5432

ENTRYPOINT ["/usr/local/bin/start_postgres.sh"]