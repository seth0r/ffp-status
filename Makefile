help: always
	@echo "make start             Build and Start all RecvCtl containers."
	@echo "make stop              Stop all RecvCtl containers."
	@echo "make restart           Stop and Start all RecvCtl containers."
	@echo "make update            Update all RecvCtl repositories."

always:
.PHONY: always

restart: stop start

start: always grafana xmlcollect-receiver cherry-status messagesender
	docker compose up -d --build

stop: always
	docker compose down --remove-orphans


update: update_xmlcollect-receiver update_cherry-status update_messagesender


update_xmlcollect-receiver: xmlcollect-receiver always
	cd "$<"; make update; cd ..

update_cherry-status: cherry-status always
	cd "$<"; make update; cd ..

update_messagesender: messagesender always
	cd "$<"; make update; cd ..

grafana:
	mkdir "$@"
	chown 1000 "$@"

xmlcollect-receiver:
	git clone https://github.com/seth0r/ffp-xmlcollect-receiver.git "$@"
	cd "$@"; make init; cd ..

cherry-status:
	git clone https://github.com/seth0r/ffp-cherry-status.git "$@"
	cd "$@"; make init; cd ..

messagesender:
	git clone https://github.com/seth0r/ffp-messagesender.git "$@"
	cd "$@"; make init; cd ..
