FROM python:3.6.3-alpine3.6

# app workdir
WORKDIR /app

# copy app dependencies
COPY requirements.txt docker/*.sh ./

# install dependecies
RUN set -ex \
	&& apk add --update bash curl git gcc musl-dev \
	&& apk add --virtual .fetch-deps \
	\
	# install requirement and delete pip cache
	&& pip install -r requirements.txt --upgrade \
	&& rm -rf /root/.cache/pip/* \
	\
	# uninstal deps
	&& apk del .fetch-deps \
	&& rm -rf /var/cache/apk/*

# build app source code
COPY . ./

# Default runtime configs
EXPOSE 8080
ENTRYPOINT ["./start.sh"]
CMD ["run"]
