FROM python:3

WORKDIR /srv/sbom-scorecard-website/
COPY . .

RUN curl -Lo ./sbom-scorecard https://github.com/eBay/sbom-scorecard/releases/download/0.0.2/sbom-scorecard-linux-amd64
RUN pip install pipenv
RUN pipenv install

EXPOSE 8000
CMD ["pipenv", "run", "gunicorn", "wsgi:app", "-b", "0.0.0.0:8000", "--access-logfile", "-"]
