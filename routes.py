from flask import Flask, render_template, request
from sitemap import cluster


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/action/cluster')
def check_url():
    url = request.args.get('url')
    data = cluster(url)
    return data


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=8888)
