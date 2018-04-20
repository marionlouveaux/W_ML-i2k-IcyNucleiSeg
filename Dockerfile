FROM neubiaswg5/icy-base:latest

ADD protocol.protocol /icy/protocols/protocol.protocol
ADD run.sh /icy/run.sh

RUN cd /icy && chmod a+x run.sh

FROM gmichiels/python-client-base

RUN conda install scikit-image --yes
RUN conda install joblib=0.11 --yes

ADD wrapper.py /icy/wrapper.py
RUN cd /icy && chmod a+x wrapper.py

RUN cd / && \
    git clone https://github.com/waliens/sldc.git && \
    cd sldc && \
    python setup.py build && \
    python setup.py install

ENTRYPOINT ["python", "/icy/wrapper.py"]

