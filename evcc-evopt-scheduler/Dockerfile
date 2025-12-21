ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache python3 py3-pip tzdata && \
    python3 -m ensurepip && \
    pip3 install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY run.sh /usr/local/bin/run.sh
COPY app /opt/evcc_evopt_scheduler

RUN chmod a+x /usr/local/bin/run.sh

WORKDIR /opt/evcc_evopt_scheduler

CMD ["/usr/local/bin/run.sh"]
