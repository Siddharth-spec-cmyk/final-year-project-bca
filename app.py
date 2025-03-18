from flask import Flask, render_template
from auth import auth_app
from tools import tools_app

app = Flask(__name__)
app.secret_key = 'aizen'

@app.route('/')
def home():
    return render_template("index.html")

app.register_blueprint(auth_app, url_prefix='/auth')
app.register_blueprint(tools_app, url_prefix='/tools')

if __name__ == '__main__':
    app.run(debug=True)
