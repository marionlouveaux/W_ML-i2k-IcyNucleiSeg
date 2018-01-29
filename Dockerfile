FROM neubiaswg5/icy-base:latest

ADD protocol.protocol /icy/protocols/protocol.protocol
ADD run.sh /icy/run.sh
RUN cd /icy && chmod a+x run.sh
ENTRYPOINT ["/bin/sh", "/icy/run.sh"]
