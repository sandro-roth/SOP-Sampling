FROM python:3.12-slim AS base

ARG USE_PROXY
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# export proxy vars so pip and others can see them
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV NO_PROXY=${NO_PROXY}

WORKDIR /app

# tini, ca-certificates, curl
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/usr/bin/tini","-g","--"]

# copy your CA bundle and register it
COPY certs/usz-bundle.crt /usr/local/share/ca-certificates/usz-bundle.crt
RUN update-ca-certificates

# pip config, add proxy only if USE_PROXY=true
RUN set -eux; \
    printf "[global]\ntrusted-host = pypi.org\n    files.pythonhosted.org\n" > /etc/pip.conf; \
    if [ "$USE_PROXY" = "true" ]; then \
        printf "proxy = %s\n" "$HTTP_PROXY" >> /etc/pip.conf; \
        echo "pip will use proxy"; \
    else \
        echo "pip without proxy"; \
    fi

# ---------- Shared utils stage (my-utils) ----------
FROM base AS utils-base

# install shared utils from root pyproject and utils/
COPY pyproject.toml ./pyproject.toml
COPY utils ./utils

RUN python -m pip install --upgrade pip \
    && pip install .

# create common dirs used by all services
RUN mkdir -p /data /logs /config

# ---------- Service image: database (sop-sql) ----------
FROM utils-base AS database

# copy and install database package
COPY src/database/pyproject.toml /app/src/database/pyproject.toml
COPY src/database/sop_sql /app/src/database/sop_sql

WORKDIR /app/src/database
RUN pip install .

# copy scripts and use the start script
WORKDIR /app
COPY scripts ./scripts
RUN chmod +x scripts/*.sh

CMD ["./scripts/start-database.sh"]

# ---------- Service image: identify (sop-mask) ----------
FROM utils-base AS identify

COPY src/identify/pyproject.toml /app/src/identify/pyproject.toml
COPY src/identify/user_mask /app/src/identify/user_mask

WORKDIR /app/src/identify
RUN pip install .

WORKDIR /app
COPY scripts ./scripts
RUN chmod +x scripts/*.sh

CMD ["./scripts/start-identify.sh"]

# ---------- Service image: ui (sop-ui) ----------
FROM utils-base AS ui

COPY src/user_interface/pyproject.toml /app/src/user_interface/pyproject.toml
COPY src/user_interface/sop_ui /app/src/user_interface/sop_ui

WORKDIR /app/src/user_interface
RUN pip install .

WORKDIR /app
COPY scripts ./scripts
RUN chmod +x scripts/*.sh

CMD ["./scripts/start-ui.sh"]




# get rid of warning use for production environment
# CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "sop_ui.app:app"]