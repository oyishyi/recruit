# python3

#########################################################
# import module
#########################################################
from flask import Flask, render_template, request,session,\
                    redirect, url_for, jsonify, g
from sqlalchemy import func
import re
import json
import webbrowser
import os

#Library not in CSE
from geopy import distance
from geopy.geocoders import GoogleV3



#our library
from models import  user_favorite, company_favorite, user, degree, communication_record, \
                    job_request, resume, experience, qualification, job_position, offer_tb
import test_config, config
from exts import db, nlp

#########################################################
# environment setup
#########################################################
app = Flask(__name__)
app.config.from_object(config)

db.init_app(app)
with app.app_context():
    db.create_all()

basedir = os.path.abspath(os.path.dirname(__file__))

#########################################################
# view function
#########################################################
@app.route('/')
@app.route('/loginhome')
def home():
    if hasattr(g, 'user'):
        return render_template("loginhome.html")
    else:
        return render_template("home.html")
    

@app.route('/login',methods=["POST","GET"])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        email = request.values.get('email')
        password = request.values.get('pwd')
        # "Job Seeker" or "Employer"
        usertype = request.values.get('usertype')
        type = request.values.get('type')
        # register
        if type=='new':
            existed_user = user.query.filter(user.email == email).first()
            if existed_user:
                #'This email is already registered'
                return json.dumps({'state': 'exist'})
            else:
                # success
                new_user = user(email=email, password=password, user_type=usertype)
                db.session.add(new_user)
                db.session.commit()
                session["user_id"] = new_user.id
                session.permanent = True
                return json.dumps({'state': 'login'})
        # login
        if type == 'login':
            existed_user = user.query.filter(user.email == email, user.password == password).first()
            # success
            if existed_user:
                session["user_id"] = existed_user.id
                session.permanent = True
                return json.dumps({'state':'login'})

            else:
                # 'Wrong email or password'
                return json.dumps({'state': 'wrong'})
    return json.dumps({'state': 'wrong'})

# logout
@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('home'))




@app.route('/carousel')
def carousel():
    return render_template("carousel.html")

# view account profile
@app.route('/account', methods=["GET"])
def account():
    curr_user = g.user
    degree = None
    if curr_user.user_type == 'Job Seeker':
        # return None if no related information
        degrees = curr_user.degrees
        degree = {"degree": [(i.degree, i.major) for i in degrees]}

        requests = curr_user.job_requests  # access data
        jobrequest = {request.id: request.jobname for request in requests}

        return render_template("psAcc.html", curr_user=curr_user, degree=degree, jobrequest=jobrequest)
    else:
        all_pos = job_position.query.order_by(db.text('pos_name')).all()
        jobtype = sorted(list(set(pos.pos_name for pos in all_pos)))
        return render_template("coAcc.html", curr_user=curr_user,jobtype=jobtype)

        
@app.route('/verify_location', methods=["POST"])
def verify_location():
    location = request.values.get('location')
    if location == '' or location == 'None':
        result = None
    else:
        # using google map api
        geolocator = GoogleV3(api_key = 'AIzaSyBcVwMOSzZ7RwO3qHr_cocoL3T1zFgsxH4', user_agent='oyishyi')
        search_location = geolocator.geocode(location, exactly_one=False)
        if search_location != None:
            search_location = [i.address for i in search_location]
            result = search_location
        else:
            result = None
    return json.dumps({"result": result})


# job_position table for employer
@app.route('/poststable')
def poststable():
    curr_user = g.user
    #database read
    positions = job_position.query.filter(job_position.comp_id == curr_user.id).\
                                order_by(db.text('-create_time')).all()
    jobpost = {position.id: position.pos_name for position in positions}
    return render_template("poststable.html", jobpost=jobpost)

# update account profile
@app.route('/updateprofile', methods=["POST","GET"])
def updateprofile():

    curr_user=g.user

    # database read
    getData = request.values

    #database update
    # icon
    path = basedir + "/static/userIcon/"
    img = request.files['icon']
    print(img)
    if img:
        file_path = path + str(g.user.id) + '.png'
        img.save(file_path)
        curr_user.icon = "/static/userIcon/" + str(g.user.id) + '.png'

    if curr_user.user_type == 'Job Seeker':
        # school num is related to marjor num. but the num is not in order。
        # {'real_name': 'John W', 'birth_day': '2020-01-01', 'location': 'Australia NSW Sydeny UNSW', 'school': 's',
        # 'major': 'm', 'school3': 'ww', 'major3': 'ee', 'desc': 'good'}
        # at least one degree
        degrees = {getData["school"]:getData["major"]}
        # after the below loop, the dict will be {school：major}。--  {'s': 'm', 's1': 'm1'}
        for i in range(7): # num of degrees cannot over 7
            if "school"+str(i) in getData:
                degrees[getData["school"+str(i)]] = getData["major"+str(i)]
        # delete all old degree, and add all the new degrees
        # because degrees is small
        degree.query.filter(degree.user_id == curr_user.id).delete()
        for i in degrees:
            new_degree = degree(user_id = curr_user.id, degree = i, major = degrees[i])
            db.session.add(new_degree)
            db.session.commit()
        
        curr_user.real_name = getData['real_name']
        curr_user.birth_day = getData['birth_day']
        curr_user.location = getData['location']
        curr_user.desc = getData['desc']
        db.session.commit()
        return json.dumps({"state":"success"})
    else:
        curr_user.real_name = getData['real_name'] # company name
        curr_user.location = getData['location']
        curr_user.desc = getData['desc']
        db.session.commit()
        return json.dumps({"state":"success"})

@app.route('/geticon',methods=['POST'])
def geticon():
    icon = g.user.icon
    if icon != '':
        return json.dumps({'icon': icon})
    else:
        return json.dumps({'icon': None})

