FROM python:3.12-slim

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




# 1) install shared utils as "my-utils"
COPY pyproject.toml ./pyproject.toml
COPY utils ./utils
RUN pip install --upgrade pip \
    && pip install .

# 2) install database service (sop-sql or similar)
COPY src/database/pyproject.toml ./src/database/pyproject.toml
COPY src/database/sop_sql ./src/database/sop_sql
WORKDIR /app/src/database
RUN pip install .

# 3) install identify service (user-mask or similar)
COPY src/identify/pyproject.toml ./src/identify/pyproject.toml
COPY src/identify/user_mask ./src/identify/user_mask
WORKDIR /app/src/identify
RUN pip install .

# 4) install UI service (sop-ui)
COPY src/user_interface/pyproject.toml ./src/user_interface/pyproject.toml
COPY src/user_interface/sop_ui ./src/user_interface/sop_ui
WORKDIR /app/src/user_interface
RUN pip install .

# 5) copy scripts and go back to /app
WORKDIR /app
COPY scripts ./scripts
RUN chmod +x scripts/*.sh

# create dirs that you will mount
RUN mkdir -p /data /logs /config /certs

# default command, docker compose will override anyway
CMD ["bash"]






# get rid of warning use for production environment
# CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "sop_ui.app:app"]


# make sure to mount volumes for /config, /data, /logs and utils