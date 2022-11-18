from flask import Flask, render_template, url_for, request, redirect, session, make_response, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, FloatField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length
import email_validator
from functools import wraps
import re
import ibm_db
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import sqlite3 as sql
from datetime import datetime

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=6667d8e9-9d4d-4ccb-ba32-21da3bb5aafc.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=30376;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=ywz69948;PWD=bpABt6nFhm0Fzkqg", '', '')






# Session validation
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "id" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



# Create a Flask Instance
app = Flask(__name__)
app.config['SECRET_KEY'] = "Dont Know"


un = ''
email = ''
pw = ''

# Create a form for user signup
class UserForm(FlaskForm):
    user_name = StringField("Username", validators=[DataRequired(), Length(max=64)], render_kw={"placeholder": "Username"})
    user_email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
    first_name = StringField("First Name", validators=[DataRequired()], render_kw={"placeholder": "First Name"})
    last_name = StringField("Last Name", validators=[DataRequired()], render_kw={"placeholder": "Last Name"})
    pass_word = PasswordField("Password", validators=[DataRequired(), Length(min=8, message='Password should be at least %(min)d characters long')], render_kw={"placeholder": "Password"})
    Submit_signup = SubmitField("Sign Up")

# Create a form for user Login 
class LoginForm(FlaskForm):
    login_name = StringField("Login Name", validators=[DataRequired(), Length(max=64)], render_kw={"placeholder": "Username"})
    login_pw = PasswordField("Password", validators=[DataRequired(), Length(min=8, message='Password should be at least %(min)d characters long')], render_kw={"placeholder": "Password"})
    Submit_login = SubmitField("Login")
#Create a form class for sales
class SalesForm(FlaskForm):
    sale_id = IntegerField("Item Id", validators=[DataRequired()])
    sale_quantity = IntegerField("number of items", validators=[DataRequired()])
    Submit_sale = SubmitField("Submit")

# Create a form class for adding items
class AddItemForm(FlaskForm):
    item_id = IntegerField("Item ID", validators=[DataRequired()])
    item = StringField("Enter the item", validators=[DataRequired()])
    quantity = IntegerField("number of items", validators=[DataRequired()])
    expiry = DateField("Expiry Date", validators=[DataRequired()])
    price = FloatField("Price of the item", validators=[DataRequired()])
    t_price = FloatField("Total Price", validators=[DataRequired()])
    Submit_add = SubmitField("Submit")

# Create a form class for deleting items
class DeleteItemForm(FlaskForm):
    del_item_id = IntegerField("Item ID", validators=[DataRequired()])
    del_quantity = IntegerField("Number of items", validators=[DataRequired()])
    Submit_del = SubmitField("Remove")

# Create a form for Profile update
class ProfileForm(FlaskForm):
    fields = SelectField(u'fields', choices=[('1','USERNAME'),('2','FIRST NAME'),('3','LAST NAME')])
    value = StringField("Value", validators=[DataRequired()])
    Submit_field = SubmitField("Update")






@app.route("/")
def home():
    #print(request.args.get)
    return render_template('home.html')

@app.route("/signup", methods=["GET", "POST"])
def usersignup():
    # variables for user signup
    user_name = None
    first_name = None
    last_name = None
    user_email = None
    pass_word = None
    userform = UserForm()

    if userform.validate_on_submit():
        user_name = userform.user_name.data
        first_name = userform.first_name.data
        last_name = userform.last_name.data
        user_email = userform.user_email.data
        pass_word = userform.pass_word.data

        insert_sql = 'INSERT INTO users (USERNAME,FIRST_NAME,LAST_NAME,EMAIL,PASSWORD) VALUES (?,?,?,?,?)'
        pstmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(pstmt, 1, user_name)
        ibm_db.bind_param(pstmt, 2, first_name)
        ibm_db.bind_param(pstmt, 3, last_name)
        ibm_db.bind_param(pstmt, 4, user_email)
        ibm_db.bind_param(pstmt, 5, pass_word)
        print(pstmt)
        ibm_db.execute(pstmt)

        message = Mail(
                from_email=os.environ.get('MAIL_DEFAULT_SENDER'),
                to_emails=email,
                subject='New SignUp',
                html_content='<p>Hello, Your Registration was successfull. <br><br> Thank you for choosing us.</p>')

        sg = SendGridAPIClient(
            api_key=os.environ.get('SENDGRID_API_KEY'))

        response = sg.send(message)
        print(response.status_code, response.body)

        return redirect('/login')
    return render_template('signup.html', 
    user_name=user_name,
    firstname=first_name,
    last_name=last_name,
    user_email=user_email,
    pass_word=pass_word,
    userform=userform)