# change password
@app.route('/changepwd',methods=["POST","GET"])
def changepwd():
    if request.method=="GET":
        return render_template("changepwd.html")
    else:
        getData = request.values
        curr_user = g.user
        # wrong old password
        if getData.get('currpwd') != curr_user.password:
            return json.dumps({"state": "wrong"})
        # change password
        curr_user.password = getData.get('newpwd')
        db.session.commit()
        return json.dumps({"state": "success"})

####################################
# my_joblist function，whichi display 'hot'，'need'
# <display> parameter can be ['hot, 'need']
# return one type of joblist each time
# when you open homepage，whis functionwill be called twice，one for ‘hot’，another for ‘need’
####################################
joblist = {}
@app.route('/joblist/<display>',methods=["POST","GET"])
def my_joblist(display):
    global joblist
    if display == "hot":
        joblist={}
        # database read
        data = job_position.query.order_by(db.text('-submitted_nb')).limit(10).all()
        for i in range(10): #show the first 10 items
            try:
                curr_data = data[i]
            except IndexError:
                break
            joblist[str(i)] = {"id":curr_data.id, \
                    "pos_name":curr_data.pos_name,\
                    "company_name":curr_data.company.real_name,\
                    "employment_type":curr_data.employment_type,\
                    "location":curr_data.location,\
                    "closing_date":curr_data.closing_date,\
                    "pos_desc":curr_data.pos_desc
                    }
    if display == "need":
        joblist={}
        # database read
        data = job_position.query.order_by(db.text('-(recruiting_nb/(submitted_nb+1))')).limit(10).all()
        for i in range(10): #show the first 10 items
            try:
                curr_data = data[i]
            except IndexError:
                break
            joblist[str(i)] = {"id":curr_data.id, \
                    "pos_name":curr_data.pos_name,\
                    "company_name":curr_data.company.real_name,\
                    "employment_type":curr_data.employment_type,\
                    "location":curr_data.location,\
                    "closing_date":curr_data.closing_date,\
                    "pos_desc":curr_data.pos_desc
                    }
        
    return render_template("joblist.html", data=joblist)

#########################################
### job information page
@app.route('/jobInfo/<pos_id>')
def jobinfo(pos_id):

    # acquire the info of job_position fro mdatabase
    curr_position = job_position.query.filter(job_position.id == pos_id).first()

    # Integrate 'exp' to 'qual'， f'you need at least {} year {} experience'
    qualification = curr_position.qualification # if experience==1，qualification==0，\
                                                # then qualification will be 1，otherwise the front-end will ignore it
    qual_des = curr_position.qual_des.split('\r\n')
    # when qualifiction doesn't appear ‘experience’，add it
    # this is hard_code because our data is from web crawler, we need to deal with them
    if curr_position.experience == '1' and not any('experience' in i for i in qual_des):
        if qualification == '0':
            qual_des = [f'You should have a {curr_position.exp_dura.lower()} {curr_position.exp_type.lower()}.']
        else:
            qual_des+=[f'You should have a {curr_position.exp_dura.lower()} {curr_position.exp_type.lower()}.']
        qualification = '1'
        if curr_position.exp_des != 'NaN':
            qual_des+=[curr_position.exp_des]
    if curr_position.responsibility == '':
        responsibility = []
    else:
        responsibility = curr_position.responsibility.split('\r\n')
    # transfer the sqlalchemy class to dict
    info = {"id":pos_id,
            "pos_name":curr_position.pos_name,
            "company_name":curr_position.company.real_name,
            "employment_type":curr_position.employment_type,
            "company_desc":curr_position.company.desc,
            "pos_desc":curr_position.pos_desc,
            "experience":curr_position.experience, # required experience is not shown
            "exp_dura":curr_position.exp_dura,
            "exp_type":curr_position.exp_type,
            "exp_des":curr_position.exp_des if curr_position.exp_des != 'NaN' else 'No description',
            "qualification":qualification, #changed qualification
            "req_qual":curr_position.req_qual,
            "qual_des":qual_des,
            "salary":curr_position.salary,
            "salary_type":curr_position.salary_type,
            "location":curr_position.location,
            "responsibility":responsibility,
            "recruiting_nb":curr_position.recruiting_nb,
            "closing_date":curr_position.closing_date,
            "submitted_nb":curr_position.submitted_nb
            }
    
    # login status
    if hasattr(g, 'user') and g.user.user_type == 'Job Seeker':
        fav = (g.user in curr_position.favorite_users)
        return render_template("jobInfo.html",info=info, fav=fav)
    elif hasattr(g, 'user') and g.user.user_type == 'Employer':
        return render_template("ejobInfo.html",info=info)
    else:
        return render_template("njobInfo.html",info=info)

##############################
#### favorite position function
@app.route('/favorite/<job_id>/<fav>',methods=["POST","GET"])
def favorite(job_id,fav):
    # if fav == 1，favorite
    # if fav == 0， cancel favorite
    curr_user = g.user
    
    if curr_user.user_type == 'Job Seeker':
        if fav == '1':
            added_position = job_position.query.filter(job_position.id == job_id).first()
            curr_user.favorite_jobs.append(added_position)
            db.session.commit()
        else:
            removed_position = job_position.query.filter(job_position.id == job_id).first()
            curr_user.favorite_jobs.remove(removed_position)
            db.session.commit()
        return json.dumps({"state": "success"})
    else: # curr_user.user_type == 'Employer'
        if fav == '1':
            added_request = job_request.query.filter(job_request.id == job_id).first()
            curr_user.favorite_requests.append(added_request)
            db.session.commit()
        else:
            removed_request = job_request.query.filter(job_request.id == job_id).first()
            curr_user.favorite_requests.remove(removed_request)
            db.session.commit()
        return json.dumps({"state": "success"})

##############################
#### favorite position shown in account profile
@app.route('/favjobstable', methods=["POST", "GET"])
def favjobstable():
    curr_user = g.user
    favjobs_database = curr_user.favorite_jobs
    favjobs = {i.id: {'pos_name': i.pos_name, 'com_name': i.company.real_name} for i in favjobs_database}
    return render_template("favjobstable.html", favjobs = favjobs)
