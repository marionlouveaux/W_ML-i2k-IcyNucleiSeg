FROM neubiaswg5/icy-base:latest

ADD protocol.protocol /icy/protocols/protocol.protocol
ADD wrapper.py /icy/wrapper.py
ADD run.sh /icy/run.sh

RUN chmod -R 777 /icy/data
RUN chmod a+x /icy/wrapper.py
RUN chmod a+x /icy/run.sh

ENTRYPOINT ["python", "/icy/wrapper.py"]
