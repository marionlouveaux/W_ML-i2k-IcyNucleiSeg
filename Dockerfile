FROM python:3.6

# ---------------------------------------------------------------------------------------------------------------------
# Install Cytomine python client
RUN git clone https://github.com/cytomine-uliege/Cytomine-python-client.git
RUN cd /Cytomine-python-client && git checkout tags/v2.2.0 && pip install .
RUN rm -r /Cytomine-python-client

# ---------------------------------------------------------------------------------------------------------------------
# Install Neubias-W5-Utilities (annotation exporter, compute metrics, helpers,...)
RUN git clone https://github.com/Neubias-WG5/neubiaswg5-utilities.git
RUN cd /neubiaswg5-utilities/ && git checkout tags/v0.5.2a && pip install .

# install utilities binaries
RUN chmod +x /neubiaswg5-utilities/bin/*
RUN cp /neubiaswg5-utilities/bin/* /usr/bin/

# cleaning
RUN rm -r /neubiaswg5-utilities

# Install Java
RUN apt-get update && apt-get install openjdk-8-jdk -y && apt-get clean

# Install Neubias-W5-Utilities (annotation exporter, compute metrics, helpers,...)
RUN git clone https://github.com/Neubias-WG5/neubiaswg5-utilities.git
RUN chmod +x /neubiaswg5-utilities/bin/*
RUN cp /neubiaswg5-utilities/bin/* /usr/bin/
RUN cd /neubiaswg5-utilities/ && pip install .
RUN rm -r /neubiaswg5-utilities

# keep re-install of numpy as long as this is open: https://github.com/scikit-image/scikit-image/issues/3586
# latest scikit-image is incompatible with latest numpy (1.16) on pip. This is being fixed by skimage team.

RUN pip install numpy==1.13.0
RUN pip install Cython==0.29.6
RUN pip install imagecodecs-lite==2019.2.22 

# Java is installed in neubiaswg5/neubias-base.

# Install Icy.
RUN apt-get update && apt-get install -y unzip wget && \
    mkdir -p /icy && \
    cd /icy && \
    wget -O icy.zip http://www.icy.bioimageanalysis.org/downloadIcy/icy_1.9.9.1.zip && \
    unzip icy.zip && \
    rm -rf icy.zip
      
#ADD icy_patch.jar /icy/icy.jar

# Add icy to the PATH
ENV PATH $PATH:/icy

RUN mkdir -p /icy/data/in && \
mkdir -p /icy/protocols

# add workflow specific files

ADD protocol.protocol /icy/protocols/protocol.protocol
ADD wrapper.py /app/wrapper.py

ENTRYPOINT ["python", "/app/wrapper.py"]