@app.route('/delfavjob', methods=["POST"])
def delfavjob():
    curr_user = g.user
    pos_id = request.values.get("pos_id")
    deleted_pos = job_position.query.filter(job_position.id == pos_id).first()
    curr_user.favorite_jobs.remove(deleted_pos)
    db.session.commit()
    return json.dumps({"state": "success"})


# submit resume in job_position info page
@app.route('/resume/<pos_id>', methods = ['GET', 'POST'])
def resumepage(pos_id):
    if request.method == 'GET':
        return render_template('resume.html', pos_id = pos_id)
    else:
        # resume
        jobpos_id = pos_id
        #one user can only submit one time for each jobposition
        if resume.query.filter(resume.user_id == g.user.id, resume.jobpos_id == jobpos_id).first() != None:
            return json.dumps({"state": "fail"})
        phone_num = request.values.get('phone_num')
        my_experience = request.values.get('experience')
        my_qualification = request.values.get('qualification')
        expected_salary = request.values.get('expected_salary')
        skill = request.values.get('skill')
        ps = request.values.get('ps')

        # attachment
        path = basedir + "/static/attachment/"
        attachment = request.files['attachment']
        print(attachment)
        

        new_resume = resume(user_id=g.user.id, jobpos_id=jobpos_id, phone_num=phone_num, experience=my_experience, qualification=my_qualification,\
                            expected_salary=expected_salary, skill=skill, ps=ps)
        db.session.add(new_resume)
        db.session.commit()
        if attachment:
            file_path = path + str(new_resume.id) + '.pdf'
            attachment.save(file_path)
            new_resume.attachment = ("/static/attachment/" + str(new_resume.id) + '.pdf')
            db.session.commit()
        # add experience
        if my_experience == '1':
            start_date = request.values.get('start_date')
            end_date = request.values.get('end_date')
            exp_type = request.values.get('exp_type')
            exp_desc = request.values.get('exp_desc')
            new_experience = experience(resume_id=new_resume.id, start_date=start_date, end_date=end_date, type=exp_type, desc=exp_desc)
            db.session.add(new_experience)
            db.session.commit()

        # add qualification
        if my_qualification == '1':
            qual_date = request.values.get('qual_date')
            qual_type = request.values.get('qual_type')
            qual_desc = request.values.get('qual_desc')
            new_qualification = qualification(resume_id=new_resume.id, date=qual_date, type=qual_type, desc=qual_desc)
            db.session.add(new_qualification)
            db.session.commit()

        #change submitted_nb
        curr_position = job_position.query.filter(job_position.id == pos_id).first()
        curr_position.submitted_nb+=1
        db.session.commit()

        return json.dumps({"state": "success"})

# job request list in the home page
@app.route('/jobrequest')
def jobrequest():
    request = {}
    latest_requests = job_request.query.order_by(db.text('-create_time')).limit(10).all()
    for i in range(10):
        try:
            data = latest_requests[i]
        except IndexError:
            break
        request[str(i)] = {
            "request_id": data.id,
            "real_name": data.user.real_name,
            'icon': data.user.icon,
            "pos_name": data.jobname,
            "desc": data.desc
        }
    return render_template("jobrequest.html", data=request)

@app.route('/requeststable')
def requeststable():
    ### jobseeker requests table
    jobrequest = {}
    all_requests = job_request.query.filter(job_request.user_id==g.user.id).order_by(db.text('-create_time')).all()
    jobrequest = {request.id: request.jobname for request in all_requests}

    return render_template("requeststable.html", jobrequest=jobrequest)

###############################################
### seeker add request
@app.route('/request',methods=["POST","GET"])
def requestpage():
    if request.method == "GET":
        return render_template("request.html")
    else:
        getData = request.values
        print(getData)
        jobname = getData.get('jobname')

        exp_need = getData.get('exp_need')
        if exp_need == '1':
            exp_duration = getData.get('exp_duration')
            exp_type = getData.get('exp_type')
            exp_desc = getData.get('exp_desc')
        else:
            exp_duration = ''
            exp_type = ''
            exp_desc = ''

        qual_need = getData.get('qualification')
        if qual_need == '1':
            qual_date = getData.get('qual_date')
            qual_type =  getData.get('qual_type')
            qual_desc = getData.get('qual_desc')
        else:
            qual_date = ''
            qual_type = ''
            qual_desc = ''

        desc = getData.get('desc')
        phone_num = getData.get('phone_num')
        new_request = job_request(user_id=g.user.id, phone_num=phone_num, jobname=jobname, exp_need=exp_need, exp_duration=exp_duration,\
                                    exp_type=exp_type, exp_desc=exp_desc, qual_need=qual_need, qual_date=qual_date,\
                                        qual_type=qual_type, qual_desc=qual_desc, desc=desc)
        db.session.add(new_request)
        db.session.commit()
        # [('jobname', 'nurse'), ('exp_need', '1'), ('exp_duration', 'Less than one year'), ('exp_type', 'Internship'),
        #  ('exp_desc', 'good'), ('qual_need', '1'), ('qual_date', '2020-10-09'), ('qual_type', 'Award')])]
        return json.dumps({"state": "success", 'id': new_request.id})

###############################################
### seeker delete request
@app.route('/deljobrequest',methods=["POST","GET"])
def deljobrequest():
    request_id = request.values.get("request_id")
    print(request_id)
    try:
        job_request.query.filter(job_request.id == request_id).delete()
        db.session.commit()
        return json.dumps({"state": "success"})
    except:
        db.session.rollback()
        return json.dumps({"state": "fail"})

