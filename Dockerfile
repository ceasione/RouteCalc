
# docker build --progress=plain -t routecalc .

# sudo docker run -it -v /home/oliver/RTDATA:/RouteCalc/storage -v /tmp:/tmp/rcsocket routecalc

# sudo docker run -d -v /home/oliver/RTDATA:/RouteCalc/storage -v /tmp:/tmp/rcsocket routecalc

# sudo docker exec -it <container_id> /bin/bash

# docker ps -a / docker rm <id>
# docker images / docker rmi <id>


FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


COPY . /RouteCalc

WORKDIR /RouteCalc

RUN pip3 install --upgrade pip

RUN pip3 install --no-cache-dir -r /RouteCalc/requirements.txt

CMD ["uwsgi", "--ini", "/RouteCalc/uwsgi.ini"]
