Bootstrap: docker
From: neubiaswg5/icy-base:latest

%files
	protocol.protocol /icy/protocols/protocol.protocol
	run.sh /icy/run.sh

%post
	cd /icy && chmod a+x run.sh

%runscript
	echo "start"
	/bin/sh ./icy/run.sh
