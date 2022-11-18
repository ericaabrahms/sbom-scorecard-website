from flask import Flask, request, Response
with open('static/test_json.json') as f:
  json_file = "".join(f.readlines())

app = Flask(__name__)

# url_for('static', filename='style.css')

@app.route("/")
def hello_world():
  return "<p>Hello world</p>"

@app.post("/score")
def score():
  return Response(json_file, mimetype='application/json')
  # 1. Serve static files
  # 2. Fake JSON payload
  # 3. ...make a website
  # 4. make a database/s3 to store the uploaded files
  # 5. deploy
  # 6. Profit