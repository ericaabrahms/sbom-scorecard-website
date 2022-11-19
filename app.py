from flask import Flask, render_template, request, Response

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
    "Ratio": 0.5,
    "Reasoning": "100% have purls and 0% have CPEs",
    "MaxPoints": 20
  },
  "PackageVersions": {
    "Ratio": 1,
    "Reasoning": "",
    "MaxPoints": 20
  },
  "PackageLicenses": {
    "Ratio": 0,
    "Reasoning": "",
    "MaxPoints": 20
  },
  "Total": {
    "Ratio": 0.64705884,
    "Reasoning": "",
    "MaxPoints": 85
  }
}'''
  return Response(json_file, mimetype='application/json')

  # 1. Serve static files
  # 2. Fake JSON payload
  # 3. ...make a website
  # 4. make a database/s3 to store the uploaded files
  # 5. deploy
  # 6. Profit
