help: always
	@echo "make start             Build and Start all RecvCtl containers."
	@echo "make stop              Stop all RecvCtl containers."
	@echo "make restart           Stop and Start all RecvCtl containers."
	@echo "make update            Update all RecvCtl repositories."

always:
.PHONY: always

restart: stop start

start: always grafana
	docker compose up -d --build

stop: always
	docker compose down --remove-orphans

grafana:
	mkdir "$@"
	chown 1000 "$@"
