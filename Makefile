help:
	@echo "make start             Build and Start all RecvCtl containers."
	@echo "make stop              Stop all RecvCtl containers."
	@echo "make restart           Stop and Start all RecvCtl containers."
	@echo "make update            Update all RecvCtl repositories."
.PHONY: help

restart: stop start
.PHONY: restart

start: grafana xmlcollect-receiver
	docker compose up -d --build
.PHONY: start

stop: xmlcollect-receiver
	docker compose down --remove-orphans
.PHONY: stop


update: update_xmlcollect-receiver
.PHONY: update


update_xmlcollect-receiver: xmlcollect-receiver
	cd "$<"; make update; cd ..
.PHONY: update_xmlcr

grafana:
	mkdir "$@"
	chown 1000 "$@"

xmlcollect-receiver:
	git clone https://github.com/seth0r/ffp-xmlcollect-receiver.git "$@"
	cd "$@"; make init; cd ..

cherry-status:
	git clone https://github.com/seth0r/ffp-cherry-status.git "$@"
	cd "$@"; make init; cd ..
