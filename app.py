from flask import Flask, render_template, request, url_for, redirect, session, flash
from models import db, User, Course, Examination, Rubrics, Slots, Booking
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

db.init_app(app)

with app.app_context():
	db.create_all()
	
	if not User.query.filter_by(role="admin").first():
		admin = User(name='Admin', email="admin@examportal.com", password="admin@123", role='admin', phone="0123456789", department="web admin")
		db.session.add(admin)
		db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
	return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
	role = session.get('role')
	if role == 'admin':
		return redirect(url_for('admin_dashboard'))
	elif role == "examiner":
		return redirect(url_for('examiner_dashboard'))
	elif role == "student":
		return redirect(url_for('student_dashboard'))
	return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
	if session.get('role') != 'admin':
		flash('Unauthorized access', 'danger')
		return redirect(url_for('login'))
	total_courses = Course.query.count()
	total_exams = Examination.query.count()
	total_examiners = User.query.filter_by(role='examiner').count()
	total_students = User.query.filter_by(role='student').count()
	total_slots = Slots.query.count()
	total_bookings = Booking.query.count()
	courses = Course.query.all()
	examinations = Examination.query.all()
	examiners = User.query.filter_by(role='examiner').all()

	search = request.args.get('q', '').strip()

	if search.isdigit():
		examinations = Examination.query.filter_by(id=int(search)).all()
	elif search:
		examinations = Examination.query.filter(Examination.exam_name.contains(search)).all()
	else:
		examinations = Examination.query.all()

	return render_template('admin_dashboard.html',total_courses=total_courses,
	total_exams=total_exams,total_examiners=total_examiners,total_students=total_students,
	total_slots=total_slots,total_bookings=total_bookings,
	examinations=examinations,courses=courses,examiners=examiners,search=search)


@app.route('/admin/course/add', methods=['GET','POST'])
def add_course():
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	if request.method == 'POST':
		code = request.form.get('course_code')
		name = request.form.get('course_name')
		description = request.form.get('description')
		status = request.form.get('status', 'active')
	
		if Course.query.filter_by(course_code=code).first():
			flash('Course code already exists', 'danger')
		else:	
			course = Course(course_code=code,course_name=name,description=description,status=status)
			db.session.add(course)
			db.session.commit()
			
			flash('Course added successfully.', 'success')
			return redirect(url_for('admin_dashboard'))
	return render_template('course.html')

@app.route('/admin/course/edit/<int:course_id>', methods=['GET','POST'])
def edit_course(course_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))

	course = Course.query.get_or_404(course_id)
	if request.method=="POST":
		code = request.form.get('course_code')
		name = request.form.get('course_name')
		description = request.form.get('description')
		status = request.form.get('status')

		if Course.query.filter(Course.course_code == code, Course.id != course_id).first():
			flash('Course code already exists.', "danger")
		else:
			course.course_code = code
			course.course_name = name
			course.description = description
			course.status = status

			db.session.commit()
			flash('Course updated successfully.', 'success')
			return redirect(url_for('admin_dashboard'))
		return redirect(url_for('edit_course', course_id=course_id))
	return render_template('edit_course.html', course=course)

