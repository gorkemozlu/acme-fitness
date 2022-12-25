var express = require('express'),
app = express(),
port = process.env.PAYMENT_PORT;
if (!port) {
  port = 9000;
}
body = require('body-parser');
const request = require('request');
const opentracing = require('opentracing');
const uuidv4 = require('uuid/v4');
const tracer = require('./tracer');

tracer.initGlobalTracer();

userHost = process.env.USERS_HOST;
if (!userHost) {
  userHost = "users";
} 
userPort = process.env.USERS_PORT;
if (!userPort) {
  userPort = 8083;
}

app.use(body.urlencoded({ extended: true }));
app.use(body.json());

app.listen(port);

console.log('payment service started on: ' + port);

//Liveness test via GET
app.get('/live', function (req,res) {
  res.send('live');
});

//POST to process 'payment'
app.post('/pay', function (req, res) {
  console.log('POST call to /pay');
  //console.log(req.headers);
  //console.log(req.body);

  // Tracing setup
  const parentCtx = opentracing.globalTracer().extract(opentracing.FORMAT_HTTP_HEADERS, req.headers);
  const paySpan = opentracing.globalTracer().startSpan('processing_payment', {
    childOf: parentCtx
  });
  paySpan.setTag('http.method', 'POST');
  paySpan.setTag('http.url', `http://${req.headers.host}${req.url}`);
  //console.log(paySpan);

  // Get and verify JWT from request headers
  let token = req.headers['x-access-token'] || req.headers['authorization'];
  if (token) {
    if (token.startsWith('Bearer ')) {
      token = token.slice(7, token.length);
    }
  } 
  else {
    paySpan.setTag(opentracing.Tags.ERROR, true);
    paySpan.finish();
    return res.json({
      success: false,
      message: 'Authorization token was not provided'
    });
  }

  // Make POST call to '/verify-token' on USER service
  
  var data = JSON.stringify({
    'access_token': token
  });
  var options = {
    uri: 'http://' + userHost + ':' + userPort + '/verify-token',
    body: data,
  }
  return new Promise(function(resolve, reject) {
    request.post(options, function(err, response, body) {
      if (err) {
        paySpan.setTag(opentracing.Tags.ERROR, true);
        paySpan.finish();
        console.log(err);
        res.status(401).send({
          'message': 'call from payment to users/verify-token returned an error',
          'error': err
        });
      }
      else if(response.statusCode != 200) {
        paySpan.setTag(opentracing.Tags.ERROR, true);
        paySpan.finish();
        console.log('call to payment processesing is unauthorized');
        res.status(401).send({
          'message': 'call to users/verify-token did not return a statusCode 200'
        });
      }
      else {

        //check card number
        card = req.body.card;
        d = new Date();
        cardNum = card.number;
        curYear = d.getFullYear();
        curMonth = d.getMonth()+1;
        expYear = Number(card.expYear);
        expMonth = Number(card.expMonth);
        ccv = card.ccv;
        total = Number(req.body.total);
        if (!cardNum || !expYear || !expMonth || !ccv || !total) {
          console.log('payment failed due to incomplete info');
          paySpan.setTag(opentracing.Tags.ERROR, true);
          paySpan.finish();
          res.status(400).send({
            success: 'false',
            status: '400',
            message: 'missing required data',
            amount: '0',
            transactionID: '-1'
          });
        }
        else if(cardNum.length % 4 != 0) {
          console.log('payment failed due to bad card number');
          paySpan.setTag(opentracing.Tags.ERROR, true);
          paySpan.finish();
          return res.status(400).send({
            success: 'false',
            status: '400',
            message: 'not a valid card number',
            amount: '0',
            transactionID: '-2'
          });
        }
        //check expiry
        else if ((expYear < curYear) || (expYear == curYear && (expMonth < curMonth))) {
          console.log('payment failed due to expired card');
          paySpan.setTag(opentracing.Tags.ERROR, true);
          paySpan.finish();
          return res.status(400).send({
            success: 'false',
            status: '400',
            message: 'card is expired',
            amount: '0',
            transactionID: '-3'
          });
        }
        //process payment
        else {
          console.log('payment processed successfully');
          paySpan.setTag(opentracing.Tags.HTTP_STATUS_CODE, 200);
          paySpan.finish();
          tID = uuidv4();
          return res.status(200).send({
            success: 'true',
            status: '200',
            message: 'transaction successful',
            amount: total,
            transactionID: tID
          });
        }
      }
    });
  })
});
