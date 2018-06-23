#!/bin/bash

docker-compose up --build -d --scale timeseries=2 --scale twitter=2
docker-compose logs -f
