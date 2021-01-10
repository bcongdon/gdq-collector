#!/bin/bash

docker-compose up --build -d
docker-compose scale timeseries=2
docker-compose logs -f
