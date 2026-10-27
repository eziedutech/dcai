BACK := code/backpy
WEB := code/frontnext
DROID := code/android
UV := uv --directory $(BACK)

.PHONY: setup dev test lint fmt probe models web-setup web-dev web-lint web-build android-test android-build eval seed replay-record

setup:
	$(UV) sync

dev:
	$(UV) run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

fmt:
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

# One small real call per configured endpoint. Costs credits, run once.
probe:
	$(UV) run python -m app.llm.probe call

# List model IDs, for example: make models P=fireworks F=muse
models:
	$(UV) run python -m app.llm.probe models $(P) $(F)

# Parent dashboard and homepage (Next.js). Talks to the backend at DCAI_API_URL.
web-setup:
	npm --prefix $(WEB) ci

web-dev:
	npm --prefix $(WEB) run dev

web-lint:
	cd $(WEB) && npx next typegen && npx tsc --noEmit && npm run lint

web-build:
	npm --prefix $(WEB) run build

# dcAI Guardian (Android app) and the sample chat app.
android-test:
	cd $(DROID) && ./gradlew :app:testDebugUnitTest :app:lintDebug

android-build:
	cd $(DROID) && ./gradlew :app:assembleDebug :sample:assembleDebug

eval seed replay-record:
	@echo "$@: not built yet (spec section 12, day 2 to day 8)" && exit 1
