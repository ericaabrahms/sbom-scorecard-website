FROM python:3

WORKDIR /srv/sbom-scorecard-website/
COPY . .


RUN curl -Lo ./sbom-scorecard https://github.com/justinabrahms/sbom-scorecard/releases/download/0.0.8/sbom-scorecard-linux-amd64
RUN chmod +x ./sbom-scorecard
RUN pip install pipenv
RUN pipenv install --system --deploy

EXPOSE 8000
ENV TIMEOUT 120
CMD ["pipenv", "run", "gunicorn", "wsgi:app", "-b", "0.0.0.0:8000", "--access-logfile", "-"]
