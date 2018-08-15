From python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir /config
ADD /config/requirements.txt /config/ 
RUN pip install -r /config/requirements.txt
RUN mkdir /src;
RUN mkdir /static
WORKDIR /src
CMD python manage.py collectstatic --no-input;python manage.py migrate; gunicorn tesserack_core.wsgi:application -b 0.0.0.0:8000
