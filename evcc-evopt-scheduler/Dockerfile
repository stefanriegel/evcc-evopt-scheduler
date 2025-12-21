ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache python3 py3-pip tzdata && \
    python3 -m ensurepip && \
    pip3 install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY app /app
COPY rootfs/ /

RUN chmod a+x /etc/services.d/evcc-evopt-scheduler/run \
    /etc/cont-init.d/10-set-workdir

WORKDIR /app

