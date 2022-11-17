from flask import Flask, render_template, url_for, request, redirect, session, make_response, flash

app = Flask(__name__)

@app.route("/")
def home():
    #print(request.args.get)
    return render_template('index.html')

@app.route("/signup")
def usersignup():
      
    return render_template('signup.html')
@app.route('/login')
def userlogin():
    return render_template('login.html')


if __name__ == "__main__":
    app.run()