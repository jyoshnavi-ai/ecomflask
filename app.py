from flask import Flask, jsonify, request, url_for, session,make_response
from flask_session import Session
import re
import razorpay
import random
import os
from mysql.connector import connection
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_bcrypt import Bcrypt
from cmail import send_mail
from stoken import endata, dndata
from werkzeug.utils import secure_filename
from reportlab.platypus import (SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus.flowables import HRFlowable
from datetime import datetime, timedelta
from io import BytesIO

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'webp', 'gif', 'png'}


app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, y_host=1)
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.permanent_session_lifetime=timedelta(days=1)
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)

app.secret_key = 'Code@123'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

Session(app)


mydb = connection.MySQLConnection(
    user='flaskuser',
    host='localhost',
    password='@2005',
    db='ecom29'
)

client = razorpay.Client(auth=('rzp_test_TEuDHI8Wd0eKZt', 'BielZhhW3kKLOPlpalRPnrJk'))
def genotp():
    return random.randint(100000, 999999)


def allowed_extension(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "success",
        "message": "Welcome to ecom app"
    }), 200


@app.route('/api/admin/register', methods=['POST'])
def admincreate():
    cursor = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "failed",
                "message": "No valid JSON input given"
            }), 400

        adminname = data.get('username', '').strip()
        adminemail = data.get('useremail', '').strip()
        adminpassword = data.get('userpassword', '').strip()
        adminaddress = data.get('useraddress', '').strip()
        adminagree = data.get('useragree')

        if not adminname:
            return jsonify({
                "status": "failed",
                "message": "Username required"
            }), 400

        if not adminemail:
            return jsonify({
                "status": "failed",
                "message": "Email required"
            }), 400

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not re.match(email_pattern, adminemail):
            return jsonify({
                "status": "failed",
                "message": "Invalid email address"
            }), 400

        if not adminpassword:
            return jsonify({
                "status": "failed",
                "message": "Password required"
            }), 400

        if len(adminpassword) < 6:
            return jsonify({
                "status": "failed",
                "message": "Password is too short"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select adminemail from admindata where adminemail=%s", (adminemail,))

        existing_admin = cursor.fetchone()

        if existing_admin:
            return jsonify({
                "status": "failed",
                "message": "Email already exists"
            }), 409

        gotp = genotp()

        hashed_password = bcrypt.generate_password_hash(adminpassword).decode('utf-8')

        admindata = {
            "admin_username": adminname,
            "admin_useremail": adminemail,
            "admin_address": adminaddress,
            "admin_userpassword": hashed_password,
            "admin_agree": adminagree,
            "admin_otp": gotp
        }

        subject = "Verification code for admin"

        body = f"""Hello Admin,
        Your OTP is: {gotp}
        This OTP is valid for 5 minutes."""

        send_mail(
            to=adminemail,
            subject=subject,
            body=body
        )

        token = endata(admindata)

        return jsonify({
            "status": "success",
            "message": "OTP sent successfully",
            "token": token
        }), 200

    except Exception as e:
        print("Error in admin register:", str(e))

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


@app.route('/api/admin/verify-otp', methods=['POST'])
def adminotpverify():
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "status": "failed",
                "message": "No valid JSON input given"
            }), 400

        userotp = data.get('otp')
        token = data.get('token')

        if userotp is None or not token:
            return jsonify({
                "status": "failed",
                "message": "OTP and token required"
            }), 400

        try:
            admin_details = dndata(token)

        except Exception:
            return jsonify({
                "status": "failed",
                "message": "Invalid or expired token"
            }), 400

        tokenotp = admin_details.get('admin_otp')

        if int(userotp) != int(tokenotp):
            return jsonify({
                "status": "failed",
                "message": "Invalid OTP"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select count(*) from admindata where adminemail=%s", (admin_details['admin_useremail'],))

        email_exists = cursor.fetchone()[0]

        if email_exists > 0:
            return jsonify({
                "status": "failed",
                "message": "Email already exists"
            }), 409

        cursor.execute("insert into admindata(adminid,adminname,adminemail,adminpassword,adminaddress,adminagree) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s)", (admin_details['admin_username'], admin_details['admin_useremail'], admin_details['admin_userpassword'], admin_details['admin_address'], admin_details['admin_agree']))

        mydb.commit()

        return jsonify({
            "status": "success",
            "message": "Admin details registered successfully"
        }), 200

    except Exception as e:
        mydb.rollback()
        print("MySQL Error:", str(e))

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


@app.route('/api/admin/login', methods=['POST'])
def adminlogin():
    cursor = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "failed",
                "message": "No input data given"
            }), 400

        login_email = data.get('email', '').strip()
        login_password = data.get('password', '').strip()

        if not login_email or not login_password:
            return jsonify({
                "status": "failed",
                "message": "Login email and password required"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select bin_to_uuid(adminid),adminname,adminemail,adminpassword from admindata where adminemail=%s", (login_email,))

        admin_data = cursor.fetchone()

        if not admin_data:
            return jsonify({
                "status": "failed",
                "message": "Invalid email"
            }), 400

        adminid = admin_data[0]
        adminname = admin_data[1]
        adminemail = admin_data[2]
        stored_password = admin_data[3]

        if not bcrypt.check_password_hash(stored_password, login_password):
            return jsonify({
                "status": "failed",
                "message": "Invalid password"
            }), 400

        session.permanent = True
        session['adminid'] = adminid
        session['adminemail'] = adminemail

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "admin": {
                "adminid": adminid,
                "adminname": adminname,
                "adminemail": adminemail
            }
        }), 200

    except Exception as e:
        mydb.rollback()
        print("MySQL Error:", str(e))

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


