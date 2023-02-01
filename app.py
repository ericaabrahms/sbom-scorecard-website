import json, os, boto3, botocore, re
from hashlib import sha1
from tempfile import TemporaryDirectory
from invoke import run
from flask import Flask, render_template, request, Response
from werkzeug.utils import secure_filename
import logging
import xml.dom.minidom

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


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

def add_spaces_to_name(name):
    return re.sub( r"([A-Z])", r" \1", name)

@app.post("/score")
def score():
  f = request.files['json-file']

  log.debug("saving")
  if f.filename == '':
        status_code = 400
        return render_template(
            'scorecard.html',
        ), status_code

  if f.mimetype == 'text/xml':
      payload = b"".join(f.stream.readlines())
      dom = xml.dom.minidom.parseString(payload)
      # not the most space efficient, but it's at least normalized.
      payload = dom.toprettyxml()
      pretty_payload = dom.toprettyxml()

  elif f.mimetype == 'application/json':
      payload = normalize_json(b"".join(f.stream.readlines()))
      pretty_payload = json.dumps(json.loads(payload), indent=4)
  else:
      pretty_payload = payload = b"".join(f.stream.readlines())

  checksum = sha1(payload).hexdigest()
  f.seek(0) # reset cursor back to beginning after reading it out

  # TODO: Openfeature?

  if os.getenv("SKIP_UPLOAD", "false") != "true":
    log.info("pushing %s to spaces", checksum)
    client.put_object(
        Bucket=os.getenv('SPACES_BUCKET'),
        Key=f"{checksum}.json",
        ContentType=f.mimetype,
        ChecksumAlgorithm='sha1',
        ChecksumSHA1=checksum,
        Body=payload,
        ACL='private',
        Metadata={}
    )

  with TemporaryDirectory(f.filename) as d:
      outfile = f'{d}/{f.filename}'
      f.save(outfile)
      log.debug("running cmd")
      output = run(
          f"./sbom-scorecard score {outfile} --outputFormat json",
          hide='out', # hide stdout
          warn=True, # don't throw exceptions on error
      )


  # Note for Erica of the future:
  # use request.files to get to uploaded file
  # specifically, request.files('json-file')

  log.debug("outputting")
  if output.ok:
    print(output.stdout)
    print(output.stderr)
    score_data = json.loads(output.stdout)
    status_code = 200
  else:
    log.warning("Error when running on file %s", checksum)
    score_data = None
    status_code = 400

  return render_template(
    'scorecard.html',
    score_data=score_data,
    add_spaces_to_name=add_spaces_to_name,
    json_data=pretty_payload,
  ), status_code