###############################################
### seeker change request
@app.route('/editrequest/<job_id>',methods=["POST","GET"])
def editrequest(job_id):
    #acquire request info
    requestinfo = job_request.query.filter(job_request.id == job_id).first()
    if request.method == "GET":
        return render_template("editrequest.html", requestinfo=requestinfo)
    else:
        getData = request.values
        requestinfo.jobname = getData.get('jobname')

        exp_need = getData.get('exp_need')
        requestinfo.exp_need = exp_need
        if exp_need == '1':
            requestinfo.exp_duration = getData.get('exp_duration')
            requestinfo.exp_type = getData.get('exp_type')
            requestinfo.exp_desc = getData.get('exp_desc')
        else:
            exp_duration = ''
            exp_type = ''
            exp_desc = ''
        
        qual_need = getData.get('qual_need')
        requestinfo.qual_need = qual_need
        if qual_need == '1':
            requestinfo.qual_date = getData.get('qual_date')
            requestinfo.qual_type =  getData.get('qual_type')
            requestinfo.qual_desc = getData.get('qual_desc')
        else:
            qual_date = ''
            qual_type = ''
            qual_desc = ''

        requestinfo.desc = getData.get('desc')
        requestinfo.phone_num = getData.get('phone_num')

        db.session.commit()
        return json.dumps({"state": "success"} )

#### favorite job request
@app.route('/favrequeststable', methods=["POST", "GET"])
def favrequeststable():
    curr_user = g.user
    favreuqests_database = curr_user.favorite_requests
    favreuqests = {i.id: {'pos_name': i.jobname, 'real_name': i.user.real_name} for i in favreuqests_database}
    return render_template("favrequeststable.html", favreuqests=favreuqests)

## delete favorite request
@app.route('/delfavrequest', methods=["POST"])
def delfavrequest():
    curr_user = g.user
    pos_id = request.values.get("pos_id")
    print(pos_id)
    deleted_request = job_request.query.filter(job_request.id == pos_id).first()
    curr_user.favorite_requests.remove(deleted_request)
    db.session.commit()
    return json.dumps({"state": "success"})
    # return json.dumps({"state":"fail"})

# job request description page
@app.route('/requestInfo/<request_id>', methods=['GET'])
def requestInfo(request_id):
    curr_request = job_request.query.filter(job_request.id == request_id).first()
    info={
        'request_id':curr_request.id,
        'icon': curr_request.user.icon,
        'phone_num':curr_request.phone_num,
        'real_name':curr_request.user.real_name,
        'jobname':curr_request.jobname,
        'desc':curr_request.desc,
        'exp_need':curr_request.exp_need,
        'exp_duration':curr_request.exp_duration,
        'exp_type':curr_request.exp_type,
        'exp_desc':curr_request.exp_desc,
        'qual_need':curr_request.qual_need,
        'qual_date':curr_request.qual_date,
        'qual_type':curr_request.qual_type,
        'qual_desc':curr_request.qual_desc,
        'location':curr_request.user.location
    }
    if hasattr(g, 'user') and g.user.user_type == 'Employer':
        fav = (g.user in curr_request.favorite_users)
        return render_template("requestInfo.html", info=info, fav=fav)
    elif hasattr(g, 'user') and g.user.user_type == 'Job Seeker':
        return render_template("srequestInfo.html", info=info)
    else:
        return render_template("nrequestInfo.html", info=info)

#########################################
### employer account page, add job position
@app.route('/post', methods=["POST", "GET"])
def postpage():
    if request.method == "GET":
        return render_template("post.html")
    else:
        pos_name = request.values.get('pos_name')
        pos_desc = request.values.get('pos_desc')

        employment_type = request.values.get('employment_type')
        salary = request.values.get('salary')
        salary_type = request.values.get('salary_type')

        location = request.values.get('location')
        responsibility = request.values.get('responsibility')

        experience = request.values.get('experience')
        if experience == '1':
            exp_dura = request.values.get('exp_dura')
            exp_type = request.values.get('exp_type')
            exp_des = request.values.get('exp_des')
        else:
            exp_dura = ''
            exp_type = ''
            exp_des = ''

        qualification = request.values.get('qualification')
        if qualification == '1':
            req_qual = request.values.get('req_qual')
            qual_des = request.values.get('qual_des')
        else:
            req_qual = ''
            qual_des = ''
        recruiting_nb = request.values.get('recruiting_nb')
        closing_date = request.values.get('closing_date')


        new_jobpos = job_position(comp_id=g.user.id, pos_name=pos_name, pos_desc=pos_desc,\
                          employment_type=employment_type, salary=salary,salary_type=salary_type,\
                          location=location,responsibility=responsibility,\
                          experience=experience,exp_dura=exp_dura,exp_type=exp_type,exp_des=exp_des,\
                          qualification=qualification,req_qual=req_qual,qual_des=qual_des,\
                          recruiting_nb=recruiting_nb,closing_date=closing_date
                          )

        db.session.add(new_jobpos)
        db.session.commit()


        # [('pos_name', 'nurse'), ('desc', 'good'), ('employment_type', 'Full-time job'),
        #  ('salary', '12'), ('salary_type', 'per hour'), ('location', 'Sydeny'),
        #  ('responsibility', 'kind'), ('experience', '1'), ('qual_need', '1'),
        #  ('qual_type', 'Award'), ('qualification', 'first price'),
        #  ('recruiting_nb', '12'), ('closing_date', '2020-10-23')]
        return json.dumps({"state": "success", 'id': new_jobpos.id})
###############################################
#### delete job position
@app.route('/deljobpost',methods=["POST","GET"])
def deljobpost():
    pos_id = request.values.get("pos_id")
    try:
        job_position.query.filter(job_position.id == pos_id).delete()
        db.session.commit()
        return json.dumps({"state": "success"})
    except:
        db.session.rollback()
        return json.dumps({"state":"fail"})