@app.route('/admin/course/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	course=Course.query.get_or_404(course_id)
	db.session.delete(course)
	db.session.commit()
	flash('Course deleted successfully.', 'success')
	return redirect(url_for('admin_dashboard'))
	
@app.route('/admin/examination/add', methods=["GET", "POST"])
def add_examination():
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	courses= Course.query.filter_by(status="active").all()
	examiners = User.query.filter_by(role='examiner').all()
	
	if request.method == 'POST':
		exam = Examination(course_id=request.form.get('course_id'),examiner_id=request.form.get('examiner_id') or None, exam_name=request.form.get('exam_name'),
		exam_type=request.form.get('exam_type'),duration=request.form.get('duration'),max_marks=request.form.get('max_marks'),
		slot_creation_start_date=request.form.get('slot_creation_start_date'),slot_creation_end_date=request.form.get('slot_creation_end_date'),
		slot_booking_start_date=request.form.get('slot_booking_start_date'),slot_booking_end_date=request.form.get('slot_booking_end_date'),status='Slot Creation')
		
		db.session.add(exam)
		db.session.commit()
		
		flash('Examination created successfully.', 'success')
		return redirect(url_for('admin_dashboard'))
	return render_template('examination.html', courses=courses,examiners=examiners)

@app.route('/admin/examination/edit/<int:exam_id>', methods=["GET", 'POST'])
def edit_examination(exam_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	exam = Examination.query.get_or_404(exam_id)
	courses = Course.query.all()
	examiners = User.query.filter_by(role='examiner').all()
	
	if request.method == "POST":
		exam.course_id = request.form.get('course_id')
		exam.examiner_id = request.form.get('examiner_id') or None
		exam.exam_name = request.form.get('exam_name')
		exam.exam_type = request.form.get('exam_type')
		exam.duration = request.form.get('duration')
		exam.max_marks = request.form.get('max_marks')
		exam.slot_creation_start_date = request.form.get('slot_creation_start_date')
		exam.slot_creation_end_date = request.form.get('slot_creation_end_date')
		exam.slot_booking_start_date = request.form.get('slot_booking_start_date')
		exam.slot_booking_end_date = request.form.get('slot_booking_end_date')
		exam.status = request.form.get('status')
		db.session.commit()
		return redirect(url_for('admin_dashboard'))
	return render_template('edit_examination.html', exam=exam,courses=courses,examiners=examiners)


@app.route('/admin/examination/delete/<int:exam_id>', methods=['POST'])
def delete_examination(exam_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	exam = Examination.query.get_or_404(exam_id)
	db.session.delete(exam)
	db.session.commit()
	return redirect(url_for('admin_dashboard'))


@app.route('/admin/examination/<int:exam_id>/rubrics')
def view_rubrics(exam_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	exam = Examination.query.get_or_404(exam_id)
	rubrics = Rubrics.query.filter_by(exam_id=exam.id).all()
	return render_template('view_rubrics.html', exam=exam, rubrics=rubrics)

@app.route('/admin/examination/<int:exam_id>/rubrics/add', methods=["GET","POST"])
def add_rubrics(exam_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	exam = Examination.query.get_or_404(exam_id)
	if request.method == 'POST':
		exam_id = exam.id
		criterion_name = request.form.get('criterion_name')
		max_marks = request.form.get('max_marks')
		weightage = request.form.get('weightage')
		description = request.form.get('description')
		
		rubric = Rubrics(exam_id=exam_id,criterion_name=criterion_name,max_marks=max_marks,
		weightage=weightage,description=description)
		
		db.session.add(rubric)
		db.session.commit()
		
		flash('Rubric Added Successfully.', 'success')
		return redirect(url_for('view_rubrics', exam_id=exam.id))
	return render_template('add_rubric.html', exam=exam)

@app.route('/admin/rubric/edit/<int:rubric_id>', methods=["GET","POST"])
def edit_rubric(rubric_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	rubric = Rubrics.query.get_or_404(rubric_id)
	
	if request.method == "POST":
		rubric.criterion_name = request.form.get('criterion_name')
		rubric.max_marks = request.form.get('max_marks')
		rubric.weightage = request.form.get('weightage')
		rubric.description = request.form.get('description')
		
		db.session.commit()
		flash('Rubric updated Successfully.', 'success')
		return redirect(url_for('view_rubrics',exam_id=rubric.exam_id))
	return render_template('edit_rubric.html',rubric=rubric)

@app.route('/admin/rubric/delete/<int:rubric_id>', methods=['POST'])
def delete_rubric(rubric_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	rubric = Rubrics.query.get_or_404(rubric_id)
	exam_id = rubric.exam_id
	db.session.delete(rubric)
	db.session.commit()
	flash('Rubric Deleted Successfully.', 'success')
	return redirect(url_for('view_rubrics',exam_id=exam_id))
		
@app.route('/admin/examination/<int:exam_id>/students')
def registered_students(exam_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))

	exam = Examination.query.get_or_404(exam_id)
	search = request.args.get('q', '').strip()

	query = Booking.query.join(Slots).join(User, Booking.student_id == User.id).filter(Slots.exam_id == exam.id)

	if search.isdigit():
		query = query.filter(Booking.id == int(search))
	elif search:
		query = query.filter(User.name.contains(search))

	bookings = query.all()
	return render_template('registered_students.html', exam=exam, bookings=bookings, search=search)

@app.route('/admin/booking/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	booking = Booking.query.get_or_404(booking_id)
	exam_id = booking.slot.exam_id
	slot = booking.slot
	
	if booking.status != 'Cancelled':
		booking.status = 'Cancelled'
		slot.available_seats += 1
		if slot.status == 'Full' and slot.available_seats > 0:
			slot.status = 'Available'

	db.session.commit()
	flash('Booking Cancelled Successfully.', 'success')
	return redirect(url_for('registered_students',exam_id=exam_id))

@app.route('/admin/booking/reschedule/<int:booking_id>', methods=['GET',"POST"])
def reschedule_booking(booking_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	booking = Booking.query.get_or_404(booking_id)
	old_slot = booking.slot
	exam = old_slot.exam

	available_slots = Slots.query.filter(Slots.exam_id == exam.id, Slots.id != old_slot.id, Slots.available_seats > 0, Slots.status=='Available').all()
	if request.method == 'POST':
		new_slot_id = request.form.get('new_slot_id', type=int)
		new_slot = Slots.query.get_or_404(new_slot_id)

		if new_slot.available_seats <= 0:
			flash('Selected Slot has no seats available.', 'danger')
			return redirect(url_for('reschedule_booking', booking_id=booking.id))
		old_slot.available_seats += 1
		if old_slot.status == 'Full' and old_slot.available_seats > 0 :
			old_slot.status = "Available"

		new_slot.available_seats -= 1
		if new_slot.available_seats == 0:
			new_slot.status = 'Full'

		booking.slot_id = new_slot.id
		db.session.commit()

		flash(f'Booking #{booking.id} rescheduled for {booking.student.name}.', 'success')
		return redirect(url_for('registered_students', exam_id=exam.id))
	return render_template('reschedule_booking.html',booking=booking,available_slots=available_slots)


@app.route('/admin/students')
def manage_students():
	if session.get('role') != 'admin':
		return redirect(url_for('login'))

	search = request.args.get('q', '').strip()

	if search.isdigit():
		students = User.query.filter_by(role='student', id=int(search)).all()
	elif search:
		students = User.query.filter(User.role == 'student', User.name.contains(search)).all()
	else:
		students = User.query.filter_by(role='student').all()
	return render_template('students.html', students=students, search=search)

@app.route('/admin/student/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	student = User.query.filter_by(id=student_id, role='student').first_or_404()
	
	if request.method == 'POST':
		student.name = request.form.get('name')
		student.email = request.form.get('email')
		student.phone = request.form.get('phone')
		student.department = request.form.get('department')
		db.session.commit()
		
		flash('Student details updated successfully.', 'success')
		return redirect(url_for('manage_students'))
		
	return render_template('edit_student.html', student=student)

@app.route('/admin/student/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	student = User.query.filter_by(id=student_id, role='student').first_or_404()
	
	for booking in Booking.query.filter_by(student_id=student.id).all():
		if booking.status == 'Booked':
			booking.slot.available_seats += 1
			if booking.slot.status == 'Full':
				booking.slot.status = 'Available'
		db.session.delete(booking)
		
	db.session.delete(student)
	db.session.commit()
	flash('Student deleted successfully.', 'success')
	return redirect(url_for('manage_students'))

@app.route('/admin/examiners')
def manage_examiners():
	if session.get('role') != 'admin':
		return redirect(url_for('login'))

	search = request.args.get('q', '').strip()

	if search.isdigit():
		examiners = User.query.filter_by(role='examiner', id=int(search)).all()
	elif search:
		examiners = User.query.filter(User.role == 'examiner', User.name.contains(search)).all()
	else:
		examiners = User.query.filter_by(role='examiner').all()
	return render_template('examiners.html', examiners=examiners, search=search)


@app.route('/admin/examiner/edit/<int:examiner_id>', methods=['GET','POST'])
def edit_examiner(examiner_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	examiner=User.query.filter_by(id=examiner_id,role="examiner").first_or_404()
	
	if request.method== 'POST':
		examiner.name= request.form.get('name')
		examiner.email = request.form.get('email')
		examiner.phone= request.form.get('phone')
		examiner.department= request.form.get('department')
		db.session.commit()
		
		flash('Examiner details updated successfully.', 'success')
		return redirect(url_for('manage_examiners'))
	return render_template('edit_examiner.html',examiner=examiner)

@app.route('/admin/examiner/delete/<int:examiner_id>', methods=["POST"])
def delete_examiner(examiner_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	
	examiner = User.query.get_or_404(examiner_id)
	
	for exam in Examination.query.filter_by(examiner_id=examiner.id).all():
		exam.examiner_id = None

	for slot in Slots.query.filter_by(examiner_id=examiner.id).all():
		db.session.delete(slot)
		
	db.session.delete(examiner)
	db.session.commit()
	flash('Examiner deleted successfully', 'success')
	return redirect(url_for('manage_examiners'))


@app.route('/admin/examination/<int:exam_id>/slots')
def exam_slots(exam_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	exam = Examination.query.get_or_404(exam_id)
	slots = Slots.query.filter_by(exam_id=exam.id).all()
	return render_template('slots.html',exam=exam,slots=slots)

@app.route('/admin/slot/edit/<int:slot_id>', methods=['GET','POST'])
def edit_slots(slot_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
	slot = Slots.query.get_or_404(slot_id)
	examiners = User.query.filter_by(role='examiner').all()
	
	if request.method == 'POST':
		slot.date = request.form.get('date')
		slot.start_time = request.form.get('start_time')
		slot.end_time = request.form.get('end_time')
		slot.examiner_id = request.form.get('examiner_id')
		slot.status = request.form.get('status')
		db.session.commit()
		flash('Slot Updated Successfully.', 'success')
		return redirect(url_for('exam_slots', exam_id = slot.exam_id))

	return render_template('edit_slots.html', slot=slot,examiners=examiners)

@app.route('/admin/examiner/toggle-status/<int:examiner_id>', methods=['POST'])
def examiner_status(examiner_id):
	if session.get('role') != 'admin':
		return redirect(url_for('login'))
		
	examiner = User.query.filter_by(id=examiner_id, role='examiner').first_or_404()
	if examiner.status == 'Active':
		examiner.status = 'Inactive'
		flash(f'{examiner.name} has been deactivated.', 'warning')
	else:
		examiner.status = 'Active'
		flash(f'{examiner.name} has been approved.', 'success')
		
	db.session.commit()
	return redirect(url_for('manage_examiners'))

@app.route('/examiner_dashboard')
def examiner_dashboard():
	if session.get('role') != 'examiner':
		return redirect(url_for('login'))
	examiner = User.query.get_or_404(session.get('user_id'))
	if examiner.status != 'Active':
		session.clear()
		flash('Your account is inactive or pending for approval by admin.', 'warning')
		return redirect(url_for('login'))
	assigned_exams = Examination.query.filter_by(examiner_id=examiner.id).all()
	created_slots = Slots.query.filter_by(examiner_id=examiner.id).all()

	total_booked = Booking.query.join(Slots).filter(Slots.examiner_id == examiner.id, Booking.status != 'Cancelled').count()
	pending_evaluations = Booking.query.join(Slots).filter(Slots.examiner_id == examiner.id, Booking.status == 'Booked').count()
	today = date.today().isoformat()

	return render_template('examiner_dashboard.html',assigned_exams=assigned_exams,created_slots=created_slots,
	                       total_booked=total_booked,pending_evaluations=pending_evaluations,today=today)
	
@app.route('/examiner/exam/<int:exam_id>/slot/add', methods=['GET','POST'])
def create_slot(exam_id):
	if session.get('role') != 'examiner':
		return redirect(url_for('login'))
	
	exam = Examination.query.get_or_404(exam_id)
	today = date.today().isoformat()
	if exam.status != 'Slot Creation' or not (exam.slot_creation_start_date <= today <= exam.slot_creation_end_date):
		flash('Slot creation is not allowed', 'danger')
		return redirect(url_for('examiner_dashboard'))
	
	if request.method == 'POST':
		slot_date = request.form.get('date')
		if slot_date < exam.slot_booking_end_date:
			flash('Exam slot date must be on or after the student booking end date.', 'danger')
			return redirect(url_for('create_slot', exam_id=exam.id))

		capacity = request.form.get('max_capacity', type=int)
		new_slot = Slots(exam_id=exam.id,examiner_id=session.get('user_id'),date=slot_date,
		start_time=request.form.get('start_time'),end_time=request.form.get('end_time'),
		max_capacity=capacity,available_seats=capacity,status='Available')
		db.session.add(new_slot)
		db.session.commit()
		flash('Slot Created Successfully.', 'success')
		return redirect(url_for('examiner_dashboard'))
	return render_template('create_slot.html', exam=exam)

@app.route('/examiner/slot/edit/<int:slot_id>', methods=['GET','POST'])
def edit_slot(slot_id):
	if session.get('role') != 'examiner':
		return redirect(url_for('login'))
	slot = Slots.query.get_or_404(slot_id)
	if slot.examiner_id != session.get('user_id'):
		return redirect(url_for('examiner_dashboard'))
	today = date.today().isoformat()
	active_bookings = Booking.query.filter(Booking.slot_id == slot.id, Booking.status != 'Cancelled').count()

	if today >= slot.exam.slot_booking_start_date or active_bookings >0:
		flash('Slots cannot be edited after booking has started or students have booked the slot.', 'danger')
		return redirect(url_for('examiner_dashboard'))

	if request.method == 'POST':
		new_capacity = request.form.get('max_capacity', type=int)
		slot.date = request.form.get('date')
		slot.start_time = request.form.get('start_time')
		slot.end_time = request.form.get('end_time')
		slot.max_capacity = new_capacity
		slot.available_seats = new_capacity
		db.session.commit()
		flash('Slot updated successfully.', 'success')
		return redirect(url_for('examiner_dashboard'))
	return render_template('examiner_edit_slot.html', slot=slot)

@app.route('/examiner/slot/delete/<int:slot_id>', methods=['POST'])
def delete_slot(slot_id):
	if session.get('role') != 'examiner':
		return redirect(url_for('login'))
	
	slot = Slots.query.get_or_404(slot_id)
	if slot.examiner_id != session.get('user_id'):
		return redirect(url_for('examiner_dashboard'))
	today = date.today().isoformat()
	active_bookings = Booking.query.filter(Booking.slot_id == slot.id, Booking.status != 'Cancelled').count()

	if today >= slot.exam.slot_booking_start_date or active_bookings > 0:
		flash('Slots cannot be deleted after booking has started or students have booked the slot.', 'danger')
		return redirect(url_for('examiner_dashboard'))
	
	db.session.delete(slot)
	db.session.commit()
	flash('Slot deleted Successfully.', 'success')
	return redirect(url_for('examiner_dashboard'))

@app.route('/examiner/slot/<int:slot_id>/evaluate', methods=['GET', 'POST'])
def evaluate_slot(slot_id):
	if session.get('role') != 'examiner':
		return redirect(url_for('login'))
		
	slot = Slots.query.get_or_404(slot_id)
	
	if slot.examiner_id != session.get('user_id'):
		return redirect(url_for('examiner_dashboard'))
	
	if request.method == 'POST':
		booking_id = request.form.get('booking_id')
		booking = Booking.query.get_or_404(booking_id)
		
		rubrics = slot.exam.rubrics
		if rubrics:
			total_marks = 0
			for rubric in rubrics:
				val = request.form.get(f'rubric_{rubric.id}', type=int) or 0
				total_marks += val
			booking.marks = total_marks
		else:
			booking.marks = request.form.get('marks', type=int) or 0
			
		booking.remarks = request.form.get('remarks')
		booking.status = 'Evaluated'
		db.session.commit()
		return redirect(url_for('evaluate_slot', slot_id=slot.id))
		
	bookings = Booking.query.filter_by(slot_id=slot.id).all()
	return render_template('evaluate_slot.html', slot=slot, bookings=bookings)
	
@app.route('/student_dashboard')
def student_dashboard():
	if session.get('role') != 'student':
		return redirect(url_for('login'))

	student_id = session.get('user_id')
	today = date.today().isoformat()

	search = request.args.get('q', '').strip()
	exam_type = request.args.get('exam_type', '').strip()

	exam_query = Examination.query.join(Course).filter(Course.status == 'active',Examination.status.in_(['Booking Open', 'Slot Creation', 'Closed', 'Completed']))

	if exam_type:
		exam_query = exam_query.filter(Examination.exam_type == exam_type)

	examinations = exam_query.all()

	if search:
		s_lower = search.lower()
		examinations = [exam for exam in examinations if s_lower in exam.exam_name.lower() 
						or s_lower in exam.course.course_name.lower() or s_lower in exam.course.course_code.lower()]

	exam_types = [row[0] for row in db.session.query(Examination.exam_type).distinct().all()]
	bookings = Booking.query.filter_by(student_id=student_id).order_by(Booking.id.desc()).all()
	booked_exam_ids = {b.slot.exam_id for b in bookings if b.status != 'Cancelled'}

	return render_template('student_dashboard.html',examinations=examinations,bookings=bookings,
						   booked_exam_ids=booked_exam_ids,exam_types=exam_types,search=search,selected_type=exam_type,today=today)

@app.route('/student/exam/<int:exam_id>/slots')
def student_exam_slots(exam_id):
	if session.get('role') != 'student':
		return redirect(url_for('login'))
		
	exam = Examination.query.get_or_404(exam_id)
	student_id = session.get('user_id')
	today = date.today().isoformat()
	
	slots = Slots.query.filter_by(exam_id=exam.id).all()
	
	existing_booking = Booking.query.join(Slots).filter(Booking.student_id == student_id,Slots.exam_id == exam.id,Booking.status != 'Cancelled').first()
	booking_open = (exam.status == 'Booking Open' and exam.slot_booking_start_date <= today <= exam.slot_booking_end_date)
	
	return render_template('student_slots.html',exam=exam,slots=slots,existing_booking=existing_booking,booking_open=booking_open)

@app.route('/student/slot/<int:slot_id>/book', methods=['POST'])
def book_slot(slot_id):
	if session.get('role') != 'student':
		return redirect(url_for('login'))
		
	slot = Slots.query.get_or_404(slot_id)
	exam = slot.exam
	student_id = session.get('user_id')
	today = date.today().isoformat()
	
	if exam.status != 'Booking Open' or not (exam.slot_booking_start_date <= today <= exam.slot_booking_end_date):
		flash('Slot booking is currently closed for this examination.', 'danger')
		return redirect(url_for('student_exam_slots', exam_id=exam.id))
		
	duplicate = Booking.query.join(Slots).filter(Booking.student_id == student_id,Slots.exam_id == exam.id,Booking.status != 'Cancelled').first()
	if duplicate:
		flash('You have already booked a slot for this examination.', 'warning')
		return redirect(url_for('student_exam_slots', exam_id=exam.id))
		
	if slot.available_seats <= 0 or slot.status != 'Available':
		flash('This slot is already full or unavailable.', 'danger')
		return redirect(url_for('student_exam_slots', exam_id=exam.id))
		
	new_booking = Booking(student_id=student_id,slot_id=slot.id,booking_date=today,status='Booked')
	slot.available_seats -= 1
	if slot.available_seats == 0:
		slot.status = 'Full'
		
	db.session.add(new_booking)
	db.session.commit()
	
	flash('Slot Booked Successfully!', 'success')
	return redirect(url_for('student_dashboard'))

@app.route('/student/booking/<int:booking_id>/cancel', methods=['POST'])
def student_cancel_booking(booking_id):
	if session.get('role') != 'student':
		return redirect(url_for('login'))
		
	booking = Booking.query.get_or_404(booking_id)
	if booking.student_id != session.get('user_id'):
		return redirect(url_for('student_dashboard'))
		
	today = date.today().isoformat()
	exam = booking.slot.exam
	
	
	if booking.status != 'Booked' or today > exam.slot_booking_end_date:
		flash('This booking can no longer be cancelled.', 'warning')
		return redirect(url_for('student_dashboard'))
		
	booking.status = 'Cancelled'
	slot = booking.slot
	slot.available_seats += 1
	if slot.status == 'Full' and slot.available_seats > 0:
		slot.status = 'Available'
		
	db.session.commit()
	flash('Booking Cancelled Successfully.', 'info')
	return redirect(url_for('student_dashboard'))

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
	if session.get('role') != 'student':
		return redirect(url_for('login'))
		
	student = User.query.get_or_404(session.get('user_id'))
	
	if request.method == 'POST':
		student.name = request.form.get('name')
		student.phone = request.form.get('phone')
		student.department = request.form.get('department')
		new_password = request.form.get('password')
		if new_password:
			student.password = new_password
			
		db.session.commit()
		session['name'] = student.name
		flash('Profile Updated Successfully.', 'success')
		return redirect(url_for('student_profile'))
		
	return render_template('student_profile.html', student=student)

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == "GET":
		return render_template('login.html')
	
	elif request.method == 'POST':
		useremail = request.form['email']
		userpassword = request.form['password']
		
		user = User.query.filter_by(email=useremail).first()
		
		if user and user.password == userpassword:
			if user.role == 'examiner' and user.status != 'Active':
				flash('Your account is pending for approval by admin. Please wait until that or your account has been disabled.', 'warning')
				return redirect(url_for('login'))
			
			session['user_id'] = user.id
			session['name'] = user.name
			session['role'] = user.role
			
			if user.role == 'admin':
				return redirect(url_for('admin_dashboard'))
			if user.role == 'examiner':
				return redirect(url_for('examiner_dashboard'))
			if user.role == 'student':
				return redirect(url_for('student_dashboard'))
		else:
			flash('Invalid email or password', 'danger')
			return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'GET':
		return render_template('signup.html')
	elif request.method == "POST":
		name = request.form.get('name')
		email = request.form.get('email')
		password = request.form.get('password')
		role = request.form.get('role')
		department = request.form.get('department')
		phone = request.form.get('phone')

		if User.query.filter_by(email=email).first():
			flash('Email is alredy registered. Please use a different email.', 'danger')
			return redirect(url_for('signup'))			
		else:
			status = 'Pending' if role == 'examiner' else 'Active'

			credentials = User(name=name, email=email, password=password,role=role,department=department,phone=phone,status=status)
			db.session.add(credentials)
			db.session.commit()

			if role=='examiner':
				flash('Registration is Successfull! Plese wait for approval by Admin to login.', 'success')
			else:
				flash('Registration successful! Now you can log in.', 'success')
			return redirect(url_for('login'))


if __name__ == '__main__':
	app.run(debug=True)
