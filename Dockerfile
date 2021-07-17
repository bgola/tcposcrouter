FROM python:3.8-alpine

WORKDIR /home/tcposcrouter

ADD . .

RUN python setup.py install

ENTRYPOINT ["tcposcrouter"]
