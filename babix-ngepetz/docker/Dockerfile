FROM python:3.6.1

# app workdir
WORKDIR /app

# copy app dependencies
COPY requirements.txt docker/*.sh ./

# install dependecies
RUN set -ex \
    && apt-get update \
    && apt-get -y install bash git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r ./requirements.txt --upgrade \
    && rm -rf /root/.cache/pip/* \
    && rm -rf /var/cache/apk/*

# build app source code
COPY . ./

# Default runtime configs
EXPOSE 8080
ENTRYPOINT ["./start.sh"]
CMD ["run"]
