FROM centos:6.7

RUN mkdir -p  /home

COPY run.sh /home/
COPY ld-2.12.so /lib/
COPY libc-2.12.so /lib/
COPY libdl-2.12.so /lib/
COPY libgcc_s-4.4.7-20120601.so.1 /lib/
COPY libm-2.12.so /lib/
COPY libpthread-2.12.so /lib/
COPY librt-2.12.so /lib/
COPY ld-linux.so.2 /lib/
COPY libstdc++.so.6.0.13 /usr/lib/

RUN chmod 755 /lib/*so*
RUN chmod 755 /usr/lib/*so*

RUN ln -s /lib/libdl-2.12.so /lib/libdl.so.2
RUN ln -s /usr/lib/libstdc++.so.6.0.13 /usr/lib/libstdc++.so.6
RUN ln -s /lib/libm-2.12.so /lib/libm.so.6
RUN ln -s /lib/libgcc_s-4.4.7-20120601.so.1 /lib/libgcc_s.so.1
RUN ln -s /lib/libc-2.12.so /lib/libc.so.6
RUN ln -s /lib/libpthread-2.12.so /lib/libpthread.so.0
RUN ln -s /lib/librt-2.12.so /lib/librt.so.1