@app.route('/api/admin/dashboard', methods=['GET'])
def admindashboard():
    try:
        if 'adminid' not in session:
            return jsonify({
                "status": "failure",
                "message": "Please login first"
            }), 401

        return jsonify({
            "status": "success",
            "message": "Welcome admin",
            "admin": {
                "adminid": session.get('adminid'),
                "adminemail": session.get('adminemail')
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500


@app.route('/api/admin/add-item', methods=['POST'])
def additem():
    cursor = None
    save_path = None

    try:
        if 'adminid' not in session:
            return jsonify({
                "status": "failure",
                "message": "Please login first"
            }), 401

        item_name = request.form.get('title', '').strip()
        item_description = request.form.get('Description', '').strip()
        item_about = request.form.get('About_item', '').strip()
        item_price = request.form.get('price', '').strip()
        item_quantity = request.form.get('quantity', '').strip()
        item_category = request.form.get('category', '').strip()

        if not item_name:
            return jsonify({
                "status": "failure",
                "message": "Item name required"
            }), 400

        if not item_description:
            return jsonify({
                "status": "failure",
                "message": "Item description required"
            }), 400

        if not item_price or not item_quantity:
            return jsonify({
                "status": "failure",
                "message": "Price and quantity required"
            }), 400

        try:
            item_price = int(item_price)
            item_quantity = int(item_quantity)

        except ValueError:
            return jsonify({
                "status": "failure",
                "message": "Price and quantity must be integers"
            }), 400

        item_filedata = request.files.get('file')

        if not item_filedata or not item_filedata.filename:
            return jsonify({
                "status": "failure",
                "message": "Item image required"
            }), 400

        filename = item_filedata.filename

        if not allowed_extension(filename):
            return jsonify({
                "status": "failure",
                "message": "Invalid file type"
            }), 400

        if not item_filedata.mimetype.startswith('image/'):
            return jsonify({
                "status": "failure",
                "message": "Invalid image"
            }), 400

        sec_filename = secure_filename(filename)
        ext = os.path.splitext(sec_filename)[1]
        new_filename = str(genotp()) + ext

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

        item_filedata.save(save_path)

        mydb.ping(reconnect=True)
        userid = session.get('adminid')
        cursor = mydb.cursor(buffered=True)
        cursor.execute("insert into items(itemid,itemname,itemdescription,itemAbout,itemprice,itemquantity,category,itemfilename,added_by) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s,uuid_to_bin(%s))", (item_name, item_description, item_about, item_price, item_quantity, item_category, new_filename, userid))
        mydb.commit()

        return jsonify({
            "status": "success",
            "message": "Item details registered successfully",
            "image_url": url_for(
                'static',
                filename=f'uploads/{new_filename}',
                _external=True
            )
        }), 200

    except Exception as e:
        mydb.rollback()
        print("MySQL Error:", str(e))

        if save_path and os.path.exists(save_path):
            os.remove(save_path)

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/admin/items', methods=['GET'])
def viewallfiles():
    cursor = None

    try:
        if 'adminid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "Pls login first"
            }), 401

        mydb.ping(reconnect=True)
        userid = session.get('adminid')
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select bin_to_uuid(itemid),itemname,itemdescription,itemAbout,itemprice,itemquantity,category,itemfilename from items where added_by=uuid_to_bin(%s)", (userid,))

        allitems_data = cursor.fetchall()

        if not allitems_data:
            return jsonify({
                "Status": "Failed",
                "Message": "No items found"
            }), 404

        products = []

        for item in allitems_data:
            products.append({
                "itemid": item[0],
                "itemname": item[1],
                "item_desc": item[2],
                "item_about": item[3],
                "price": float(item[4]),
                "quantity": item[5],
                "category": item[6],
                "image": url_for('static', filename=f'uploads/{item[7]}', _external=True)
            })

        return jsonify({
            "Status": "Success",
            "Message": "All items data",
            "products": products
        }), 200

    except Exception as e:
        print("Mysql Error", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/admin/item/<id>',methods=['GET'])
def viewitems(id):
    cursor=None
    try:
        if 'adminid' not in session:
            return jsonify({
                "status": "failure",
                "message": "Please login first"
            })
        #mysql connection
        mydb.ping(reconnect=True)
        userid = session.get('adminid')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(itemid),itemname,itemdescription,itemAbout,itemprice,itemquantity,category,itemfilename from items where added_by=uuid_to_bin(%s) and itemid=uuid_to_bin(%s)',[userid,id])
        item_data=cursor.fetchone()
        if not item_data:
            return jsonify({
                "status":"failure",
                "message":"No item found"
            })
        
        products=({
                'itemid':item_data[0],
                'itemname':item_data[1],
                'item_desc':item_data[2],
                'item_about':item_data[3],
                'price':float(item_data[4]),
                'quantity':item_data[5],
                'category':item_data[6],
                'image':url_for('static',filename=f'uploads/{item_data[7]}',_external=True)
            })
        return jsonify({
            "status":"success",
            "message":"All items data",
            "product":products
        })
    except Exception as e:
        print('Mysql Error',str(e))
        return jsonify({
            "status":"failed",
            "message":f"{str(e)}"
        }),500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/admin/delete-item/<string:itemid>', methods=['DELETE'])
def deleteitem(itemid):
    cursor = None

    try:
        if 'adminid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "Please login first"
            }), 401

        adminid = session.get('adminid')

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select itemfilename from items where itemid=uuid_to_bin(%s) and added_by=uuid_to_bin(%s)", (itemid, adminid))

        item_data = cursor.fetchone()

        if not item_data:
            return jsonify({
                "Status": "Failed",
                "Message": "Item not found"
            }), 404

        image_name = item_data[0]
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)

        cursor.execute("delete from items where itemid=uuid_to_bin(%s) and added_by=uuid_to_bin(%s)", (itemid, adminid))

        mydb.commit()

        if os.path.exists(image_path):
            os.remove(image_path)

        return jsonify({
            "Status": "Success",
            "Message": "Item deleted successfully"
        }), 200

    except Exception as e:
        mydb.rollback()
        print("Mysql Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/admin/edit-item/<string:itemid>', methods=['PUT'])
def edititem(itemid):
    cursor = None

    try:
        if 'adminid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "Please login first"
            }), 401

        adminid = session.get('adminid')

        item_name = request.form.get('title', '').strip()
        item_description = request.form.get('Description', '').strip()
        item_about = request.form.get('About_item', '').strip()
        item_price = request.form.get('price', '').strip()
        item_quantity = request.form.get('quantity', '').strip()
        item_category = request.form.get('category', '').strip()

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select itemfilename from items where itemid=uuid_to_bin(%s) and added_by=uuid_to_bin(%s)", (itemid, adminid))

        item_data = cursor.fetchone()

        if not item_data:
            return jsonify({
                "Status": "Failed",
                "Message": "Item not found"
            }), 404

        old_image = item_data[0]
        new_image = old_image

        item_filedata = request.files.get('file')

        if item_filedata and item_filedata.filename:

            if not allowed_extension(item_filedata.filename):
                return jsonify({
                    "Status": "Failed",
                    "Message": "Invalid image type"
                }), 400

            sec_filename = secure_filename(item_filedata.filename)
            ext = os.path.splitext(sec_filename)[1]
            new_image = str(genotp()) + ext

            save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_image)
            item_filedata.save(save_path)

            old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image)

            if os.path.exists(old_path):
                os.remove(old_path)

        cursor.execute("update items set itemname=%s,itemdescription=%s,itemAbout=%s,itemprice=%s,itemquantity=%s,category=%s,itemfilename=%s where itemid=uuid_to_bin(%s) and added_by=uuid_to_bin(%s)", (item_name, item_description, item_about, item_price, item_quantity, item_category, new_image, itemid, adminid))

        mydb.commit()

        return jsonify({
            "Status": "Success",
            "Message": "Item updated successfully"
        }), 200

    except Exception as e:
        mydb.rollback()

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/user/register', methods=['POST'])
def usercreate():
    cursor = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "Status": "Failed",
                "Message": "No valid JSON input given"
            }), 400

        username = data.get('username', '').strip()
        useremail = data.get('useremail', '').strip()
        userpassword = data.get('userpassword', '').strip()
        useraddress = data.get('useraddress', '').strip()
        usergender = data.get('usergender', '').strip()
        userphone = data.get('userphone', '').strip()

        if not username:
            return jsonify({
                "Status": "Failed",
                "Message": "Username required"
            }), 400

        if not useremail:
            return jsonify({
                "Status": "Failed",
                "Message": "Email required"
            }), 400

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not re.match(email_pattern, useremail):
            return jsonify({
                "Status": "Failed",
                "Message": "Invalid email address"
            }), 400

        if not userpassword:
            return jsonify({
                "Status": "Failed",
                "Message": "Password required"
            }), 400

        if len(userpassword) < 6:
            return jsonify({
                "Status": "Failed",
                "Message": "Password must contain at least 6 characters"
            }), 400

        if not userphone:
            return jsonify({
                "Status": "Failed",
                "Message": "Phone number required"
            }), 400

        if not usergender:
            return jsonify({
                "Status": "Failed",
                "Message": "Gender required"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select useremail from userdata where useremail=%s", (useremail,))

        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({
                "Status": "Failed",
                "Message": "Email already exists"
            }), 409

        gotp = genotp()

        hashed_password = bcrypt.generate_password_hash(userpassword).decode('utf-8')

        userdata = {
            "username": username,
            "useremail": useremail,
            "password": hashed_password,
            "useraddress": useraddress,
            "usergender": usergender,
            "userphone": userphone,
            "userotp": gotp
        }

        subject = "Verification code for user"

        body = f"""Hello User,
        Your OTP is: {gotp}
        This OTP is valid for 5 minutes."""

        send_mail(
            to=useremail,
            subject=subject,
            body=body
        )

        token = endata(userdata)

        return jsonify({
            "Status": "Success",
            "Message": "OTP sent successfully",
            "token": token
        }), 200

    except Exception as e:
        print("Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
    
@app.route('/api/user/verify-otp', methods=['POST'])
def userverifyotp():
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "Status": "Failed",
                "Message": "No valid JSON input given"
            }), 400

        userotp = data.get('otp')
        token = data.get('token')

        if userotp is None or not token:
            return jsonify({
                "Status": "Failed",
                "Message": "OTP and token required"
            }), 400

        try:
            user_details = dndata(token)

        except Exception:
            return jsonify({
                "Status": "Failed",
                "Message": "Invalid or expired token"
            }), 400

        tokenotp = user_details.get('userotp')

        if int(userotp) != int(tokenotp):
            return jsonify({
                "Status": "Failed",
                "Message": "Invalid OTP"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select count(*) from userdata where useremail=%s", (user_details['useremail'],))

        email_exists = cursor.fetchone()[0]

        if email_exists > 0:
            return jsonify({
                "Status": "Failed",
                "Message": "Email already exists"
            }), 409

        cursor.execute("insert into userdata(userid,username,useremail,password,useraddress,usergender,userphone) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s)", (user_details['username'], user_details['useremail'], user_details['password'], user_details['useraddress'], user_details['usergender'], user_details['userphone']))

        mydb.commit()

        return jsonify({
            "Status": "Success",
            "Message": "User registered successfully"
        }), 200

    except Exception as e:
        mydb.rollback()
        print("Mysql Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/user/login', methods=['POST'])
def userlogin():
    cursor = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "Status": "Failed",
                "Message": "No input data given"
            }), 400

        login_email = data.get('email', '').strip()
        login_password = data.get('password', '').strip()

        if not login_email or not login_password:
            return jsonify({
                "Status": "Failed",
                "Message": "Email and password required"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select bin_to_uuid(userid),username,useremail,password from userdata where useremail=%s", (login_email,))

        user_data = cursor.fetchone()

        if not user_data:
            return jsonify({
                "Status": "Failed",
                "Message": "Invalid email"
            }), 400

        userid = user_data[0]
        username = user_data[1]
        useremail = user_data[2]
        stored_password = user_data[3]

        if not bcrypt.check_password_hash(stored_password, login_password):
            return jsonify({
                "Status": "Failed",
                "Message": "Invalid password"
            }), 400

        session.permanent = True
        session['userid'] = userid
        session['useremail'] = useremail

        return jsonify({
            "Status": "Success",
            "Message": "Login successful",
            "user": {
                "userid": userid,
                "username": username,
                "useremail": useremail
            }
        }), 200

    except Exception as e:
        mydb.rollback()
        print("Mysql Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()


    cursor = None

    try:
        if 'userid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "Please login first"
            }), 401

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select bin_to_uuid(itemid),itemname,itemdescription,itemAbout,itemprice,itemquantity,category,itemfilename from items")

        allitems_data = cursor.fetchall()

        if not allitems_data:
            return jsonify({
                "Status": "Success",
                "Message": "No products found",
                "Products": []
            }), 200

        products = []

        for item in allitems_data:
            products.append({
                "itemid": item[0],
                "itemname": item[1],
                "item_desc": item[2],
                "item_about": item[3],
                "price": float(item[4]),
                "quantity": item[5],
                "category": item[6],
                "image": url_for('static', filename=f'uploads/{item[7]}', _external=True)
            })

        return jsonify({
            "Status": "Success",
            "Message": "Products fetched successfully",
            "Products": products
        }), 200

    except Exception as e:
        print("Mysql Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/user/logout', methods=['POST'])
def userlogout():
    try:
        if 'userid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "User is not logged in"
            }), 401

        session.pop('userid', None)
        session.pop('useremail', None)

        return jsonify({
            "Status": "Success",
            "Message": "Logout successful"
        }), 200

    except Exception as e:
        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

@app.route('/api/user/items', methods=['GET'])
def useritems():
    cursor = None

    try:
        if 'userid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "Please login first"
            }), 401

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select bin_to_uuid(itemid),itemname,itemdescription,itemAbout,itemprice,itemquantity,category,itemfilename,created_at from items order by created_at desc")

        allitems_data = cursor.fetchall()

        products = []

        for item in allitems_data:
            products.append({
                "itemid": item[0],
                "itemname": item[1],
                "item_desc": item[2],
                "item_about": item[3],
                "price": float(item[4]),
                "quantity": item[5],
                "category": item[6],
                "image": url_for('static', filename=f'uploads/{item[7]}', _external=True),
                "created_at": item[8]
            })

        return jsonify({
            "Status": "Success",
            "Message": "Products fetched successfully",
            "Products": products
        }), 200

    except Exception as e:
        print("Mysql Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/user/category/<string:ctype>', methods=['GET'])
def categoryitems(ctype):
    cursor = None

    try:
        if 'userid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "Please login first"
            }), 401

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select bin_to_uuid(itemid),itemname,itemdescription,itemAbout,itemprice,itemquantity,category,itemfilename,created_at from items where lower(category)=lower(%s) order by created_at desc", (ctype,))

        allitems_data = cursor.fetchall()

        products = []

        for item in allitems_data:
            products.append({
                "itemid": item[0],
                "itemname": item[1],
                "item_desc": item[2],
                "item_about": item[3],
                "price": float(item[4]),
                "quantity": item[5],
                "category": item[6],
                "image": url_for('static', filename=f'uploads/{item[7]}', _external=True),
                "created_at": item[8]
            })

        return jsonify({
            "Status": "Success",
            "Message": f"{ctype} products fetched successfully",
            "Products": products
        }), 200

    except Exception as e:
        print("Mysql Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/cart/add', methods=['POST'])
def addtocart():
    cursor = None

    try:
        if 'userid' not in session:
            return jsonify({
                "Status": "Failed",
                "Message": "Please login first"
            }), 401

        data = request.get_json()

        itemid = data.get('itemid')
        quantity = int(data.get('quantity', 1))
        userid = session['userid']

        if not itemid:
            return jsonify({
                "Status": "Failed",
                "Message": "Item id is required"
            }), 400

        if quantity <= 0:
            return jsonify({
                "Status": "Failed",
                "Message": "Quantity should be greater than zero"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        cursor.execute("select itemquantity from items where itemid=uuid_to_bin(%s)", (itemid,))
        item = cursor.fetchone()

        if not item:
            return jsonify({
                "Status": "Failed",
                "Message": "Product not found"
            }), 404

        stock = item[0]

        cursor.execute("select quantity from cart where userid=uuid_to_bin(%s) and itemid=uuid_to_bin(%s)", (userid, itemid))
        cartitem = cursor.fetchone()

        if cartitem:
            newqty = cartitem[0] + quantity

            if newqty > stock:
                return jsonify({
                    "Status": "Failed",
                    "Message": f"Only {stock} item(s) available in stock"
                }), 400

            cursor.execute("update cart set quantity=%s where userid=uuid_to_bin(%s) and itemid=uuid_to_bin(%s)", (newqty, userid, itemid))

            mydb.commit()

            return jsonify({
                "Status": "Success",
                "Message": "Cart updated successfully"
            }), 200

        if quantity > stock:
            return jsonify({
                "Status": "Failed",
                "Message": f"Only {stock} item(s) available in stock"
            }), 400

        cursor.execute("insert into cart(cartid,userid,itemid,quantity) values(uuid_to_bin(uuid()),uuid_to_bin(%s),uuid_to_bin(%s),%s)", (userid, itemid, quantity))

        mydb.commit()

        return jsonify({
            "Status": "Success",
            "Message": "Item added to cart successfully"
        }), 201

    except Exception as e:
        print("Mysql Error:", str(e))

        return jsonify({
            "Status": "Failed",
            "Message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/cart/view',methods=['GET'])
def viewcart():

    cursor=None 
    try:
        if 'userid' not in session:
            return jsonify({
                "status":"failed",
                "message":"Pls login first"
            }),401  
        #mysql connection
        mydb.ping(reconnect=True)
        userid=session.get('userid')
        cursor = mydb.cursor(buffered=True)
        cursor.execute("select bin_to_uuid(i.itemid),i.itemname,i.itemprice,i.category,i.itemfilename,c.quantity from items i inner join cart c on c.itemid=i.itemid where c.userid=uuid_to_bin(%s)",(userid,))
        cart_items=cursor.fetchall()
        if not cart_items:
            return jsonify({
                "status":"failed",
                "message":"Cart is empty"
            }),401
        subtotal=0
        items_data=[]
        for item in cart_items:
            itemid=item[0]
            item_name=item[1]
            item_price=float(item[2])
            item_quantity=int(item[5])
            item_category=item[3]
            item_imgname=item[4]
            amount=item_price*item_quantity
            subtotal=subtotal+amount
            image_url=url_for('static',filename=f'uploads/{item_imgname}',_external=True)
            items_data.append({'itemid':itemid,'itemname':item_name,'price':item_price,'quantity':item_quantity,'category':item_category,'image':image_url,'total':amount})
        delivery=40
        tax_=round(subtotal*0.05,2)
        grand_total=delivery+tax_+subtotal
        return jsonify({
            'Status':'Success',
            'cart_items':items_data,
            'summary':{
                "subtotal":subtotal,
                "delivery":delivery,
                "tax":tax_,
                "grand_total":grand_total
            }
        }),200
    except Exception as e:
        print('Mysql Error:',str(e))
        return jsonify({
            "status":"failed",
            "message":str(e)
        }),500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/cart/update',methods=['PUT'])
def updatecart():
    cursor=None
    try:
        if 'userid' not in session:
            return jsonify({
                "status":"failed",
                "message":"Pls login first"
            }),401
        data=request.get_json()
        print(data)
        if not data:
            return jsonify({
                "status":"failed",
                "message":"No Input data given"
            }),401
        itemid=data.get('itemid')
        try:
            updated_quantity=int(data.get('quantity',0))
        except ValueError:
            return jsonify({
                "status":"failed","message":"invalid quantity"
            })
        if not itemid:
            return jsonify({
                "status":"failed","message":"itemid required"
            })
        #mysql connection 
        mydb.ping(reconnect=True)
        userid=session.get('userid')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select quantity from cart where userid=uuid_to_bin(%s) and itemid=uuid_to_bin(%s)',[userid,itemid])
        existing_cart=cursor.fetchone()
        if not existing_cart:
            return jsonify({
                "status":"failed",
                "message":"No item in cart"
            }),401
        cursor.execute('select itemquantity from items where itemid=uuid_to_bin(%s)',[itemid])
        item=cursor.fetchone()
        if not item:
            return jsonify({
                "status":"failed","message":"No item found"
            })
        available_stock=item[0]
        if updated_quantity>available_stock:
            return jsonify({
                "status":"failed",
                "message":"Insufficient stock"
            }),400
        cursor.execute('update cart set quantity=%s where userid=uuid_to_bin(%s) and itemid=uuid_to_bin(%s)',[updated_quantity,userid,itemid])
        mydb.commit()
        return jsonify({
            "status":"success",
            "message":"cart Update succesfully"
        }),200
    except Exception as e:
        mydb.rollback()
        print('Mysql Error',str(e))
        return jsonify({
                "status":"failed",
                "message":f"{str(e)}"
            }),500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/cart/remove/<itemid>',methods=['DELETE'])
def removecart(itemid):
    cursor=None
    try:
        if 'userid' not in session:
            return jsonify({
                "status":"failed",
                "message":"Pls login first"
            }),401
        #mysql connection 
        mydb.ping(reconnect=True)
        userid=session.get('userid')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select itemquantity from items where itemid=uuid_to_bin(%s)',[itemid])
        item=cursor.fetchone()
        if not item:
            return jsonify({
                "status":"failed","message":"No item found"
            }),401
        cursor.execute('select quantity from cart where userid=uuid_to_bin(%s) and itemid=uuid_to_bin(%s)',[userid,itemid])
        existing_cart=cursor.fetchone()
        if not existing_cart:
            return jsonify({
                "status":"failed",
                "message":"No item in cart"
            }),401
        cursor.execute('delete from cart where userid=uuid_to_bin(%s) and itemid=uuid_to_bin(%s)',[userid,itemid])
        mydb.commit()
        return jsonify({
            "status":"success",
            "message":"cart item removed succesfully"
        }),200
    except Exception as e:
        mydb.rollback() 
        print('Mysql Error',str(e))
        return jsonify({
                "status":"failed",
                "message":f"{str(e)}"
            }),500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/payment/create-order', methods=['POST'])
def pay_cart():
    cursor = None

    try:
        if 'userid' not in session:
            return jsonify({
                "status": "failed",
                "message": "Please login first"
            }), 401

        data = request.get_json()
        payment_type = data.get('type', 'cart')

        mydb.ping(reconnect=True)
        userid = session.get('userid')
        cursor = mydb.cursor(buffered=True)

        if payment_type == 'cart':

            cursor.execute(
                "select bin_to_uuid(i.itemid),i.itemname,i.itemprice,i.category,i.itemfilename,c.quantity from items i inner join cart c on c.itemid=i.itemid where c.userid=uuid_to_bin(%s)",
                (userid,)
            )

            cart_items = cursor.fetchall()

            if not cart_items:
                return jsonify({
                    "status": "failed",
                    "message": "Cart is empty"
                }), 404

        else:

            itemid = data.get('itemid')
            quantity = int(data.get('quantity', 1))

            cursor.execute(
                "select bin_to_uuid(itemid),itemname,itemprice,category,itemfilename,itemquantity from items where itemid=uuid_to_bin(%s)",
                (itemid,)
            )

            item = cursor.fetchone()

            if not item:
                return jsonify({
                    "status": "failed",
                    "message": "Item not found"
                }), 404

            available_stock = item[5]

            if quantity > available_stock:
                return jsonify({
                    "status": "failed",
                    "message": "Insufficient stock"
                }), 400

            cart_items = [
                (
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    quantity
                )
            ]

        subtotal = 0
        items_data = []

        for item in cart_items:

            itemid = item[0]
            item_name = item[1]
            item_price = float(item[2])
            item_category = item[3]
            item_imgname = item[4]
            item_quantity = int(item[5])

            amount = item_price * item_quantity
            subtotal += amount

            image_url = url_for(
                'static',
                filename=f'uploads/{item_imgname}',
                _external=True
            )

            items_data.append({
                "itemid": itemid,
                "itemname": item_name,
                "price": item_price,
                "quantity": item_quantity,
                "category": item_category,
                "image": image_url,
                "total": amount
            })

        delivery = 40
        tax = round(subtotal * 0.05, 2)
        grand_total = subtotal + delivery + tax

        razorpay_amount = int(grand_total * 100)

        payment_order = client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "receipt": userid,
            "payment_capture": 1
        })

        return jsonify({
            "status": "success",
            "order": {
                "order_id": payment_order["id"],
                "amount": payment_order["amount"],
                "currency": payment_order["currency"]
            },
            "cart_items": items_data,
            "summary": {
                "subtotal": subtotal,
                "delivery": delivery,
                "tax": tax,
                "grand_total": grand_total
            },
            "razorpay_key_id": "rzp_test_TEuDHI8Wd0eKZt"
        }), 200

    except Exception as e:
        print("Order Creation:", str(e))

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/payment/verify',methods=['POST'])
def verify_payment():
    cursor=None
    try:
        data=request.get_json()

        # get frontend data
        payment_id=data.get('razorpay_payment_id')
        order_id=data.get('razorpay_order_id')
        signature=data.get('razorpay_signature')
        mode=data.get('mode','cart')
        # verify signature details
        params_dict={
            "razorpay_order_id":order_id,
            "razorpay_payment_id":payment_id,
            "razorpay_signature":signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            print(e)
            return jsonify({
                "Status":"Failed",
                "Message":"Could not verify razorpay details"
            }),400
        #login validation
        if 'userid' not in session:
            return jsonify({
                "Status":"Failed",
                "Message":"Please login first"
            }),401
        #mysql connection
        mydb.ping(reconnect=True)
        userid = session.get('userid')
        cursor = mydb.cursor(buffered=True)

        if mode == 'cart':

            cursor.execute(
                "select bin_to_uuid(i.itemid),i.itemname,i.itemprice,i.category,i.itemfilename,c.quantity from items i inner join cart c on c.itemid=i.itemid where c.userid=uuid_to_bin(%s)",
                (userid,)
            )

            cart_items = cursor.fetchall()

            if not cart_items:
                return jsonify({
                    "status": "failed",
                    "message": "Cart is empty"
                }), 404

        else:

            itemid = data.get('itemid')
            quantity = int(data.get('quantity', 1))

            cursor.execute(
                "select bin_to_uuid(itemid),itemname,itemprice,category,itemfilename,itemquantity from items where itemid=uuid_to_bin(%s)",
                (itemid,)
            )

            item = cursor.fetchone()

            if not item:
                return jsonify({
                    "status": "failed",
                    "message": "Item not found"
                }), 404

            available_stock = item[5]

            if quantity > available_stock:
                return jsonify({
                    "status": "failed",
                    "message": "Insufficient stock"
                }), 400

            cart_items = [
                (
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4],
                    quantity
                )
            ]

        subtotal = 0

        for item in cart_items:

            itemid = item[0]
            item_name = item[1]
            item_price = float(item[2])
            item_category = item[3]
            item_imgname = item[4]
            item_quantity = int(item[5])

            amount = item_price * item_quantity
            subtotal += amount
        delivery = 40
        tax = round(subtotal * 0.05, 2)
        grand_total = subtotal + delivery + tax
        # store order details
        cursor.execute("insert into orders(razorpay_orderid,razorpay_paymentid,userid,total_amount,grand_total,delivery,tax,status) values(%s,%s,uuid_to_bin(%s),%s,%s,%s,%s,'paid')",(order_id,payment_id,userid,subtotal,grand_total,delivery,tax))
        order_table_id=cursor.lastrowid
        orderdetails_insert='''insert into order_item_details(orderid,itemid,item_name,item_price,item_quantity,subtotal,item_category,item_filename) values(%s,uuid_to_bin(%s),%s,%s,%s,%s,%s,%s)'''
        ordered_items=[]
        for item in cart_items:
            itemid=item[0]
            item_name=item[1]
            item_price=float(item[2])
            item_quantity=int(item[5])
            item_category=item[3]
            item_imgname=item[4]
            amount=item_price*item_quantity
            subtotal+=amount
            cursor.execute(orderdetails_insert,[order_table_id,itemid,item_name,item_price,item_quantity,subtotal,item_category,item_imgname])
            # reduce stock
            cursor.execute('update items set itemquantity=itemquantity-%s where itemid=uuid_to_bin(%s)',[item_quantity,itemid])
            ordered_items.append({
                "itemid":itemid,
                "itemname":item_name,
                "price":item_price,
                "quantity":item_quantity,
                'subtotal':amount,
            })
            # after order successfull, clear the cart
            if mode=='cart':
                cursor.execute('delete from cart where userid=uuid_to_bin(%s)',[userid])
            mydb.commit()
            return jsonify({
                "Status":"Success",
                "Message":"Payment verified successfully",
                "payment":{
                    "payment_id":payment_id,
                    "order_id":order_id,
                },
                "summary":{
                    'subtotal':subtotal,
                    'delivery':delivery,
                    'tax':tax,
                    'grand_total':grand_total
                },
                "ordered_items":ordered_items
            })
    except Exception as e:
        mydb.rollback()
        print('Mysql Error',str(e))
        return jsonify({
                "status":"failed",
                "message":f"{str(e)}"
            }),500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/myorders', methods=['GET'])
def myorders():
    cursor = None

    try:
        if 'userid' not in session:
            return jsonify({
                "status": "failed",
                "message": "Please login first"
            }), 401

        mydb.ping(reconnect=True)
        userid = session.get('userid')
        cursor = mydb.cursor(buffered=True)

        cursor.execute(
            "select orderid,razorpay_orderid,razorpay_paymentid,total_amount,grand_total,delivery,tax,status,created_at from orders where userid=uuid_to_bin(%s) order by created_at desc",
            (userid,)
        )

        orders = cursor.fetchall()

        if not orders:
            return jsonify({
                "status": "success",
                "message": "No orders found",
                "orders": []
            }), 200

        orders_list = []

        for order in orders:

            orderid = order[0]
            razorpay_orderid = order[1]
            razorpay_paymentid = order[2]
            total_amount = float(order[3])
            grand_total = float(order[4])
            delivery = float(order[5])
            tax = float(order[6])
            status = order[7]
            created_at = order[8]

            cursor.execute(
                "select bin_to_uuid(itemid),item_name,item_price,item_quantity,subtotal,item_category,item_filename from order_item_details where orderid=%s",
                (orderid,)
            )

            items = cursor.fetchall()

            items_list = []

            for item in items:

                itemid = item[0]
                item_name = item[1]
                item_price = float(item[2])
                item_quantity = int(item[3])
                subtotal = float(item[4])
                item_category = item[5]
                item_imgname = item[6]

                image_url = url_for(
                    'static',
                    filename=f'uploads/{item_imgname}',
                    _external=True
                )

                items_list.append({
                    "itemid": itemid,
                    "itemname": item_name,
                    "price": item_price,
                    "quantity": item_quantity,
                    "subtotal": subtotal,
                    "category": item_category,
                    "image": image_url
                })

            orders_list.append({
                "orderid": orderid,
                "razorpay_orderid": razorpay_orderid,
                "payment_id": razorpay_paymentid,
                "total_amount": total_amount,
                "grand_total": grand_total,
                "delivery": delivery,
                "tax": tax,
                "status": status,
                "created_at": created_at,
                "items": items_list
            })

        return jsonify({
            "status": "success",
            "message": "Orders fetched successfully",
            "orders": orders_list
        }), 200

    except Exception as e:
        print("Mysql Error:", str(e))

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/orders/<int:ordid>', methods=['GET'])
def myorder_details(ordid):
    cursor = None

    try:
        if 'userid' not in session:
            return jsonify({
                "status": "failed",
                "message": "Please login first"
            }), 401

        mydb.ping(reconnect=True)
        userid = session.get('userid')
        cursor = mydb.cursor(buffered=True)

        cursor.execute(
            "select orderid,razorpay_orderid,razorpay_paymentid,total_amount,delivery,tax,grand_total,status,created_at from orders where userid=uuid_to_bin(%s) and orderid=%s",
            (userid, ordid)
        )

        order_data = cursor.fetchone()

        if not order_data:
            return jsonify({
                "status": "failed",
                "message": "Order not found"
            }), 404

        cursor.execute(
            "select orderdetails_id,bin_to_uuid(itemid),item_name,item_price,item_quantity,subtotal,item_category,item_filename from order_item_details where orderid=%s",
            (ordid,)
        )

        order_items = cursor.fetchall()

        order_json = {
            "orderid": order_data[0],
            "razorpay_orderid": order_data[1],
            "razorpay_paymentid": order_data[2],
            "total_amount": float(order_data[3]),
            "delivery": float(order_data[4]),
            "tax": float(order_data[5]),
            "grand_total": float(order_data[6]),
            "status": order_data[7],
            "created_at": order_data[8]
        }

        items_json = []

        for item in order_items:
            print(item[7])

            image_url = url_for('static',filename=f"uploads/{item[7]}",_external=True)

            items_json.append({
                "order_details_id": item[0],
                "item_id": item[1],
                "item_name": item[2],
                "item_price": float(item[3]),
                "item_quantity": item[4],
                "subtotal": float(item[5]),
                "item_category": item[6],
                "item_image": image_url
            })

        return jsonify({
            "status": "success",
            "order": order_json,
            "items": items_json
        }), 200

    except Exception as e:
        print("Mysql Error:", str(e))

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

@app.route('/api/search', methods=['GET'])
def usersearch():
    cursor = None

    try:

        searchdata = request.args.get('q', '').strip()

        if not searchdata:
            return jsonify({
                "status": "failed",
                "message": "Search query required"
            }), 400

        pattern = re.compile(r'^[A-Za-z0-9 ]+$')

        if not pattern.match(searchdata):
            return jsonify({
                "status": "failed",
                "message": "Invalid search"
            }), 400

        mydb.ping(reconnect=True)
        cursor = mydb.cursor(buffered=True)

        keyword = f"%{searchdata}%"

        cursor.execute(
            "select bin_to_uuid(itemid),itemname,itemdescription,itemAbout,itemprice,itemquantity,category,itemfilename from items where itemname like %s or itemdescription like %s or category like %s",
            (keyword, keyword, keyword)
        )

        allitems_data = cursor.fetchall()

        items = []

        for item in allitems_data:

            items.append({
                "itemid": item[0],
                "itemname": item[1],
                "item_desc": item[2],
                "item_about": item[3],
                "price": float(item[4]),
                "quantity": item[5],
                "category": item[6],
                "image": url_for(
                    'static',
                    filename=f'uploads/{item[7]}',
                    _external=True
                )
            })

        return jsonify({
            "status": "success",
            "message": "Items fetched successfully",
            "items": items
        }), 200

    except Exception as e:
        print("Mysql Error:", str(e))

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
@app.route('/api/invoice/<int:ordid>',methods=['GET'])
def get_invoice(ordid):
    cursor=None
    try:
        if 'userid' not in session:
            return jsonify({
                "status":"failed",
                "message":"Pls login first"
            }),401
        #mysql connect
        mydb.ping(reconnect=True)
        userid=session.get('userid')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('''select orderid,razorpay_orderid,razorpay_paymentid,total_amount,delivery,tax,grand_total,status,created_at from orders where userid=uuid_to_bin(%s) and orderid=%s''',[userid,ordid])   
        order_data=cursor.fetchone()
        if not order_data:
            return jsonify({
                "status":"failed",
                "message":"order not found"
            }),401
        cursor.execute('''select item_name,item_price,item_quantity,subtotal,item_category,item_filename from order_item_details where orderid=%s''',[ordid])
        orders_items=cursor.fetchall()
        #----------------CREATE PDF BUFFER--------------
        pdf_buffer=BytesIO()
        #--------------------create document---------------
        doc=SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightmargin=30,
            leftMargin=30,
            topMargin=30,
            buttomMargin=20
        )
        styles=getSampleStyleSheet()
        elements=[]
        #-----------------------Set Title--------
        title=Paragraph(
            "<b>BUYROUTE Invoice</b>",styles['Title']
        )
        elements.append(title)
        elements.append(Spacer(1,15))
        
        #-----------------------order details-------------
        order_info=f'''
        <b>ORDER ID:</b> {order_data[0]}<br/>
        <b>Razorpay order ID:</b> {order_data[1]}<br/>
        <b>Razorpay Payment ID:</b> {order_data[2]}<br/>
        <b>Order date:</b> {order_data[8]}<br/>'''
        order_para=Paragraph(
            order_info,
            styles['BodyText']
        )
        elements.append(order_para)
        elements.append(Spacer(1,10))
        elements.append(HRFlowable(width="100%"))
        elements.append(Spacer(1,15))
        #-------------------Table Format and data ---------------
        table_data=[['Itemname','Itemcategory','Itemprice','Itemquantity','subtotal']]
        for item in orders_items:
            table_data.append([item[0][0:20],item[4],f"₹{float(item[1])}",str(item[2]),f"₹{float(item[3])}"])
        #---------------create table----------------
        table=Table(table_data,colWidths=[180,100,80,70,80])
        #------------table style
        table.setStyle(
            TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0d6efd')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('FONTSIZE',(0,0),(-1,-1),10),
                ('BOTTOMPADDING',(0,0),(-1,0),10),
                ('GRID',(0,0),(-1,-1),1,colors.black),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                ('ALIGN',(2,1),(-1,-1),'CENTER')                
            ])
        )
        elements.append(table)
        elements.append(Spacer(1,20))
        #---------------------------Summary----------------
        summary=f"""
        <b>ITEM ToTAL:</b> ₹{float(order_data[3])}<br/><br/>
        <b>Delivery:</b> ₹{float(order_data[4])}<br/><br/>
        <b>Tax:</b> ₹{float(order_data[5])}<br/><br/>
        <b>GRAND ToTAL:</b> ₹{float(order_data[6])}<br/><br/>"""
        summary_para=Paragraph(
            summary,
            styles['Heading3']
        )
        elements.append(summary_para)
        elements.append(Spacer(1,25))
        #------------------Footer----------
        footer=Paragraph("Thank you for shopping with BUYROUTE",styles['Italic'])
        elements.append(footer)
        #-----------------Build pdf-------
        doc.build(elements)
        pdf_buffer.seek(0)
        #---------------------------RESPONSE----------------------
        response=make_response(
            pdf_buffer.getvalue()
        )
        response.headers['Content-Type']='application/pdf'
        response.headers['Content-Disposition']=(
            f'attachment; filename=invoice_{ordid}.pdf'
        )
        return response
    except Exception as e:
        print(str(e))
        return jsonify({
                "status":"failed",
                "message":f"{str(e)}"
            }),500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/user/forgotpassword',methods=['POST'])
