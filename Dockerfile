FROM neubiaswg5/icy-base:latest

ADD protocol.protocol /icy/protocols/protocol.protocol
ADD wrapper.py /app/wrapper.py

ENTRYPOINT ["python", "/app/wrapper.py"]
