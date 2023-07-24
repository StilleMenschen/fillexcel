FROM python:3.11.4-alpine3.18

WORKDIR /app

COPY ./requirements.txt ./entrypoint.sh /app/

RUN sed -i 's/psycopg2==/psycopg2-binary==/' /aap/requirements.txt && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -U -r /app/requirements.txt && \
    pip cache purge && \
    rm -f /app/requirements.txt

ENTRYPOINT [ "/bin/sh", "entrypoint.sh" ]