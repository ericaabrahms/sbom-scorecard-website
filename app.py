import json, os, boto3, botocore, re
from hashlib import sha1
from tempfile import TemporaryDirectory
from invoke import run
from flask import Flask, render_template, request, Response
from werkzeug.utils import secure_filename


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

  # Upload the file
  f = request.files['json-file']

  with TemporaryDirectory(f.filename) as d:
      outfile = f'{d}/{f.filename}'
      f.save(outfile)
      f.seek(0) # reset cursor back to beginning after writing it out
      output = run(
          f"./sbom-scorecard score {outfile} --outputFormat json",
          hide='out', # hide stdout
          warn=True, # don't throw exceptions on error
      )

  # normalize the loaded json.
  the_json = normalize_json(b"".join(f.stream.readlines()))
  checksum = sha1(the_json).hexdigest()
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

  if output.ok:
    score_data = json.loads(output.stdout)
  else:
    # TODO: do some sort of error handling...
    score_data = {}

  return render_template('scorecard.html', score_data=score_data, add_spaces_to_name=add_spaces_to_name)
  # return Response(json_file, mimetype='application/json')

  # 1. Serve static files
  # 2. Fake JSON payload
  # 3. ...make a website
  # 4. make a database/s3 to store the uploaded files
  # 5. deploy
  # 6. Profit
