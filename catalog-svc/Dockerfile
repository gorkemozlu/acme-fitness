FROM bitnami/python:3.7

ENV CATALOG_DB_HOST="localhost"
ENV CATALOG_DB_PORT="27017"
ENV CATALOG_DB_USERNAME="mongoadmin"
ENV CATALOG_DB_PASSWORD="KeepItSimple1!"

ENV TRACER_HOST="localhost"
ENV TRACER_PORT="6832"
ENV JAEGER_HOST_AGENT="localhost"
ENV JAEGER_HOST_PORT="6832"

RUN wget https://downloads.mongodb.com/compass/mongosh-1.6.1-linux-x64.tgz && tar -zxvf mongosh-1.6.1-linux-x64.tgz && cp mongosh-1.6.1-linux-x64/bin/mongosh /usr/local/bin/mongo && chmod +x /usr/local/bin/mongo && rm -rf mongosh-1.6.1-linux-x64.tgz

ADD . /app
RUN chmod 777 /app/catalog
COPY entrypoint/docker-entrypoint.sh /usr/local/bin/
RUN chmod 777 /usr/local/bin/docker-entrypoint.sh

RUN ln -s /usr/local/bin/docker-entrypoint.sh /app # backwards compat

EXPOSE 8082
ENTRYPOINT ["docker-entrypoint.sh"]
#CMD ["python3", "cart.py"]