@app.route('/login', methods=['GET', 'POST'])
def userlogin():
    global userid
    login_name = None
    login_pw = None
    loginform = LoginForm()

    if loginform.validate_on_submit():
        login_name = loginform.login_name.data
        login_pw = loginform.login_pw.data
        sql = "SELECT * FROM users WHERE USERNAME =? AND PASSWORD=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, login_name)
        ibm_db.bind_param(stmt, 2, login_pw)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['loggedin'] = True
            session['id'] = account['EMAIL']
            userid = account['EMAIL']
            session['username'] = account['USERNAME']
            return redirect('/dashboard')
        else:
            flash('Incorrect Username or Password!')
    return render_template('login.html',
    login_name=login_name,
    login_pw=login_pw,
    loginform = loginform)


@app.route("/dashboard")
@login_required
def userdashboard():
    insert_sql = 'SELECT * FROM STOCKS'
    pstmt = ibm_db.exec_immediate(conn, insert_sql)
    dictionary = ibm_db.fetch_assoc(pstmt)
    stocks = []
    headings = list(dictionary.keys())
    while dictionary != False:
        stocks.append(dictionary)
        dictionary = ibm_db.fetch_assoc(pstmt)
    print(headings, stocks)
    return render_template('dashboard.html', name=session['username'], headings=headings, data=stocks)

@app.route("/sale", methods=["GET", "POST"])
def newsale():
    #Sold items
    sale_id = None
    sale_quantity = None
    sale_form = SalesForm()

    #Validate Form
    if sale_form.validate_on_submit():
        sale_id = sale_form.sale_id.data
        sale_quantity = sale_form.sale_quantity.data
        insert_sql = 'SELECT * FROM STOCKS WHERE ITEM_ID=?'
        pstmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(pstmt, 1, sale_id)
        ibm_db.execute(pstmt)
        dictionary = ibm_db.fetch_assoc(pstmt)
        
        if dictionary:
            curr_quantity = dictionary["QUANTITY"]
            if curr_quantity> sale_quantity:
                insert_sql = 'UPDATE STOCKS SET QUANTITY=? WHERE ITEM_ID=?'
                pstmt = ibm_db.prepare(conn, insert_sql)
                ibm_db.bind_param(pstmt, 1, curr_quantity - sale_quantity)
                ibm_db.bind_param(pstmt, 2, sale_id)
                ibm_db.execute(pstmt)
                flash("Sold")
            elif curr_quantity == sale_quantity:
                insert_sql = 'DELETE FROM STOCKS WHERE ITEM_ID=?'
                pstmt = ibm_db.prepare(conn, insert_sql)
                ibm_db.bind_param(pstmt, 1, sale_id)
                ibm_db.execute(pstmt)
                flash("Sold")
        else:
            flash("Item Not available!")

    return render_template('sale.html',
    sale_id = sale_id,
    sale_quantity = sale_quantity,
    sale_form = sale_form)

@app.route("/profile")
def userprofile():
    if request.method == "GET":
        try:
            email = session['id']
            insert_sql = 'SELECT * FROM users WHERE EMAIL=?'
            pstmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(pstmt, 1, email)
            ibm_db.execute(pstmt)
            dictionary = ibm_db.fetch_assoc(pstmt)
            print(dictionary)
        except Exception as e:
            msg = e
        finally:
            # print(msg)
            return render_template("profile.html", data=dictionary)


