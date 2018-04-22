#!/bin/bash
#fullpaths for lib, jar, protocol
#launch it from icy directory
cd /icy/

#First Icy launch to be sure it is up-to-date
java -cp /icy/lib/ -jar /icy/icy.jar -hl

java -cp /icy/lib/ -jar /icy/icy.jar -hl -x plugins.adufour.protocols.Protocols protocol="/icy/protocols/protocol.protocol" inputFolder="$1" extension=tif csvFileSuffix=_results scale3enable=true scale3sensitivity=$2

#parameters can be exposed through read boxes in the icy protocols and identified with an id, here e.g. scale3enable
