from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(100), unique = True, nullable=False)
	password = db.Column(db.String(100), nullable=False)
	role = db.Column(db.String(10), nullable=False)
	department = db.Column(db.String(50), nullable=True)
	phone = db.Column(db.String(15), nullable=True)
	status = db.Column(db.String(20), default='Active')
	
class Course(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	course_code = db.Column(db.String(50), nullable=False, unique=True)
	course_name = db.Column(db.String(50), nullable=False)
	description = db.Column(db.String(200))
	status = db.Column(db.String(20), default='active')
	
	exams = db.relationship('Examination', backref='course', cascade='all, delete-orphan')
	
class Examination(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
	examiner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
	exam_name = db.Column(db.String(50), nullable=False)
	exam_type = db.Column(db.String(50), nullable=False)
	max_marks = db.Column(db.Integer, nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	slot_creation_start_date = db.Column(db.String(10))
	slot_creation_end_date = db.Column(db.String(10))
	slot_booking_start_date = db.Column(db.String(10))
	slot_booking_end_date = db.Column(db.String(10))
	status = db.Column(db.String(20))
	
	examiner = db.relationship('User', foreign_keys=[examiner_id])
	rubrics = db.relationship('Rubrics', backref='exam', cascade='all, delete-orphan')
	slots = db.relationship('Slots', backref='exam', cascade='all, delete-orphan')
	
class Rubrics(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	exam_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
	criterion_name = db.Column(db.String(50), nullable=False)
	max_marks = db.Column(db.Integer, nullable=False)
	weightage = db.Column(db.Integer, nullable=False)
	description = db.Column(db.String(100))
	
class Slots(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	exam_id = db.Column(db.Integer, db.ForeignKey('examination.id'), nullable=False)
	examiner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	date = db.Column(db.String(15), nullable=False)
	start_time = db.Column(db.String(15), nullable=False)
	end_time = db.Column(db.String(15), nullable=False)
	max_capacity = db.Column(db.Integer, nullable=False)
	available_seats = db.Column(db.Integer, nullable=False)
	status = db.Column(db.String(10), default='Available')
	
	examiner = db.relationship('User', foreign_keys=[examiner_id])
	bookings = db.relationship('Booking', backref='slot', cascade='all, delete-orphan')
	
class Booking(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	slot_id = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
	booking_date = db.Column(db.String(15), nullable=False)
	status = db.Column(db.String(10), default='Booked')
	marks = db.Column(db.Integer, nullable=True)
	remarks = db.Column(db.String(100), nullable=True)
	
	student = db.relationship('User', foreign_keys=[student_id])