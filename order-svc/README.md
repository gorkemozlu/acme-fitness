# order server

This server is part of the new polygot acme fitness online store.
This will help interact with the catalog, front-end, and make calls to the order services.
It is meant to be run with mongo.

## pre-requirements

* Python 3.7.2<br>
* py-mongo 3.7.2<br>
* python libraries in requirements.txt<br>
* mongodb - must be installed and running either in a docker container or locally<br>
* payment service (if not there it has a built in "fake" payment service which returns with a positive result everytime)<br>
<br>
NOTE: Payment service must be up before order otherwise it will result in connecting to a fake payment service

## docker image build & run

```
git clone directory
```

If you want to run ALPINE LINUX:

```
cp Dockerfile.Alpine Dockerfile
docker build -t order-service .
```

Ensure redis is installed and running locally on port 6379

```
docker run -p 5000:5000 order-service
```

Environment Variables for docker container:\
* ENV ORDER_DB_HOST (default value is "localhost" if not set)\
* ENV ORDER_DB_PORT (default value is "27017" if not set)\
* ENV ORDER_DB_PASSWORD (default value is "" if not set)\
* ENV ORDER_DB_USERNAME (default value is "" if not set)\
* ENV PAYMENT_HOST (default value is 'localhost' if not set)\
* ENV PAYMENT_PORT (default value is 9000 if not set)\
* ENV ORDER_PORT {default value is 5000 if not set}

## api summary

> Get all orders for a specific userid<br>

**'/order/\<userid\>', methods=['GET']**<br>

> Get all orders in the system<br>

**'/order/all', methods=['GET']**<br>

> Add order for a specific user and run payment<br>

**'/order/add/\<userid\>', methods=['GET', 'POST']**<br>

> Expected input - see order.json file<br>

> Typical output -<br> 
```json
{
    "order_id": "ea5ed52e-3c4e-11e9-9aff-e62b216188c4",
    "payment": {
        "amount": "100",
        "message": "Payment processed",
        "success": "true",
        "transactionID": "jefugyifjgpxbah"
    },
    "userid": "7892"
}
```

