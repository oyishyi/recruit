from flask_sqlalchemy import SQLAlchemy
from exts import db
from datetime import datetime

# favorite jobs of users
user_favorite = db.Table(
    'user_favorite',
    db.Column('user_id', db.ForeignKey('user.id'), primary_key=True),
    db.Column('job_position_id', db.ForeignKey('job_position.id'), primary_key=True)
)

# favorite job requests of companies
company_favorite = db.Table(
    'company_favorite',
    db.Column('user_id', db.ForeignKey('user.id'), primary_key=True),
    db.Column('job_request_id', db.ForeignKey('job_request.id'), primary_key=True)
)


class user(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(320), nullable=False)  # 256(domain)+64(localname)(varchar(320))
    user_type = db.Column(db.String(10), nullable=False)  # 'Job Seeker'or 'Employer'

    # user info
    password = db.Column(db.String(20), nullable=False)  # just a convention
    real_name = db.Column(db.String(50))
    icon = db.Column(db.Text)
    location = db.Column(db.String(100))
    desc = db.Column(db.Text)  # depends on identity

    # employee info
    birth_day = db.Column(db.String(10))
    favorite_jobs = db.relationship('job_position', secondary=user_favorite, backref=db.backref('favorite_users'))

    # employer info
    favorite_requests = db.relationship('job_request', secondary=company_favorite, backref=db.backref('favorite_users'))


# graduate school
class degree(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    degree = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(50), nullable=False)
    user = db.relationship('user', backref=db.backref('degrees'))


# chat record
class communication_record(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime, default=datetime.now)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    content = db.Column(db.String(100), nullable=False)


class job_request(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    create_time = db.Column(db.DateTime, default=datetime.now)  # used by jobList sort algorithm

    phone_num = db.Column(db.String(11), nullable=False)
    jobname = db.Column(db.String(50), nullable=False)

    exp_need = db.Column(db.String(2))
    exp_duration = db.Column(db.String(25))
    exp_type = db.Column(db.String(25))
    exp_desc = db.Column(db.String(500))

    qual_need = db.Column(db.String(2))
    qual_date = db.Column(db.String(30))
    qual_type = db.Column(db.String(30))
    qual_desc = db.Column(db.String(500))

    desc = db.Column(db.Text, nullable=False)

    user = db.relationship('user', backref=db.backref('job_requests'))


class resume(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # resume <-> job seekers
    jobpos_id = db.Column(db.Integer, db.ForeignKey('job_position.id'),
                          primary_key=True)  # resume <-> employers(job position)

    phone_num = db.Column(db.String(11), nullable=False)
    experience = db.Column(db.String(1), nullable=False)
    qualification = db.Column(db.String(1), nullable=False)

    expected_salary = db.Column(db.String(60), nullable=False)
    skill = db.Column(db.String(500))
    attachment = db.Column(db.Text)
    ps = db.Column(db.Text)

    user = db.relationship('user', backref=db.backref('resumes'))
    job_position = db.relationship('job_position', backref=db.backref('resumes'))

    status = db.Column(db.String(50), default='1:submitted')
    score = db.Column(db.Integer, default=0)
    order_id = db.Column(db.Integer, default=9999)


class experience(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'))

    start_date = db.Column(db.String(10))
    end_date = db.Column(db.String(10))
    type = db.Column(db.String(30), nullable=False)
    desc = db.Column(db.Text, nullable=False)


    resume = db.relationship('resume', backref=db.backref('experiences'))


class qualification(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'))

    date = db.Column(db.String(10))
    type = db.Column(db.String(30), nullable=False)
    desc = db.Column(db.Text, nullable=False)

    resume = db.relationship('resume', backref=db.backref('qualifications'))

from sqlalchemy.ext.hybrid import hybrid_property
class job_position(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    create_time = db.Column(db.DateTime, default=datetime.now)  # used by jobList sort algorithm
    comp_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    pos_name = db.Column(db.String(80), nullable=False)
    pos_desc = db.Column(db.Text, nullable=False)

    # employment_type = db.Column(db.Enum('Full-time', 'Part-time', 'Internship'), default='full-time')
    employment_type = db.Column(db.String(20))
    salary = db.Column(db.DECIMAL(10, 2), nullable=False)
    salary_type = db.Column(db.String(20))

    location = db.Column(db.String(100))
    responsibility = db.Column(db.Text, nullable=False)

    experience = db.Column(db.String(2))
    exp_dura = db.Column(db.String(50))
    exp_type = db.Column(db.String(20))
    exp_des = db.Column(db.Text)

    qualification = db.Column(db.String(2))
    req_qual = db.Column(db.String(20))
    qual_des = db.Column(db.Text)

    recruiting_nb = db.Column(db.Integer)
    closing_date = db.Column(db.String(10), default='OPEN')

    submitted_nb = db.Column(db.Integer, default = 0)
    company = db.relationship('user', backref=db.backref('job_positions'))

    @hybrid_property
    def transfer_salary(self): # change all the salary type to 'per year'
        if self.salary_type == 'per hour':
            return self.salary * 7 * 240
        elif self.salary_type == 'per day':
            return self.salary * 240
        elif self.salary_type == 'per week':
            return self.salary * 48
        elif self.salary_type == 'per month':
            return self.salary * 12
        else:
            return self.salary
    @transfer_salary.expression
    def transfer_salary(cls):
        return db.case([
            (cls.salary_type == 'per hour', cls.salary * 7 * 240),
            (cls.salary_type == 'per day', cls.salary * 240),
            (cls.salary_type == 'per week', cls.salary * 48),
            (cls.salary_type == 'per month', cls.salary * 12)
        ], else_= cls.salary)


class question(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.now)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('user', backref=db.backref('questions'))


class answer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.now)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    question = db.relationship('question', backref=db.backref('answer'))
    # question = db.relationship('question', backref=db.backref('answer'), order_by=id.desc())
    author = db.relationship('user', backref=db.backref('answers'))


class comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(20))
    content = db.Column(db.String(500))

    create_time = db.Column(db.DateTime, default=datetime.now)


class ContactUs(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(320), nullable=False)
    information = db.Column(db.String(1000), nullable=False)

class offer_tb(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    res_id = db.Column(db.Integer, db.ForeignKey('resume.id'))
    create_time = db.Column(db.DateTime, default=datetime.now)

    classes = db.Column(db.String(20))
    # templete
    pos_name = db.Column(db.String(50))
    department = db.Column(db.String(50))
    working_date = db.Column(db.String(10))
    salary = db.Column(db.DECIMAL(10, 2))
    salary_type = db.Column(db.String(20))
    benefit_date = db.Column(db.String(10))
    HR_name = db.Column(db.String(30))
    # user defined
    customized_cont = db.Column(db.String(1000))
