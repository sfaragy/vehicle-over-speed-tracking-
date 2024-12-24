.PHONY: build stop start app-login


build: stop
	docker-compose -f docker-compose.yml build

stop:
	docker-compose -f docker-compose.yml down

start: stop
	docker-compose -f docker-compose.yml up --remove-orphans -d

restart: stop start

app-login:
	docker exec -it banglossOverspeed bash

