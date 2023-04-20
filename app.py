import json, os, boto3, botocore, re
from hashlib import sha1
from tempfile import TemporaryDirectory
from invoke import run
from flask import Flask, render_template, request, Response, redirect, url_for
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

def pretty_and_normalized(raw: str) -> (str, str):
    try:
        normalized = normalize_json(raw)
        pretty_payload = json.dumps(json.loads(normalized), indent=4)
    except json.decoder.JSONDecodeError:
        dom = xml.dom.minidom.parseString(raw)
        # not the most space efficient, but it's at least normalized.
        normalized = dom.toprettyxml().encode('utf-8')
        pretty_payload = dom.toprettyxml()
    except:
        pretty_payload = normalized = raw

    return pretty_payload, normalized

app = Flask(__name__)

@app.route("/")
def homepage():
  return render_template('hello.html')

def add_spaces_to_name(name):
    return re.sub( r"([A-Z])", r" \1", name)

@app.route("/score/<sha1checksum>")
def get_score(sha1checksum):
    with TemporaryDirectory(sha1checksum) as d:
        filepath = os.path.join(d, sha1checksum)
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                client.download_fileobj(os.getenv('SPACES_BUCKET'), f"{sha1checksum}.json", f)

        with open(filepath, 'r') as f:
            contents = ''.join(f.readlines())

        pretty_payload, normalized = pretty_and_normalized(contents)

        log.debug("running cmd")
        output = run(
            f"./sbom-scorecard score {filepath} --outputFormat json",
            hide='out', # hide stdout
            warn=True, # don't throw exceptions on error
        )

    log.debug("outputting")
    if output.ok:
      print(output.stdout)
      print(output.stderr)
      score_data = json.loads(output.stdout)
      status_code = 200
    else:
      log.warning("Error when running on file %s", sha1checksum)
      score_data = None
      status_code = 400

    return render_template(
      'scorecard.html',
      score_data=score_data,
      add_spaces_to_name=add_spaces_to_name,
      json_data=pretty_payload,
    ), status_code


@app.post("/score")
def score():
  f = request.files['json-file']

  log.debug("saving")
  if f.filename == '':
        return render_template(
            'scorecard.html',
        ), 400
  raw_payload = b"".join(f.stream.readlines()).decode('utf-8')
  pretty_payload, payload = pretty_and_normalized(raw_payload)
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

  return redirect(url_for('get_score', sha1checksum=checksum))
