FROM neubiaswg5/icy-base:latest

RUN mkdir -p /app/data && chmod -R 777 /app/data

ADD protocol.protocol /app/protocol.protocol
ADD wrapper.py /app/wrapper.py

ENTRYPOINT ["python", "/app/wrapper.py"]
