FROM python:3

WORKDIR /srv/sbom-scorecard-website/
COPY . .

RUN pip install pipenv
RUN pipenv install

EXPOSE 8000
CMD ["pipenv", "run", "gunicorn", "wsgi:app", "-b", "0.0.0.0:8000", "--access-logfile", "-"]