###############################################
#### change job position
@app.route('/editpost/<pos_id>',methods=["POST","GET"])
def editpost(pos_id):
    jobInfo = job_position.query.filter(job_position.id == pos_id).first()
    if request.method == "GET":
        return render_template("editpost.html", jobinfo=jobInfo)
    else:
        # acquire positioninfo after the page is changed
        jobInfo.pos_name = request.values.get('pos_name')
        jobInfo.pos_desc = request.values.get('pos_desc')

        jobInfo.employment_type = request.values.get('employment_type')
        jobInfo.salary = request.values.get('salary')
        jobInfo.salary_type = request.values.get('salary_type')

        jobInfo.location = request.values.get('location')
        jobInfo.responsibility = request.values.get('responsibility')

        experience = request.values.get('experience')
        jobInfo.experience = experience
        if experience == '1':
            jobInfo.exp_dura = request.values.get('exp_dura')
            jobInfo.exp_type = request.values.get('exp_type')
            jobInfo.exp_des = request.values.get('exp_des')
        else:
            jobInfo.exp_dura = ''
            jobInfo.exp_type = ''
            jobInfo.exp_des = ''

        qualification = request.values.get('qualification')
        jobInfo.qualification = qualification
        if qualification == '1':
            jobInfo.req_qual = request.values.get('req_qual')
            jobInfo.qual_des = request.values.get('qual_des')
        else:
            jobInfo.req_qual = ''
            jobInfo.qual_des = ''

        jobInfo.recruiting_nb = request.values.get('recruiting_nb')
        jobInfo.closing_date = request.values.get('closing_date')

        db.session.commit()
        return json.dumps({"state": "success"})

####################################
##### company view resumes
# the default interface display resume by the oder of order_id
@app.route('/resumestable/<path:jobtype>')
def resumestable(jobtype):
    comp = g.user
    # If no job position is selected in the front end, the default position type is' All ',
    # job_ position is a list
    if jobtype == 'All':
        all_jobpos = job_position.query.filter(job_position.comp_id == comp.id).all()
        pos_id = [pos.id for pos in all_jobpos]
        all_resumes = resume.query.filter(resume.jobpos_id.in_(pos_id)).order_by(resume.order_id).all()
    # Select a job position from the jobtype and the job_ position is a specific value
    else:
        # Information about the position in the company
        print(jobtype)
        curr_jobpos = job_position.query.filter(job_position.comp_id == comp.id,job_position.pos_name == jobtype).first()
        print(curr_jobpos)
        # all_resumes: All resume of the position in the company
        all_resumes = resume.query.filter(resume.jobpos_id == curr_jobpos.id).order_by(resume.order_id).all()
        print(all_resumes)
    resumeinfos = {}
    for res in all_resumes:
        if res.status == '1:submitted':
            resumeinfos[res.id] = {"real_name": res.user.real_name, \
                                "pos_name": res.job_position.pos_name, \
                                "status": res.status
                                }
    totalnum = len(resumeinfos)
    return render_template("resumestable.html", resumeinfos=resumeinfos, jobtype=jobtype, totalnum=totalnum)


################################
### the resume details page
@app.route('/resumeinfo/<resume_id>')
def resumeinfo(resume_id):
    res = resume.query.filter(resume.id ==resume_id).first()
    res_exp = experience.query.filter(experience.resume_id ==resume_id).first()
    res_qual = qualification.query.filter(qualification.resume_id == resume_id).first()
    resumeinfo = {
        "real_name": res.user.real_name,
        'icon': res.user.icon,
        "company_name": res.job_position.company.real_name,
        "pos_name": res.job_position.pos_name,
        "phone_num": res.phone_num,
        "location": res.user.location,
        "experience": res.experience,
        "qualification": res.qualification,
        'expected_salary': res.expected_salary if res.expected_salary!='- Renumeration range(dollars per month)-' else 0,
        'skill': res.skill,
        'ps': res.ps,
        'attachment': res.attachment
    }
    if res.experience == '1':
        resumeinfo["start_date"] =  res_exp.start_date
        resumeinfo["end_date"] = res_exp.end_date
        resumeinfo["exp_type"] = res_exp.type
        resumeinfo["exp_desc"] = res_exp.desc

    if res.qualification == '1':
        resumeinfo["qual_date"] = res_qual.date
        resumeinfo["qual_type"] = res_qual.type
        resumeinfo["qual_desc"] = res_qual.desc

    return render_template("resumeinfo.html", info=resumeinfo)

###############################
### Intelligent resume ranking, 
##  according to the experience and qualification of each resume to calculate resume.score
##  AI function
@app.route('/sorted_resume/<path:jobtype>')
def sorted_resume(jobtype):
    comp = g.user
    # If no job position is selected in the front end, the default position type is' All '
    if jobtype == 'All':
        all_jobpos = job_position.query.filter(job_position.comp_id == comp.id).all()
        pos_id = [pos.id for pos in all_jobpos]
        all_resumes = resume.query.filter(resume.jobpos_id.in_(pos_id)).all()

    # Select a job position from the jobtype
    else:
        # Information about the position in the company
        curr_jobpos = job_position.query.filter(job_position.comp_id == comp.id,job_position.pos_name == jobtype).first()
        # all_ resumes: all resumes of the job position in the company
        all_resumes = resume.query.filter(resume.jobpos_id == curr_jobpos.id).all()

    for res in all_resumes:
        score = 0
        # Calculate a score for each resume and sort it according to this score
        # Does the job seeker have experience?
        seeker_experience = res.experience
        if seeker_experience == '1':
            score += 1
            # Add score according to the type of experiences
            res_exp = experience.query.filter(experience.resume_id == res.id).first()
            if res_exp.type == 'Working experience':
                score += 2
            elif res_exp.type == 'Internship':
                score += 1
            # Add score according to the duration of experiences
            start = res_exp.start_date.split('-')
            end = res_exp.end_date.split('-')
            end_n = int(end[0])*10000+int(end[1])*100+int(end[2])
            start_n = int(start[0])*10000+int(start[1])*100+int(start[2])
            dura = (end_n - start_n)*0.0002 #2 points for one year's experience
            score += dura

        # Does the job seeker have qualification
        seeker_qualification = res.qualification
        if seeker_qualification == '1':
            score += 1
            #Add score according to the type of qualifications
            res_qual = qualification.query.filter(qualification.resume_id == res.id).first()
            if res_qual.type =='Certification':
                score += 2
            elif res_qual.type == 'Award':
                score += 1
        results = resume.query.filter(resume.id == res.id).first()
        results.score = score
        db.session.commit()

    if jobtype == 'All':
        sorted_score_resumes = resume.query.filter(resume.jobpos_id.in_(pos_id)).order_by(-resume.score).all()
    else:
        sorted_score_resumes = resume.query.filter(resume.jobpos_id == curr_jobpos.id).order_by(-resume.score).all()
    resumeinfos = {}
    # sorted_ Resumes is sorted by score, then the order_ id will changed after saving
    for res in sorted_score_resumes:
        if res.status == '1:submitted':
            resumeinfos[res.id] = {"real_name": res.user.real_name, \
                                   "pos_name": res.job_position.pos_name, \
                                   "status": res.status
                                   }
    totalnum = len(resumeinfos)
    return render_template("resumestable.html", resumeinfos=resumeinfos, jobtype=jobtype, totalnum=totalnum)

