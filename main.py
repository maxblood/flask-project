from flask import Flask ,render_template,session,redirect,request
import boto3
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hello-world'
app.config['UPLOADER_FOLDER'] = "/home/harsh/data_uploader"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@127.0.0.1/cloud_simulation"
db = SQLAlchemy(app)



class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    phone_num = db.Column(db.String(15),  nullable=False)
    msg = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(120),  nullable=False)




@app.route("/home")
def home():
    return render_template('index.html')






@app.route("/about")
def about():
    return render_template('about.html')






@app.route("/network")
def network():
    if ('user' in session and session['user'] == "harsh"):
        user = session['user']
        return render_template('network.html',user=user)
    else:
        return redirect('/dashboard')





@app.route("/command")
def command():
    if ('user' in session and session['user'] == "harsh"):
        ec2 = boto3.resource('ec2')

        vpc = ec2.create_vpc(CidrBlock='172.16.0.0/16')

        vpc.create_tags(Tags=[{"Key": "Name", "Value": "new_vpc"}])

        vpc.wait_until_available()

        ec2Client = boto3.client('ec2')
        ec2Client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsSupport={'Value': True})
        ec2Client.modify_vpc_attribute(VpcId=vpc.id, EnableDnsHostnames={'Value': True})

        internetgateway = ec2.create_internet_gateway()
        vpc.attach_internet_gateway(InternetGatewayId=internetgateway.id)

        routetable = vpc.create_route_table()
        route = routetable.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=internetgateway.id)

        subnet = ec2.create_subnet(CidrBlock='172.16.1.0/24', VpcId=vpc.id)
        routetable.associate_with_subnet(SubnetId=subnet.id)

        securitygroup = ec2.create_security_group(GroupName='SSH-ONLY', Description='only allow SSH traffic', VpcId=vpc.id)
        securitygroup.authorize_ingress(CidrIp='0.0.0.0/0', IpProtocol='tcp', FromPort=22, ToPort=22)

        complete = "Infrastructure is deployed succesfully [Check AWS console!]"
        success = "\n\nis created successfully..."
        return render_template('network.html',vpc=str(vpc) + success,IGW=str(internetgateway) +success,routetable=str(routetable)+success,subnet=str(subnet)+success,securitygroup=str(securitygroup)+success,complete=complete)





@app.route("/dashboard", methods= ['GET','POST'])
def login():
    
    if ('user' in session and session['user'] == "harsh"):
        user = session['user']
        return render_template('dashboard.html',user=user)

    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == "harsh" and password == "12345":
            session['user'] = username
            user = username
            return render_template('dashboard.html',user=user)

    return render_template('login.html')



@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')



@app.route("/s3/<string:s3_slug>")
def s3_bucket(s3_slug):
    if ('user' in session and session['user'] == "harsh"):
        if s3_slug == '0':
            return render_template('s3.html')
        elif s3_slug == '1':
            s3 = boto3.resource('s3')
            response = []
            for bucket in s3.buckets.all():
                response.append(bucket.name)
            return render_template("s3.html",response=response)

    else:
        return redirect('/dashboard')



@app.route("/uploader", methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == "harsh"):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOADER_FOLDER'],f.filename ))
            return redirect('/s3/0')



@app.route("/contact", methods= ['GET','POST'])
def contact():
    if (request.method == 'POST'):

        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')

        entry = Contacts(name=name, phone_num=phone, msg= message,date = datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()

    return render_template('contacts.html')








app.run(debug=True)
