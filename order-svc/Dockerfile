FROM python:3.6-alpine


ENV ORDER_DB_HOST="localhost"
ENV ORDER_DB_PORT="5432"
ENV ORDER_DB_PASSWORD="password"
ENV ORDER_DB_USERNAME="postgres"
ENV PGPASSWORD="password"
ENV ORDER_AUTH_DB="postgres"
ENV PAYMENT_HOST="localhost"
ENV PAYMENT_PORT="9000"

RUN apk update 
RUN apk --no-cache add build-base 
RUN apk --no-cache add postgresql-dev

RUN pip3 install psycopg2

RUN apk add postgresql-client

RUN pip3 install flask
RUN pip3 install flask_httpauth
RUN pip3 install requests
RUN pip3 install SQLAlchemy
RUN pip3 install opentracing
RUN pip3 install jaeger_client

WORKDIR /app
ADD . /app
COPY entrypoint/docker-entrypoint.sh /usr/local/bin/
RUN chmod 777 /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh /app # backwards compat

COPY ./requirements.txt /app/requirements.txt
#RUN pip3 install -r requirements.txt
EXPOSE 5000
ENTRYPOINT ["docker-entrypoint.sh"]
#CMD ["python3", "order.py"]