################################
### Save changed resume order
@app.route('/saveresumes/<path:jobtype>', methods=["POST"])
def saveresumes(jobtype):
    id  = request.values.getlist('id')
    for i in range(len(id)):
        res = resume.query.filter(resume.id == id[i]).first()
        res.order_id = int(i)
        db.session.commit()

    return json.dumps({"state": "success"})


###############################################
#### company invite candidates
@app.route('/invite/<path:jobtype>', methods=["POST"])
def invite(jobtype):
    num = request.values.get("num")
    print('hi',jobtype)
    # According to jobtype, get the top x resumes
    if jobtype == 'All':
        all_jobpos = job_position.query.filter(job_position.comp_id == g.user.id).all()
        pos_id = [pos.id for pos in all_jobpos]
        top_X_resumes = resume.query.filter(resume.jobpos_id.in_(pos_id)).order_by(resume.order_id).limit(num)

    # Select a job position from the jobtype
    else:
        # Information about the position in the company
        print('this', jobtype)
        curr_jobpos = job_position.query.filter(job_position.comp_id == g.user.id,job_position.pos_name == jobtype).first()
        print(curr_jobpos)
        top_X_resumes = resume.query.filter(resume.jobpos_id == curr_jobpos.id, resume.status=='1:submitted').order_by(resume.order_id).limit(num)
        print(top_X_resumes)
    # Change the status of the first X resume selected to "2-1: audition":
    # the employer waits for the job seekers to accept or reject the interview
    for res in top_X_resumes:
        res.status = "2-1:audition"
        db.session.commit()

    return json.dumps({"state": "success"})


#########################################################
# Operation of company on offer
# offerstable：Show all the candidates invited for interview
# rejectoffer：Candidates who do not meet the requirements will be refused
# offer：Candidates who meet the requirements will be sended an offer
# clearoffer：Companies filter resumes,only the candidates who accepted the invitation were left
#########################################################
##################################
### Show all the candidates invited for interview
@app.route('/offerstable/<path:job_pos>')
def offerstable(job_pos):
    print(job_pos)
    res_status = ["2-1:audition","2-2:refused","3-1:accept","3-2:refused","4-1:offer","4-2:refused"]
    # All resumes received by the company
    if job_pos == 'All':
        all_jobpos = job_position.query.filter(job_position.comp_id == g.user.id).all()
        pos_id = [pos.id for pos in all_jobpos]
        invited_rs = resume.query.filter(resume.jobpos_id.in_(pos_id), resume.status.in_(res_status)).all()
    # All resumes received by the company for this job position
    else:
        curr_jobpos = job_position.query.filter(job_position.comp_id == g.user.id, \
                                                job_position.pos_name == job_pos).first()
        invited_rs = resume.query.filter(resume.jobpos_id == curr_jobpos.id, resume.status.in_(res_status)).all()

    offerinfos = {}
    for res in invited_rs:
        offerinfos[res.id] = {"real_name": res.user.real_name, \
                         "pos_name": res.job_position.pos_name, \
                         "status": res.status
                         }

    return render_template("offerstable.html", offerinfos=offerinfos, job_position=job_pos)


##################################
### company reject offe，4-2:refused
@app.route('/rejectoffer/<resume_id>',methods=["POST"])
def rejectoffer(resume_id):
    curr_res = resume.query.filter(resume.id == resume_id).first()
    curr_res.status = '4-2:refused'
    db.session.commit()
    return json.dumps({"state": "success"})


##################################
### company send offer
@app.route('/offer/<resume_id>/<content>', methods=["POST", "GET"])
def offer(resume_id, content):
    if request.method == "GET":
        # Through resume_ id gets the current resume
        curr_res = resume.query.filter(resume.id == resume_id).first()

        company_name = curr_res.job_position.company.real_name
        jobseeker_name = curr_res.user.real_name
        return render_template("offer.html", resume_id=resume_id, content=content,\
                               company_name=company_name, jobseeker_name=jobseeker_name)
    else:
        # company send offer, the status of resume is changed
        curr_res = resume.query.filter(resume.id == resume_id).first()
        curr_res.status = '4-1:offer'
        if content == "templete":
            # save the details of each offer
            pos_name = request.values.get('pos_name')
            department = request.values.get('department')
            working_date = request.values.get('working_date')
            salary = request.values.get('salary')
            salary_type = request.values.get('salary_type')
            benefit_date = request.values.get('benefit_date')
            HR_name = request.values.get('HR_name')
            classes = "templete"

            new_offer = offer_tb(res_id=resume_id, pos_name=pos_name, department=department, \
                              working_date=working_date, salary=salary, salary_type=salary_type, \
                              benefit_date=benefit_date, HR_name=HR_name, classes=classes)

            db.session.add(new_offer)
            db.session.commit()

            return json.dumps({"state": "success"})

        else:
            HR_name = request.values.get('HR_name')
            customized_cont = request.values.get('offer')
            classes = "customize"
            # ('offer', ' xxxxx'), ('HR_name', '')
            new_offer = offer_tb(res_id=resume_id, HR_name=HR_name, customized_cont=customized_cont, classes=classes)
            db.session.add(new_offer)
            db.session.commit()

            return json.dumps({"state": "success"})

