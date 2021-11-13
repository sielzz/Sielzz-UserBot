FROM mrismanaziz/man-userbot:buster

RUN git clone -b Man-Userbot https://github.com/sielzz/Sielzz-UserBot /home/manuserbot/ \
    && chmod 777 /home/manuserbot \
    && mkdir /home/manuserbot/bin/

COPY ./sample_config.env ./config.env* /home/manuserbot/

WORKDIR /home/manuserbot/

CMD ["python3", "-m", "userbot"]
