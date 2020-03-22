FROM besn0847/arm-tf-cv2
MAINTAINER franck@besnard.mobi

RUN apt-get update && \
	apt-get install -y --force-yes --no-install-recommends \
		clang libclang-dev && \
	apt-get install -y --force-yes --no-install-recommends \
		build-essential pkg-config && \
	apt-get install -y --force-yes --no-install-recommends \
		libpng-dev libfreetype6-dev && \
	apt-get install -y --force-yes --no-install-recommends \
		python3-dev

RUN pip3 install inotify && \
	pip3 install resettabletimer && \
	pip3 install scikit-image && \
	pip3 install imutils && \
	pip3 install requests

RUN apt-get update && \
	apt-get remove -y --force-yes \
		cmake clang libclang-dev \
		python3-dev \
		build-essential pkg-config && \
	apt-get autoremove && \
	rm -rf /var/lib/apt/lists/*

ADD monitor.py /bootstrap/
ADD startup.sh /

RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]