@app.route('/update-user', methods=['POST', 'GET'])
@login_required
def updateUser():
    if request.method == "POST":
        email = session['id']
        field = request.form.get('field')
        value = request.form.get('value')
        insert_sql = 'UPDATE users SET ' + field + '= ? WHERE EMAIL=?'
        pstmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(pstmt, 1, value)
        ibm_db.bind_param(pstmt, 2, email)
        print(pstmt)
        ibm_db.execute(pstmt)
        return redirect('/profile')


@app.route('/update-password', methods=['POST', 'GET'])
@login_required
def updatePassword():
    if request.method == "POST":
        email = session['id']
        password = request.form.get('prev-password')
        curPassword = request.form.get('cur-password')
        confirmPassword = request.form.get('confirm-password')
        insert_sql = 'SELECT * FROM  users WHERE EMAIL=? AND PASSWORD=?'
        pstmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(pstmt, 1, email)
        ibm_db.bind_param(pstmt, 2, password)
        ibm_db.execute(pstmt)
        dictionary = ibm_db.fetch_assoc(pstmt)
        print(dictionary)
        if curPassword == confirmPassword:
            insert_sql = 'UPDATE users SET PASSWORD=? WHERE EMAIL=?'
            pstmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(pstmt, 1, confirmPassword)
            ibm_db.bind_param(pstmt, 2, email)
            ibm_db.execute(pstmt)
        return redirect('/profile')



# Create Material Page
@app.route("/materials", methods=["GET", "POST"])
@login_required
def material():
    #add material
    item_id = None
    item = None
    quantity = None
    expiry = None
    price = None
    t_price = None
    form = AddItemForm() 

    #Delete Material
    del_item_id = None
    del_quantity = None
    del_form = DeleteItemForm()
    #validate form
    if form.validate_on_submit():
        item_id = form.item_id.data
        item = form.item.data
        quantity = form.quantity.data
        expiry = form.expiry.data
        price = form.price.data
        t_price = form.t_price.data

        insert_sql = 'INSERT INTO stocks (ITEM_ID,NAME,QUANTITY,EXPIRY_DATE,PRICE_PER_ITEM,TOTAL_PRICE) VALUES (?,?,?,?,?,?)'
        pstmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(pstmt, 1, item_id)
        ibm_db.bind_param(pstmt, 2, item)
        ibm_db.bind_param(pstmt, 3, quantity)
        ibm_db.bind_param(pstmt, 4,expiry)
        ibm_db.bind_param(pstmt, 5, price)
        ibm_db.bind_param(pstmt, 6, t_price)
        ibm_db.execute(pstmt)

        form.item.data = ''
        form.quantity.data = ''
        form.expiry.data = ''
        form.price.data = ''
        form.item_id.data = ''
        form.t_price.data = ''
        flash("New Item Added Successfully!")
    
    if del_form.validate_on_submit():
        del_item_id = del_form.del_item_id.data
        del_quantity = del_form.del_quantity.data

        insert_sql = 'SELECT * FROM STOCKS WHERE item_id=?'
        pstmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(pstmt, 1,del_item_id)
        ibm_db.execute(pstmt)
        dictionary = ibm_db.fetch_assoc(pstmt)
        del_quan = dictionary['QUANTITY'] - del_quantity
        print(del_quan)
        print(dictionary)
        

        insert_sql = 'UPDATE STOCKS SET QUANTITY=? WHERE ITEM_ID=?'
        pstmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(pstmt, 1, del_quan)
        ibm_db.bind_param(pstmt, 2, del_item_id)
        ibm_db.execute(pstmt)
        del_form.del_item_id.data = ''
        del_form.del_quantity.data = ''
        flash("Item Removed Successfully!")

    return render_template("materials.html",
    item_id = item_id,
    item = item,
    quantity = quantity,
    expiry = expiry,
    price = price,
    t_price = t_price,
    form = form,
    del_item_id = del_item_id,
    delquantity = del_quantity,
    del_form = del_form)



@app.route('/logout', methods=['GET'])
@login_required
def logout():
    print(request)
    resp = make_response(render_template("home.html"))
    session.clear()
    return resp


if __name__ == "__main__":
    app.run()