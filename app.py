import time
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import send_from_directory
from flask_uploads import UploadSet, configure_uploads, patch_request_class, IMAGES
from datetime import datetime
from forms import PromotionForm
import os
from flask import flash
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired





app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
db = SQLAlchemy(app)
app.config['WTF_CSRF_ENABLED'] = False
app.secret_key = '12345'

# Настройка загрузки изображений
images = UploadSet('images', IMAGES)
app.config['UPLOADED_IMAGES_DEST'] = 'static/uploads/promotions'
configure_uploads(app, images)
patch_request_class(app, size=None)

class PromotionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    position = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)

class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

class ScheduleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)




@app.route('/')
def index():
    return render_template('index.html')

@app.route('/employees', methods=['GET', 'POST'])
def employees():
    if request.method == 'POST':
        telegram_id = request.form['telegram_id']
        full_name = request.form['full_name']
        birth_date_str = request.form['birth_date']
        position = request.form['position']
        phone_number = request.form['phone_number']

        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

        new_employee = Employee(
            telegram_id=telegram_id,
            full_name=full_name,
            birth_date=birth_date,
            position=position,
            phone_number=phone_number
        )

        db.session.add(new_employee)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error during deletion: {e}")

        # Добавляем flash message
        flash('Сотрудник успешно добавлен!', 'success')
        time.sleep(2)
        return redirect(url_for('employees'))


    employees_data = Employee.query.all()
    return render_template('employees.html', employees_data=employees_data)

@app.route('/delete_employee/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)

    # Получаем telegram_id перед удалением сотрудника
    deleted_telegram_id = employee.telegram_id

    db.session.delete(employee)

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error during deletion: {e}")

    # Возвращаем JSON-ответ для обработки на стороне клиента
    return jsonify({'status': 'success', 'deleted_telegram_id': deleted_telegram_id})

@app.route('/uploads/promotions/<filename>')
def uploaded_promotion(filename):
    return send_from_directory(app.config['UPLOADED_IMAGES_DEST'], filename)

@app.route('/promotions', methods=['GET', 'POST'])
def promotions():
    form = PromotionForm()

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        image = request.files['image']
        image_url = images.save(image, name=f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}')

        new_promotion = Promotion(title=title, description=description, image_url=image_url)
        db.session.add(new_promotion)
        db.session.commit()

        # После успешного добавления, перенаправляем на ту же страницу
        return redirect(url_for('promotions'))

    promotions_data = Promotion.query.all()

    return render_template('promotions.html', form=form, promotions_data=promotions_data)

@app.route('/delete_promotion/<int:id>', methods=['POST'])
def delete_promotion(id):
    promotion = Promotion.query.get_or_404(id)

    # Удаление изображения из папки
    image_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], promotion.image_url)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(promotion)
    db.session.commit()


    return redirect(url_for('promotions'))

@app.route('/uploads/schedule/<filename>')
def uploaded_image(filename):
    return send_from_directory(app.config['UPLOADED_IMAGES_DEST'], filename)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    form = PromotionForm()

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        image = request.files['image']
        image_url = images.save(image, name=f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secure_filename(image.filename)}')

        new_schedule_item = ScheduleItem(title=title, description=description, image_url=image_url)
        db.session.add(new_schedule_item)
        db.session.commit()

        # После успешного добавления, перенаправляем на ту же страницу
        return redirect(url_for('schedule'))

    schedule_data = ScheduleItem.query.all()

    return render_template('schedule.html', form=form, schedule_data=schedule_data)

@app.route('/delete_schedule_item/<int:id>', methods=['POST'])
def delete_schedule_item(id):
    schedule_item = ScheduleItem.query.get_or_404(id)

    # Удаление изображения из папки
    image_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], schedule_item.image_url)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(schedule_item)
    db.session.commit()

    # Возвращаем JSON-ответ для обработки на стороне клиента
    return redirect(url_for('schedule'))


# ... другие обработчики ...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


