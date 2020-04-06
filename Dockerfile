#FROM ubuntu:16.04
FROM jlesage/baseimage:ubuntu-16.04

ARG DEBIAN_FRONTEND="noninteractive"
ENV TERM="xterm" LANG="C.UTF-8" LC_ALL="C.UTF-8"

RUN apt-get update && \
    apt-get install -y bc git build-essential libargtable2-dev autoconf \
    libtool-bin ffmpeg libsdl1.2-dev libavutil-dev libavformat-dev libavcodec-dev && \

# Clone Comskip
    cd /opt && \
    git clone https://github.com/erikkaashoek/Comskip && \
    cd Comskip && \
    ./autogen.sh && \
    ./configure && \
    make && \

# Clone Comchap
    cd /opt && \
    git clone https://github.com/BrettSheleski/comchap.git && \
    cd comchap && \
    make && \

# Cleanup
    apt-get -y autoremove && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* && \
    rm -rf /var/tmp/*

ADD ./comskip.ini /opt/Comskip/comskip.ini

# Add start script
ADD comskip-wrapper.sh /comskip-wrapper.sh
RUN chmod +x /comskip-wrapper.sh
ADD start.sh /startapp.sh
RUN chmod +x /startapp.sh

ENV APP_NAME="comskip"

VOLUME ["/config"]
VOLUME ["/input"]
VOLUME ["/output"]
VOLUME ["/work"]

#ENTRYPOINT ["/start.sh"]
