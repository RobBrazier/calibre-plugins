FROM docker.io/alpine

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk add --no-cache calibre bash curl

ENTRYPOINT [ "/bin/bash" ]
