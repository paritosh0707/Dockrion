.PHONY: bootstrap test
        bootstrap:
	pip install -e packages/common-py -e packages/schema -e packages/adapters \
	            -e packages/policy-engine -e packages/telemetry \
	            -e packages/sdk-python -e packages/cli
        test:
	pytest -q
