import json, os, boto3, botocore, re
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
  the_json = b"".join(f.stream.readlines())

  client.put_object(Bucket=os.getenv('SPACES_BUCKET'),
              Key=f.filename,
              Body=the_json,
              ACL='private',
              Metadata={
                  'x-amz-meta-my-key': 'your-value'
              }
            )

  # Note for Erica of the future:
  # use request.files to get to uploaded file
  # specifically, request.files('json-file')

  score_data = json.loads(json_file)

  return render_template('scorecard.html', score_data=score_data, add_spaces_to_name=add_spaces_to_name)
  # return Response(json_file, mimetype='application/json')

  # 1. Serve static files
  # 2. Fake JSON payload
  # 3. ...make a website
  # 4. make a database/s3 to store the uploaded files
  # 5. deploy
  # 6. Profit
