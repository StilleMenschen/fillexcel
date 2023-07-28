FROM python:3.11.4-alpine3.18

WORKDIR /app

COPY ./requirements.txt ./entrypoint.sh /app/

RUN set -x && \
    addgroup -g 101 --system nginx && \
    adduser --system --ingroup nginx --no-create-home --home /nonexistent --shell /bin/false --uid 101 nginx && \
    sed -i 's/psycopg2==/psycopg2-binary==/' /app/requirements.txt && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -U -r /app/requirements.txt && \
    sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories && \
    apk add --no-cache python3-dev build-base linux-headers pcre-dev && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uwsgi && \
    pip cache purge && \
    rm -f /app/requirements.txt

ENTRYPOINT [ "/bin/sh", "entrypoint.sh" ]