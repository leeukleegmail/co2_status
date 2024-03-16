FROM python:alpine3.19

ARG container_name
ENV CONTAINER_NAME $container_name

WORKDIR /$CONTAINER_NAME

ENV TZ="Europe/Amsterdam"

RUN pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY .python_hue /root/.python_hue

#CMD python $SCRIPT_NAME
CMD python $SCRIPT_NAME