FROM ubuntu:16.04

MAINTAINER mezz64 <jtmihalic@gmail.com>

ENV USER_ID=99
ENV GROUP_ID=100

ARG S6_OVERLAY_VERSION=v1.17.2.0
ARG DEBIAN_FRONTEND="noninteractive"
ENV TERM="xterm" LANG="C.UTF-8" LC_ALL="C.UTF-8"

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y python3 git build-essential libargtable2-dev autoconf \
    libtool-bin ffmpeg libsdl1.2-dev libavutil-dev libavformat-dev libavcodec-dev && \

# Clone Comskip
    cd /opt && \
    git clone git://github.com/erikkaashoek/Comskip && \
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

#make config folder
RUN mkdir /config 

#Add start script
ADD start.sh /start.sh
RUN chmod +x /start.sh

#Add python script
ADD socketserv.py /socketserv.py
RUN chmod +x /socketserv.py

VOLUME ["/config"]

ENTRYPOINT ["/start.sh"]
