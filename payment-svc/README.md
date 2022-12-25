# Payment

[![gcr.io](https://img.shields.io/badge/gcr.io-stable-orange?style=flat-square)](https://console.cloud.google.com/gcr/images/vmwarecloudadvocacy/GLOBAL/acmeshop-payment@sha256:cd6c8192d93395a0b2d80691dec91645825448235ee4b14fb9a0f2e22de07844/details?tab=info)

> A payment service, because nothing in life is really free...

The Payment service is part of the [ACME Fitness Shop](https://github.com/vmwarecloudadvocacy/acme_fitness_demo). The goal of this specific service is to validate credit card payments. Currently the only validation performed is whether the card is acceptable.

## Prerequisites

There are different dependencies based on whether you want to run a built container, or build a new one.

### Build

* [Node.js (current LTS)](https://nodejs.org/en/)
* [Docker](https://www.docker.com/docker-community)

### Run

* [Docker](https://www.docker.com/docker-community)

## Installation

### Docker

Use this command to pull the latest tagged version of the shipping service:

```bash
docker pull gcr.io/vmwarecloudadvocacy/acmeshop-payment:1.1.0
```

To build a docker container, run `docker build . -t vmwarecloudadvocacy/acmeshop-payment:<tag>`.

The images are tagged with:

* `<Major>.<Minor>.<Bug>`, for example `1.1.0`
* `stable`: denotes the currently recommended image appropriate for most situations
* `latest`: denotes the most recently pushed image. It may not be appropriate for all use cases

### Source

To build the app as a stand-alone executable, run `npm install`. This will download all the latest dependencies from NPM.

## Usage

The **payment** service, either running inside a Docker container or as a stand-alone app, relies on the below environment variables:

* **PAYMENT_PORT**: The port that will be exposed by the Node.js process to receive requests on (defaults to `9000`)

The Docker image is based on the Bitnami Node.js container. Use this commands to run the latest stable version of the payment service with all available parameters:

```bash
docker run --rm -it -e PAYMENT_PORT=9000 -p 9000:9000 gcr.io/vmwarecloudadvocacy/acmeshop-payment:1.1.0
```

## API

### HTTP

#### `GET /live`

The live operation returns the current status of the server:

```bash
curl --request GET \
  --url http://localhost:9000/live
```

```text
live
```

#### `POST /pay`

The pay operation performs three validations on the credit card:

* All 4 keys in the JSON blob have non-NULL values
* cardNum is a multiple of 4 digits (4,8,12,16, etc)
* Card is not expired

```bash
curl --request POST \
  --url http://localhost:9000/pay \
  --header 'content-type: application/json' \
  --data '{
  "card": {
    "number": "1234",
    "expYear": "2020",
    "expMonth": "01",
    "ccv" : "123"
  },
	"total": "123"
}'
```

```json
{
  "success": "true",
  "status": "200",
  "message": "transaction successful",
  "amount": 123,
  "transactionID": "3f846704-af12-4ea9-a98c-8d7b37e10b54"
}
```

When the card fails to validate, an HTTP/400 message is sent back explaining what the error is:

```json
{
  "success": "false",
  "status": "400",
  "message": "card is expired",
  "amount": "0",
  "transactionID": "-3"
}
```

## Successful output

200 SUCCESS response with body JSON
```json
{
  "success": "true",
  "status": "200",
  "message": "transaction successful",
  "amount": value,
  "transactionID": uuID
}
```
## Contributing

[Pull requests](https://github.com/vmwarecloudadvocacy/payment/pulls) are welcome. For major changes, please open [an issue](https://github.com/vmwarecloudadvocacy/payment/issues) first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

See the [LICENSE](./LICENSE) file in the repository
