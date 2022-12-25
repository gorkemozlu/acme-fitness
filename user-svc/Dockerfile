FROM bitnami/python:3.7

ENV REDIS_HOST="localhost"
ENV REDIS_PORT="6379"
ENV REDIS_PASSWORD=""

ENV TRACER_HOST="localhost"
ENV TRACER_PORT="6832"
ENV JAEGER_HOST_AGENT="localhost"
ENV JAEGER_HOST_PORT="6832"

# needed for redis-cli ; the server is not used
RUN install_packages redis-server
RUN wget https://downloads.mongodb.com/compass/mongosh-1.6.1-linux-x64.tgz && tar -zxvf mongosh-1.6.1-linux-x64.tgz && cp mongosh-1.6.1-linux-x64/bin/mongosh /usr/local/bin/mongo && chmod +x /usr/local/bin/mongo && rm -rf mongosh-1.6.1-linux-x64.tgz

ADD . /app
RUN chmod 777 /app/user
COPY entrypoint/docker-entrypoint.sh /usr/local/bin/
RUN chmod 777 /usr/local/bin/docker-entrypoint.sh

RUN ln -s /usr/local/bin/docker-entrypoint.sh /app # backwards compat

EXPOSE 8083
ENTRYPOINT ["docker-entrypoint.sh"]
#CMD ["python3", "cart.py"]