def forgotpassword():
    try:
        data=request.get_json()
        f_email=data.get('email')
        mydb.ping(reconnect=True) #if connection lost it reconnects the mysql server
        cursor=mydb.cursor(buffered=True)
        #email recheck
        cursor.execute('select count(*) from userdata where useremail=%s',[f_email])
        email_exists=cursor.fetchone()[0]
        if email_exists==0:
            return jsonify({
                "status":"failed",
                "message":f"Email Not found"
                }),400
        reset_link=f"{url_for('resetpassword',data=endata(f_email),_external=True)}"
        subject='User forgotpassword Reset link for Ecommy Appy'
        body=f"click the given :\n{reset_link}"
        send_mail(to=f_email,subject=subject,body=body)
        return jsonify({
            "status":"success",
            "message":"Reset link has been sent to given mail"
        })
    except Exception as e:
        print(str(e))
        return jsonify({
                "status":"failed",
                "message":f"{str(e)}"
            }),500
    finally:
        if cursor:
            cursor.close()

@app.route('/resetpassword/<token>',methods=['PUT'])
def resetpassword(token):
    data=request.get_json()
    npassword=data.get('password')
    cpassword=data.get('confirm_password')
    if npassword!=cpassword:
        return jsonify({
            "Status":"Failed",
            "Message":"Passwords do not match"
        }),400
    email=dndata(token)
    hashed_pwd=bcrypt.generate_password_hash(npassword)
    cursor=mydb.cursor(buffered=True)
    cursor.execute('update userdata set password=%s where useremail=%s',[hashed_pwd,email])
    mydb.commit()
    return jsonify({
        "Status":"Success",
        "Message":f"Password updated successfully"
    }),200            

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)