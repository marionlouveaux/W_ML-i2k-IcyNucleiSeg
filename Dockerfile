FROM python:3.6.9-stretch

RUN apt-get update && apt-get install libgeos-dev -y && apt-get clean
# ---------------------------------------------------------------------------------------------------------------------
# Install Java
RUN apt-get update && apt-get install openjdk-8-jdk -y && apt-get clean

# ---------------------------------------------------------------------------------------------------------------------
# Install Cytomine python client
RUN git clone https://github.com/cytomine-uliege/Cytomine-python-client.git
RUN cd /Cytomine-python-client && git checkout tags/v2.3.0.poc.1 && pip install .
RUN rm -r /Cytomine-python-client

# ---------------------------------------------------------------------------------------------------------------------
# Install gdown
RUN pip install gdown

# ---------------------------------------------------------------------------------------------------------------------
# Install Icy.
RUN apt-get update && apt-get install -y unzip wget && \
    mkdir -p /icy && \
    cd /icy && \
    gdown -O icy.zip https://doc-10-64-docs.googleusercontent.com/docs/securesc/ha0ro937gcuc7l7deffksulhg5h7mbp1/u7qcal96olch1m3tac666lr8q3bnc4co/1579248000000/06618377988378538221/*/1vgJK6ZIt-kTfBhZOBtyRIRLUdRJM-e6f?e=download && \
    unzip icy.zip && \
    rm -rf icy.zip

# Add icy to the PATH
ENV PATH $PATH:/icy

RUN mkdir -p /icy/data/in && \
        mkdir -p /icy/protocols

RUN chmod -R a+rwx /icy 
# ---------------------------------------------------------------------------------------------------------------------
# Install Neubias-W5-Utilities (annotation exporter, compute metrics, helpers,...)
RUN git clone https://github.com/Neubias-WG5/neubiaswg5-utilities.git && \
       cd /neubiaswg5-utilities/ && git checkout tags/v0.8.0 && pip install .

# install utilities binaries
RUN chmod +x /neubiaswg5-utilities/bin/*
RUN cp /neubiaswg5-utilities/bin/* /usr/bin/

# cleaning
RUN rm -r /neubiaswg5-utilities

# custom version of imagecodecs to make sure tifffile can read icy-generated images
RUN pip install numpy==1.13.0
RUN pip install Cython==0.29.6
RUN pip install imagecodecs-lite==2019.2.22 

# ---------------------------------------------------------------------------------------------------------------------
# Install Protocol
ADD protocol.protocol /icy/protocols/protocol.protocol
ADD wrapper.py /app/wrapper.py

# for running the wrapper locally
ADD descriptor.json /app/descriptor.json

ENTRYPOINT ["python", "/app/wrapper.py"]
