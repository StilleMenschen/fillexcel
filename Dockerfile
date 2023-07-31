FROM python:3.11.4-alpine3.18

COPY --chown=101:101 ./config/ /app/config/
COPY --chown=101:101 ./fillexcel/ /app/fillexcel/
COPY --chown=101:101 ./fills/ /app/fills/
COPY --chown=101:101 ./manage.py ./requirements.txt ./entrypoint.sh /app/

RUN set -x && \
    addgroup --gid 101 --system app && \
    adduser --system --ingroup app --no-create-home --home /nonexistent --shell /bin/false --uid 101 app && \
    sed -i 's/psycopg2==/psycopg2-binary==/' /app/requirements.txt && \
    pip config --user set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config --user set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --upgrade pip && \
    pip install -U -r /app/requirements.txt && \
    sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories && \
    apk update && \
    apk add --no-cache build-base python3-dev linux-headers && \
    pip install uwsgi && \
    pip cache purge && \
    apk del build-base python3-dev linux-headers && \
    apk cache clean

USER 101:101

WORKDIR /app

ENTRYPOINT ["/bin/sh", "entrypoint.sh"]