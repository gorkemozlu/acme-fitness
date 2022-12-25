#!/usr/bin/python

#general imports
import json
import pickle
import os
import random
import sys
import datetime
import string
import requests
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, create_engine, inspect
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *

from lib.tracing import init_tracer
import opentracing
from opentracing.ext import tags
from opentracing.propagation import Format

#import sentry_sdk
#sentry_sdk.init("https://c0f58a327f2c4cd8b29e8cd0a606f0e9@sentry.io/1722363")


#Logging initialization
import logging
from logging.config import dictConfig
from logging.handlers import SysLogHandler

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi'],
        'propagate': True,
    }
})


#errorhandler for specific responses
class FoundIssue(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

#Uncomment below to turnon statsd
#from statsd import StatsClient
#statsd = StatsClient(host='localhost',
#                     port=8125,
#                     prefix='fitcycle-api-server',
#                     maxudpsize=512)


#initializing requests
from requests.auth import HTTPBasicAuth

#initializing flask
from flask import Flask, render_template, jsonify, flash, request
from flask import g,request
from flask_httpauth import HTTPTokenAuth

app = Flask(__name__)
app.debug=True
auth = HTTPTokenAuth('Bearer')

order_tracer = init_tracer('order')

@app.errorhandler(FoundIssue)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

#initializing postgres on localhost and port 27017
#If error terminates process- entire order is shut down
from os import environ

if environ.get('ORDER_DB_USERNAME') is not None:
    if os.environ['ORDER_DB_USERNAME'] != "":
        orderDbUser=os.environ['ORDER_DB_USERNAME']
    else:
        orderDbUser=''
else:
    orderDbUser=''

if environ.get('ORDER_DB_HOST') is not None:
    if os.environ['ORDER_DB_HOST'] != "":
        orderDbHost=os.environ['ORDER_DB_HOST']
    else:
        orderDbHost='localhost'
else:
    orderDbHost='localhost'

if environ.get('ORDER_DB_PORT') is not None:
    if os.environ['ORDER_DB_PORT'] != "":
        orderDbPort=os.environ['ORDER_DB_PORT']
    else:
        orderDbPort=5432
else:
    orderDbPort=5432

if environ.get('ORDER_DB_PASSWORD') is not None:
    if os.environ['ORDER_DB_PASSWORD'] != "":
        orderDbPassword=os.environ['ORDER_DB_PASSWORD']
    else:
        orderDbPassword=''
else:
    orderDbPassword=''

if environ.get('ORDER_AUTH_DB') is not None:
    if os.environ['ORDER_AUTH_DB'] != "":
        orderAuthDb=os.environ['ORDER_AUTH_DB']
    else:
        orderAuthDb='postgres'
else:
    orderAuthDb='postgres'

if environ.get('PAYMENT_HOST') is not None:
    if os.environ['PAYMENT_HOST'] != "":
        paymenthost=os.environ['PAYMENT_HOST']
    else:
        paymenthost='localhost'
else:
    paymenthost='localhost'

if environ.get('PAYMENT_PORT') is not None:
    if os.environ['PAYMENT_PORT'] != "":
        paymentport=os.environ['PAYMENT_PORT']
    else:
        paymentport='9000'
else:
    paymentport='9000'



if environ.get('ORDER_PORT') is not None:
    if os.environ['ORDER_PORT'] != "":
        orderport=os.environ['ORDER_PORT']
    else:
        orderport='5000'
else:
    orderport='5000'



if environ.get('USER_HOST') is not None:
    if os.environ['USER_HOST'] != "":
        userhost=os.environ['USER_HOST']
    else:
        userhost='localhost'
else:
    userhost='localhost'

if environ.get('USER_PORT') is not None:
    if os.environ['USER_PORT'] != "":
        userport=int(os.environ['USER_PORT'])
    else:
        userport=8081
else:
    userport=8081


if environ.get('AUTH_MODE') is not None:
    if os.environ['AUTH_MODE'] != "":
        authmode=int(os.environ['AUTH_MODE'])
        print("user service is ", authmode)
    else:
        authmode=1
else:
    authmode=1


#initializing requests
import requests
from requests.auth import HTTPBasicAuth

paymenturi='http://'+str(paymenthost)+':'+str(paymentport)

@auth.verify_token
def verify_token(token):

    global authmode

    headers={'content-type':'application/json'}
    verify_token_url="http://"+userhost+":"+str(userport)+"/verify-token"
    login_url="http://"+userhost+":"+str(userport)+"/login"

    app.logger.info("user service mode in verify_token is %s", authmode)
    if authmode == 2:
        print("using local version of user for test - getting token")

        data1=json.dumps({"username":"eric", "password":"vmware1!"})

        r=requests.post(login_url, headers=headers, data=data1)

        if r.status_code == 200:
            verify_token_payload=json.dumps({"access_token": json.loads(r.content)["access_token"]})
            r=requests.post(verify_token_url, headers=headers, data=verify_token_payload)
            if r.status_code == 200:
                app.logger.info('Authorized %s', json.loads(r.content)["message"])
                return True
            else:
                app.logger.info('Un-authorized %s', json.loads(r.content)["message"])
                return False
        else:
            app.logger.info('Bad user or password %s', json.loads(r.content)["message"])
            return False

    elif authmode == 1:
        if token == "":
            app.logger.info("No Bearer token sent")
            return False
        else:
            verify_token_payload=json.dumps({"access_token": token})
            r=requests.post(verify_token_url, headers=headers, data=verify_token_payload)
            if r.status_code == 200:
                app.logger.info('Authorized %s', json.loads(r.content)["message"])
                return True
            else:
                app.logger.info('Un-authorized %s', json.loads(r.content)["message"])
                return False

    else:
        return True

    return False


def testPayment():

    paymentup=0

    try:
        paymentreq = requests.get(paymenturi+'/live')
        paymentup=1
        app.logger.info("payment service up %s", paymentreq.status_code)
    except Exception as ex:
        paymentup=0
        app.logger.error('Error connecting to payment service %s', ex)

    return paymentup


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    id = Column(String, primary_key=True)
    date = Column(String)
    paid = Column(String)
    userid = Column(String)

# If using Citus then use this userID
#    userid = Column(String, primary_key=True)
#

    firstname = Column(String)
    lastname = Column(String)
    total = Column(Float)
    address = Column(JSONB)
    email = Column(String)
    delivery = Column(String)
    card=Column(JSONB)
    cart=Column(JSONB)

    def __repr__(self):
        return "<Order(date='{}', paid='{}', firstname={}, lastname={}, total={}, address={}, email={}, delivery={})>"\
                .format(self.date, self.paid, self.firstname, self.lastname, self.total, self.address, self.email, self.delivery)


postgresuri='postgresql://'+str(orderDbUser)+':'+str(orderDbPassword)+'@'+str(orderDbHost)+':'+str(orderDbPort)+'/'+str(orderAuthDb)


engine = create_engine(postgresuri)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

#Make composite key in the order object - i.e. add userID as the primary key also with the id as primary key also
#post table creation with a dual key for citus then need to api_for_running_sql_query_directly (“select create_distributed_table(‘orders’,'userid')”);
#The url for postgresuri will be different /postgres will be /citus
#postgres://citus:<password>@new-sai-c.postgres.database.azure.com:5432/citus
#psql cli run a 'explain plan'
#SELECT * from pg_dist_partition;  to see what tables are distributed
#Create distributed table


#Generates a random string for order id
def randomString(stringLength=15):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

#initialization of redis with fake data from the San Francisco legal offices of Shri, Dan and Bill SDB.
def insertInitialData():

    app.logger.info('inserting order')

    order = Order(
        id=str(uuid.uuid1()),
        date=str(datetime.datetime.utcnow()),
        paid='notyet',
        userid=str(uuid.uuid1()),
        firstname='zoe',
        lastname='shetti',
        total=120,
        address={ "street" : "20 San Pablo Av", "city" : "San Francisco", "zip" : "94127", "state" : "CA", "country" : "USA" },
        email="billshetti@gmail.com",
        delivery="tractor",
        card={ "type" : "amex", "number" : "1234567890123456", "ccv" : "9999", "expMonth" : "01", "expYear" : "2021" },
        cart="[{\"itemid\":\"5d38eafdb7a0b8f78558dccd\",\"name\":\"Fit Bike\",\"price\":\"499.99\",\"quantity\":3,\"shortDescription\":\"Get Light on our Fit Bike!\"},{\"itemid\":\"5d38eafdb7a0b8f78558dccc\",\"name\":\"Water Bottle\",\"price\":\"34.99\",\"quantity\":2,\"shortDescription\":\"The last Water Bottle you'll ever buy!\"},{\"itemid\":\"5d38eafdb7a0b8f78558dcd0\",\"name\":\"Red Pants\",\"price\":\"99\",\"quantity\":1,\"shortDescription\":\"Because who doesn't need red pants??\"},{\"itemid\":\"5d38eafdb7a0b8f78558dcce\",\"name\":\"Basket Ball\",\"price\":\"110.75\",\"quantity\":1,\"shortDescription\":\"World's Roundest Basketball!\"}]",
    )

    s=Session()
    try:
        s.add(order)
        s.commit()
        app.logger.info("Inserted order # %s", order.id)
    except Exception as e:
        app.logger.error("Could not insert initial data into postgres")
    finally:
        s.close()

def distributeDB():

    s=Session()
    app.logger.info("in function to distributing table")
    try:
        sqlcommand="SELECT create_distributed_table('orders','userid')"
        s.execute(sqlcommand)
        s.commit()
        app.logger.info("succeeded in distributing table")
    except Exception as e:
        app.logger.error("Could not distribute in DB", e)
    finally:
        s.close()



def convertOrder(document):

    order={}

    order["id"]=document.id
    order["date"]=document.date
    order["paid"]=document.paid
    order["firstname"]=document.firstname
    order["lastname"]=document.lastname
    order["userid"]=document.userid
    order["total"]=document.total
    order["email"]=document.email
    order["address"]=document.address
    order["delivery"]=document.delivery
    order["card"]=document.card
    order["cart"]=document.cart

    return order

#Gets specific order
def getOrder(orderid, spanC):

    functionName='/order/getOrder/function'

    with order_tracer.start_span(functionName, child_of=spanC ) as span:
        app.logger.info('/order/getOrder')

        with order_tracer.start_span('/postgres/selectOrder', child_of=span) as postgres_span:
            s=Session()
            document=s.query(Order).filter(Order.id==orderid).first()
            if document != None:
                unpacked_data = convertOrder(document)
                app.logger.info('got data from postgres')
            else:
                app.logger.info('empty - no postgres data for key %s', orderid)
                unpacked_data = 0

            s.close()

    return unpacked_data

#http call to gets all Items from a cart (userid)
#If successful this returns the cart and items, if not successfull (the user id is non-existant) - 204 returned

#@statsd.timer('getorderDbUser')
@app.route('/order/<userid>', methods=['GET'])
@auth.login_required
def getUserOrders(userid):

    span_ctx = order_tracer.extract(opentracing.Format.HTTP_HEADERS, carrier=request.headers)
    app.logger.info('the request headers are %s', str(request.headers))
    functionName='/order/<userid>'

    if span_ctx is None:
        app.logger.info('there is no context being passed for tracing or tracing if off')
    else:
        app.logger.info('there is context being passed %s', str(span_ctx))

    app.logger.info('getting all orders for user %s', userid)

    totalOrders = []
    order={}

    with order_tracer.start_span(functionName, child_of=span_ctx) as span:

        span.set_tag("userid", userid)

        with order_tracer.start_span('/postgres/selectOrder/', child_of=span) as postgres_span:
            s=Session()
            rows=s.query(Order).filter(Order.userid==userid).all()
            for document in rows:
                order=convertOrder(document)
                totalOrders.append(order)
                order={}
                s.close()

    return jsonify({'all orders': totalOrders})


#http call to get all orders and their values
#@statsd.timer('getAllOrders')
@app.route('/order/all', methods=['GET'])
@auth.login_required
def getAllOrders():

    span_ctx = order_tracer.extract(opentracing.Format.HTTP_HEADERS, carrier=request.headers)
    app.logger.info('the request headers are %s', str(request.headers))
    functionName='/order/all'

    if span_ctx is None:
        app.logger.info('there is no context being passed for tracing or tracing if off')
    else:
        app.logger.info('there is context being passed %s', str(span_ctx))

    app.logger.info('getting all orders')

    totalOrders = []
    order={}

    with order_tracer.start_span(functionName) as span:

        span.set_tag("scope", "all")

        with order_tracer.start_span('/postgres/selectOrder/', child_of=span) as postgres_span:
            s=Session()
            rows=s.query(Order).all()
            for document in rows:
                order=convertOrder(document)
                totalOrders.append(order)
                order={}

            s.close()

    return jsonify({'all orders': totalOrders})


#http call to create and order - doesn't look for another order. It essentially adds an order to the database
#once the order is paid (via payment the field "paid" is set to yes/no)
@app.route('/order/add/<userid>', methods=['GET', 'POST'])
@auth.login_required
def createOrder(userid):

    span_ctx = order_tracer.extract(opentracing.Format.HTTP_HEADERS, carrier=request.headers)
    app.logger.info('the request headers are %s', str(request.headers))
    functionName='/order/add/userid'

    if span_ctx is None:
        app.logger.info('there is no context being passed for tracing or tracing if off')
    else:
        app.logger.info('there is context being passed %s', str(span_ctx))

    app.logger.info('adding order for %s', userid)

    order_id=0
    paymentres={}

    with order_tracer.start_span(functionName, child_of=span_ctx) as span:

        span.set_tag("userid", userid)

        paymentup=0
        content = request.json

    #    content['_id']=randomString()

        order = Order(
            id=str(uuid.uuid1()),
            date=str(datetime.datetime.utcnow()),
            paid='pending',
            userid=userid,
            firstname=content['firstname'],
            lastname=content['lastname'],
            total=content['total'],
            address=content['address'],
            email=content['email'],
            delivery=content['delivery'],
            card=content['card'],
            cart=content['cart']
        )

        content['date']=str(datetime.datetime.utcnow())
        content['paid']="pending"
        transactionId="pending"
        order_id=0

        paymentres={}
        paymentPayload={}
        paymentPayload['card']=content['card']
        paymentPayload['firstname']=content['firstname']
        paymentPayload['lastname']=content['lastname']
        paymentPayload['address']=content['address']
        paymentPayload['total']=content['total']

        app.logger.info('creating order for %s with following contents %s',userid, json.dumps(content))

        paymentup=testPayment()

        s=Session()


        with order_tracer.start_span('/postgres/insertOrder/', child_of=span) as postgres_span:
            app.logger.info("this is postgres span " + str(postgres_span))
            try:
                s.add(order)
                s.commit()
                app.logger.info("Initial insert of order %s", order.id)
                order_id=order.id
            except Exception as e:
                app.logger.error("Could not insert initial data into postgres %s", e)
                raise FoundIssue(str(e), status_code=500)

        with order_tracer.start_span('/order/Payment', child_of=span) as payment_span:
            span.set_tag("orderid", order_id)
            try:
                if paymentup==0:
                    app.logger.info("Payment service is down will not process")
                    paymentres=makeFakePayment(paymentPayload)
                    transactionId=paymentres['transactionID']
                else:
                    app.logger.info("Making call to real payment service")
                    paymentres=makePayment(paymentPayload, payment_span, request.headers)
                    transactionId=paymentres['transactionID']
                #content['paid']=transactionId
                #order.paid=transactionID

                with order_tracer.start_span('/postgres/updateTransactionId/', child_of=payment_span) as transaction_span:
                    span.set_tag("transactionID", transactionId)
                    try:
            #            if (order_id !=0 and transactionId != string.empty):
                        if (order_id != 0):
                            app.logger.info("Updating order # %s with transaction id %s", order_id, transactionId)
            #                document=s.query(Order).filter(Order.id==order_id).first()
                            document=s.query(Order).filter(Order.userid==userid).filter(Order.id==order_id).first()
                            app.logger.info("Queried order has transaction of %s", document.paid)
                            app.logger.info("updating paid to new transaction id")
                            document.paid=str(transactionId)
                            s.commit()
                            #orders.update_one({"_id": order_id},{"$set":{"paid": transactionId}})
                        else:
                            app.logger.info("Issue updating order - it was never added properly to orderDB")
                    except Exception as e:
                        app.logger.error("Could not update order into postgres", str(e))
                        raise FoundIssue(str(e), status_code=204)

            except Exception as e:
                app.logger.error("Issue with making call to payment")
                raise FoundIssue(str(e), status_code=500)
            finally:
                s.close()

    return jsonify({"userid":userid, "order_id":order_id, "payment":paymentres})


#placeholder for call to payment
def makeFakePayment(paymentPayload):

    transactionId=randomString()

    paymentres={"success":"false", "message":"Payment service is down", "amount":paymentPayload['total'], "transactionID": transactionId}

    return paymentres

def makePayment(paymentPayload, span, headers):

    app.logger.info("Sending payload %s:", paymentPayload)

    token = headers["authorization"]

    headers={"authorization" : token, "content-type": "application/json"}
    
    try:
        order_tracer.inject(span, opentracing.Format.HTTP_HEADERS, carrier=headers)
    except Exception as e:
        raise FoundIssue(str(e), status_code=500)
    
    data=json.dumps(paymentPayload)

    try:
        paymentreq = requests.post(paymenturi+'/pay', headers=headers, data=data)
    except Exception as e:
        app.logger.error("Call to payment in makePayment failed")
        raise FoundIssue(str(e), status_code=500)

    #app.logger.info("result is", paymentreq.status_code, json.loads(paymentreq.json()))
    paymentres=paymentreq.json()

    if (paymentreq.status_code==200 or paymentreq.status_code==400 or paymentreq.status_code==401 or paymentreq.status_code==402):

        app.logger.info("got a known result from payment %s", paymentres)
        
    else:
        app.logger.info("got an unknown result from payment %s", paymentres)

    return paymentres

#baseline route to check is server is live ;-)
@app.route('/')
@auth.login_required
def hello_world(name=None):
	return render_template('hello.html')


if __name__ == '__main__':

    testPayment()
    insertInitialData() #initialize the database with some baseline

# If you are using citus then turn this on
#    distributeDB()

    app.run(host='0.0.0.0', port=orderport)
