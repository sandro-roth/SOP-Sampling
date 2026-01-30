reset:
	docker compose --profile tools build reset
	docker compose --profile tools run --rm reset
	docker compose up --no-deps database
	docker compose up -d