##################################
### Companies filter resumes,only the candidates who accepted the invitation were left
@app.route('/clearoffer/<job_pos>')
def clearoffer(job_pos):
    # Only resume with status 3-1 is left in the database, and then reload offertable
    # All resumes received by the company
    if job_pos == 'All':
        all_jobpos = job_position.query.filter(job_position.comp_id == g.user.id).all()
        pos_id = [pos.id for pos in all_jobpos]
        invited_rs = resume.query.filter(resume.jobpos_id.in_(pos_id), resume.status == "3-1:accept" ).all()
    # All resumes received by the company for this position
    else:
        curr_jobpos = job_position.query.filter(job_position.comp_id == g.user.id, job_position.pos_name == job_pos).first()
        invited_rs = resume.query.filter(resume.jobpos_id == curr_jobpos.id, resume.status == "3-1:accept").all()

    offerinfos = {}
    for res in invited_rs:
        offerinfos[res.id] = {"real_name": res.user.real_name, \
                         "pos_name": res.job_position.pos_name, \
                         "status": res.status
                         }

    return render_template("offerstable.html", offerinfos=offerinfos, job_position=job_pos)


###############################################
# job seekers handle offer and interview invitation
# appliedjobtable: Job seeker view the submitted resume
# accept_reject：Job seeker chooses to accept or reject the interview invitation
# viewoffer：Job seeker view received offers
###############################################

######################################
##### jobseeker offer
@app.route('/appliedjobtable')
def appliedjobtable():
    applied_resume = resume.query.filter(resume.user_id == g.user.id).all()
    appliedinfos = {}
    i = 0
    for res in applied_resume:
        i += 1
        appliedinfos[res.id] = {"company_name": res.job_position.company.real_name, \
                         "pos_id": res.job_position.id, \
                         "pos_name": res.job_position.pos_name, \
                         "status": res.status
                         }
    return render_template("appliedjobtable.html", appliedinfos=appliedinfos)


##################################
### job seeker accept/reject the interview invitation
@app.route('/accept_reject/<resume_id>/<action>', methods=["POST", "GET"])
def accept_reject(resume_id, action):
    curr_res = resume.query.filter(resume.id == resume_id).first()
    if action == 'accept':
        curr_res.status = '3-1:accept'
        db.session.commit()
    elif action == 'refuse':
        curr_res.status = '3-2:refused'
        db.session.commit()
    return json.dumps({"state": "success"})


########################
##  view offer
@app.route('/viewoffer/<resume_id>', methods=["POST", "GET"])
def viewoffer(resume_id):
    curr_offer = offer_tb.query.filter(offer_tb.res_id == resume_id).first()
    curr_res = resume.query.filter(resume.id == resume_id).first()
    offerinfos = {}
    content = curr_offer.classes
    print('content',content)
    if content == 'templete':
        offerinfos = {
            "jobseeker_name": curr_res.user.real_name,
            "create_time": curr_offer.create_time,
            'company_name': curr_res.job_position.company.real_name,

            "pos_name": curr_offer.pos_name,
            "department": curr_offer.department,
            "working_date": curr_offer.working_date,
            "salary": curr_offer.salary,
            "salary_type": curr_offer.salary_type,

            "benefit_date": curr_offer.benefit_date,
            "HR_name": curr_offer.HR_name
        }
        return render_template("viewoffer.html", offer=offerinfos, content=content)
    else:
        offerinfos = {
            "jobseeker_name": curr_res.user.real_name,
            "create_time": curr_offer.create_time,
            "offer": curr_offer.customized_cont,
            "HR_name": curr_offer.HR_name
        }
        return render_template("viewoffer.html", offer=offerinfos, content=content)



@app.route('/seekerJobInfo')
def seekerJobInfo():
    return render_template("seekerJobInfo.html")


##################################
@app.route('/footer')
def footer():
    return render_template("footer.html")
##################################
@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")

##################################
# contact us function
@app.route('/contactus')
def contactus():
    return render_template("contactus.html")

@app.route('/send_email', methods=["POST"])
def send_email():
    webbrowser.open_new('mailto:?to=oyishyikami@gmail.com'\
                                '&subject=[User message][From-HD-to-FL][COMP9900]'\
                                '&body=To help us to distinct the message from other message, we recommend you to not change the subject.')
    return '0'

#########################################################
# search function(
#########################################################

