
# docker build --progress=plain -t ceasione/routecalc .

# Deploy locally
# sudo docker run --restart unless-stopped -d \
# --name routecalc_active \
# -v /home/oliver/RTDATA:/RouteCalc/storage \
# -v /tmp:/tmp/rcsocket \
# ceasione/routecalc:latest

# Deploy at server
# sudo docker run --restart unless-stopped -d \
# --name routecalc_active \
# -v /srv/flask-uwsgi/RC_STORAGE:/RouteCalc/storage \
# -v /tmp:/tmp/rcsocket \
# ceasione/routecalc:latest

# Testing
# sudo docker run -d -v /home/oliver/RTDATA:/RouteCalc/storage -v /tmp:/tmp/rcsocket --name rctest routecalc tail -f /dev/null
# docker exec -d rctest python3 -m app.main
# docker exec rctest pytest -m unit
# docker exec rctest pytest -m integration
# docker exec rctest pytest -m network
# docker stop rctest
# docker rm rctest

# docker ps -a / docker rm <id>
# docker images / docker rmi <id>
# docker system prune


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
