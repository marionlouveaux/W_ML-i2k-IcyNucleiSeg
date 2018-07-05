FROM neubiaswg5/icy-base:latest

WORKDIR /icy

ADD protocol.protocol /icy/protocols/protocol.protocol
ADD wrapper.py /icy/wrapper.py
ADD run.sh /icy/run.sh
      
RUN cd /icy && chmod a+x run.sh

ENTRYPOINT ["python", "wrapper.py"]