@app.route('/search', methods=["POST"])
def search():

    global joblist
    joblist = {}

    search_parameter = request.values
    print(search_parameter)

    # basic parameter
    keyword = search_parameter.get('job') # keyword
    employment_type = search_parameter.get('types') # employment_type:[full-time，part-time，internship]
    min_salary = search_parameter.get('min_salary')
    max_salary = search_parameter.get('max_salary')
    salary_type = search_parameter.get('salary_types')

    # advanced parameter
    sorted_parameter = search_parameter.get('sorted_parameter')
                                        # salary  sorted by salary
                                        # time sorted by deadline
                                        # hot sorted by submitted num of the resume
    sorted_direction = search_parameter.get('sorted_direction')
                                        # '1' 
                                        # '0'

    work_experience = search_parameter.get('work_experience')
    
    # Intelligient search
    if_ai = 'if_ai' in search_parameter
    
    query = [] #list that store filter query expression, used by *query

    if employment_type != '- All employment types -':
        query.append(job_position.employment_type == employment_type)
    if work_experience != '- Experience duration -' and work_experience != None:
        query.append(job_position.exp_dura == work_experience)
    if salary_type != '- Salary types -' and min_salary != '' and max_salary != '':
        def transfer_salary_per_year(salary, salary_type):
            if salary_type == '1/24':
                return salary * 7 * 240
            elif salary_type == '1':
                return salary * 240
            elif salary_type == '7':
                return salary * 48
            elif salary_type == '30':
                return salary * 12
            else:
                return salary
        new_min = transfer_salary_per_year(int(min_salary), salary_type)
        new_max = transfer_salary_per_year(int(max_salary), salary_type)
        query.append(job_position.transfer_salary > new_min)
        query.append(job_position.transfer_salary < new_max)
    def query_sort_function(cls, sorted_parameter, sorted_direction):
        if sorted_parameter == 'salary':
            if sorted_direction == '1':
                res = -cls.transfer_salary
            else:
                res = cls.transfer_salary
        elif sorted_parameter == 'time':
            if sorted_direction == '1':
                res = func.concat(func.substr(cls.closing_date, 7, 10), func.substr(cls.closing_date, 4, 5), func.substr(cls.closing_date, 1, 2))
            else:
                res = func.concat(func.substr(cls.closing_date, 7, 10), func.substr(cls.closing_date, 4, 5), func.substr(cls.closing_date, 1, 2)).desc()
        elif sorted_parameter == 'hot':
            if sorted_direction == '1':
                res = -cls.submitted_nb
            else:
                res = cls.submitted_nb
        else:
            res = None
        return res

    #query expression of order_by
    query_sort = query_sort_function(job_position, sorted_parameter, sorted_direction)

    if not if_ai:
        query.append(job_position.pos_name.ilike(f'%{keyword}%'))
        data = job_position.query.filter(*query).order_by(query_sort).all()
    else:
        #take 1s for each 100 job positions
        data = job_position.query.filter(*query).order_by(query_sort).all()
        data = [i for i in data if (keyword.lower() in i.pos_name.lower()) \
                                                or ( nlp(keyword).similarity( nlp(i.pos_name) ) > 0.7 )]
    i = 0
    while(True):
        try:
            curr_data = data[i]
            joblist[str(i)] = {"id":curr_data.id, \
                    "pos_name":curr_data.pos_name,\
                    "company_name":curr_data.company.real_name,\
                    "employment_type":curr_data.employment_type,\
                    "location":curr_data.location,\
                    "closing_date":curr_data.closing_date,\
                    "pos_desc":curr_data.pos_desc,
                    'salary': curr_data.transfer_salary
                    }
            i+=1
        except IndexError:
            break
    return json.dumps("Submit successfully")

@app.route('/searchresult/<int:page_num>')
def searchresult(page_num):
    def dict_slice(adict, start, end):
        keys = list(adict.keys())
        dict_slice = {}
        for k in keys[start:end]:
            dict_slice[k] = adict[k]
        return dict_slice
    global joblist
    page = {
        "current_page":page_num,
        "prev_num":page_num-1,
        "next_num":page_num+1,
        "pagelist":[page_num,page_num +1, page_num+2]
    }

    return render_template("searchresult.html", data=dict_slice(joblist, (page_num-1)*5, page_num*5), page=page)


@app.route('/search_employer', methods=["POST"])
def search_employer():

    global joblist
    joblist = {}

    search_parameter = request.values
    print(search_parameter)

    position_keyword = search_parameter.get('position_keyword') # keyword of job position name
    qualification_keyword = search_parameter.get('qualification_keyword') # keyword of qualification desc
    exp_type = search_parameter.get('exp_type')
    exp_duration = search_parameter.get('exp_dura')
    qual_need = search_parameter.get('qual_need')
    
    query = []

    query.append(job_request.jobname.ilike(f'%{position_keyword}%'))
    query.append(job_request.qual_desc.ilike(f'%{qualification_keyword}%'))

    if exp_duration != '- Experience durations -':
        query.append(job_request.exp_duration == exp_duration)

    if exp_type != '- Experience type -':
        query.append(job_request.exp_type == exp_type)

    if qual_need != '- Qualification Need -' and qual_need != '0':
        query.append(job_request.qual_need == qual_need)

    data = job_request.query.filter(*query).order_by(job_request.create_time).all()
    print(data)

    i = 0
    while(True):
        try:
            curr_data = data[i]
            joblist[str(i)] = {
                "request_id": curr_data.id,
                "real_name": curr_data.user.real_name,
                'icon': curr_data.user.icon,
                "pos_name": curr_data.jobname,
                "desc": curr_data.desc
            }
            i+=1
        except IndexError:
            break

    return json.dumps("Submit successfully")

@app.route('/requestresult/<int:page_num>')
def request_result(page_num):

    def dict_slice(adict, start, end):
        keys = list(adict.keys())
        dict_slice = {}
        for k in keys[start:end]:
            dict_slice[k] = adict[k]
        return dict_slice
        
    # change name
    global joblist
    requestlist = joblist
    requestlist = dict_slice(requestlist, (page_num-1)*5, page_num*5)
    print(requestlist)

    page = {
        "current_page": page_num,
        "prev_num": page_num - 1,
        "next_num": page_num + 1,
        "pagelist": [page_num, page_num + 1, page_num + 2]
    }
    return render_template("jobrequestresult.html", data=requestlist, page=page)


#########################################################
# Q&A
#########################################################
@app.route('/q_a')
def Q_A():
    return render_template("Q&A.html")


#########################################################
# hook function
#########################################################

@app.before_request
def my_before_request():
    user_id = session.get('user_id')
    if user_id:
        curr_user = user.query.filter(user.id == user_id).first()
        if curr_user:
            g.user = curr_user

@app.context_processor
def my_context_processor():
    if hasattr(g, 'user'):
        return {'curr_user': g.user}
    return {}


if __name__ == '__main__':
    app.run()