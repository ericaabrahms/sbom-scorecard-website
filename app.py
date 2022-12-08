import json, os, boto3, botocore, re
from hashlib import sha1
from tempfile import TemporaryDirectory
from invoke import run
from flask import Flask, render_template, request, Response
from werkzeug.utils import secure_filename
import logging

log = logging.basicConfig(level=logging.DEBUG)


UPLOAD_FOLDER = '../temp_files'
ALLOWED_EXTENSIONS = {'json'}


session = boto3.session.Session()
region = os.getenv('SPACES_REGION')
client = session.client(
    's3',
    config=botocore.config.Config(s3={'addressing_style': 'virtual'}),
    region_name=region,
    endpoint_url=f'https://{region}.digitaloceanspaces.com',
    aws_access_key_id=os.getenv('SPACES_KEY'),
    aws_secret_access_key=os.getenv('SPACES_SECRET')
)


def allowed_file(filename):
    return '.' in filename and \
          filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_json(js: str):
    return json.dumps(
        json.loads(js),
        ensure_ascii=False
    ).encode('utf-8')

app = Flask(__name__)

@app.route("/")
def hello_world():
  return render_template('hello.html')

@app.post("/score")
def score():
  json_file = '''{
  "Compliance": {
    "Ratio": 1,
    "Reasoning": "",
    "MaxPoints": 25
  },
  "PackageIdentification": {
    "Ratio": 0,
    "Reasoning": "0% have purls and 0% have CPEs",
    "MaxPoints": 20
  },
  "PackageVersions": {
    "Ratio": 0,
    "Reasoning": "",
    "MaxPoints": 20
  },
  "PackageLicenses": {
    "Ratio": 1,
    "Reasoning": "",
    "MaxPoints": 20
  },
  "CreationInfo": {
    "Ratio": 0,
    "Reasoning": "No tool was used to create the sbom",
    "MaxPoints": 15
  },
  "Total": {
    "Ratio": 0.45,
    "Reasoning": "",
    "MaxPoints": 100
  }
}'''
  def add_spaces_to_name(name):
      return re.sub( r"([A-Z])", r" \1", name)

  f = request.files['json-file']

  log.debug("saving")
  with TemporaryDirectory(f.filename) as d:
      outfile = f'{d}/{f.filename}'
      f.save(outfile)
      f.seek(0) # reset cursor back to beginning after writing it out
      log.debug("running cmd")
      output = run(
          f"./sbom-scorecard score {outfile} --outputFormat json",
          hide='out', # hide stdout
          warn=True, # don't throw exceptions on error
      )

  the_json = normalize_json(b"".join(f.stream.readlines()))
  checksum = sha1(the_json).hexdigest()
  log.debug("pushing %s to spaces", checksum)
  # TODO: Openfeature?
  if os.getenv("SKIP_UPLOAD") != "false":
    client.put_object(
        Bucket=os.getenv('SPACES_BUCKET'),
        Key=f"{checksum}.json",
        ContentType="application/json",
        ChecksumAlgorithm='sha1',
        ChecksumSHA1=checksum,
        Body=the_json,
        ACL='private',
        Metadata={}
    )

  # Note for Erica of the future:
  # use request.files to get to uploaded file
  # specifically, request.files('json-file')

  log.debug("outputting")
  if output.ok:
    score_data = json.loads(output.stdout)
    status_code = 200
  else:
    log.error("Error when running on file %s", checksum)
    score_data = None
    status_code = 400

  return render_template(
    'scorecard.html',
    score_data=score_data,
    add_spaces_to_name=add_spaces_to_name,
    json_data=json.dumps(json.loads(the_json), indent=4),
  ), status_code
  # return Response(json_file, mimetype='application/json')

  # 1. Serve static files
  # 2. Fake JSON payload
  # 3. ...make a website
  # 4. make a database/s3 to store the uploaded files
  # 5. deploy
  # 6. Profit
