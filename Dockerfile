FROM python:3.11-slim as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    lsb-release curl wget gpg gcc build-essential git libffi-dev software-properties-common pkg-config libudev-dev openssh-client libssl-dev locales librust-openssl-sys-dev \
  && rm -rf /var/lib/apt/lists/*
RUN sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen
RUN locale-gen



# Add .cargo/bin to PATH
ENV PATH="/root/.cargo/bin:${PATH}"
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8

WORKDIR /code

from base as builder

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.cargo/bin:${PATH}"
RUN pip --no-cache-dir install --upgrade wheel poetry==$POETRY_VERSION pip
RUN python -m venv /venv

COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes | /venv/bin/pip install -r /dev/stdin

COPY . .
RUN poetry build && /venv/bin/pip install wheel && /venv/bin/pip install dist/*.whl

FROM base as final
COPY --from=builder /venv /venv



COPY dev.sh /
ENTRYPOINT ["/dev.sh"]