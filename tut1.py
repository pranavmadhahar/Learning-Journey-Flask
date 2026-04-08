from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/about")
def about():
    name = "Pranav"
    return render_template("about.html", name =name)

# app.run()

#This will automatically update  changes without reloading app.
app.run(debug=True)
