import os
from flask import render_template, request, redirect, url_for, flash

from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import text
from werkzeug.utils import secure_filename

from faststat import app, bcrypt, db
from faststat.forms import ComputeForm, StatForm, LoginForm, RegisterForm
from faststat.dataparse import DataSet, read_data
from faststat.db_models import User, Compute
from faststat.compute import display_stat_info, normality_tests, null_hypothesis_tests, one_way_anova, \
                    two_way_anova

# Allowed file types for file upload
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}


def allowed_file(file_name):
    """Function to check if file_name have the right extension.
    :arg file_name: str containing file name (must be either xls or xlsx)
    :return bool"""
    return '.' in file_name and file_name.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def reset_vars():
    """Reset all global variables used to None or empty lists"""
    global data_frame, info, template

    data_frame = None
    info = {'parms': {}, 'values': [], 'parm_values': [], 'parm_names': []}
    result = None
    template = "view_input.html"


def choose_template(func):
    """Based on the input of the user, chooses the proper HTML template to
    be rendered.
    :arg func: str with name of statistical analysis name
    :return str with HTML template name"""

    if func == 'Statistical Info' or func == 'One-way ANOVA':
        return "view_oneset_analysis.html"
    elif func == 'Normality Tests' or func == 'Null Hypothesis Tests' or func == 'Two-way ANOVA':
        return "view_twosets_analysis.html"


@app.route('/', methods=['GET', 'POST'])
def index():
    user = current_user
    form = StatForm(request.form)
    global filename, data_frame, parm_names, info, template
    plot = None
    
    if request.method == 'POST':

        # Save uploaded file on server if it exists and is valid
        if request.files:
            reset_vars()
            result = None
            file = request.files[form.filename.name]

            if file and allowed_file(file.filename):
                data_frame = read_data(file)

                # Make a valid version of filename for any file system
                filename = secure_filename(file.filename)
                info['file_name'] = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Store names of all statistical parameters (first row of the spread sheet)
                parm_names = data_frame.columns.values.tolist()
                info['parm_names'] = data_frame.columns.values.tolist()

            return render_template(template, form=form, user=user, filename=info['file_name'])

        # Choice of statistical analysis
        if request.form.get('stat_func'):
            info['stat_func'] = request.form.get('stat_func')
            template = choose_template(info['stat_func'])
            return render_template(template, form=form, user=user, parm_names=info['parm_names'],
                                   stat_func=info['stat_func'], parms=[])

        # Setup for simple statistical info display: one dataset
        if info['stat_func'] in ['Statistical Info', 'One-way ANOVA']:

            # Choice of parameters used for filtering data
            if request.form.get('parms'):
                parm_a = request.form.get('parmA')
                parm_b = request.form.get('parmB')
                info['parms'][parm_a] = 0
                info['parms'][parm_b] = 0
                info['parm_values'].append(list(set(data_frame[parm_a])))
                info['parm_values'].append(list(set(data_frame[parm_b])))

                return render_template(template, form=form,
                                       user=user, parm_names=info['parm_names'],
                                       stat_func=info['stat_func'], parms=list(info['parms'].keys()),
                                       parm_values=info['parm_values'], statready=False)

            # Choice of values of parameters to include in dataset.
            elif request.form.get('values'):
                parm_a = request.form.get('parmA')
                parm_b = request.form.get('parmB')
                value_a = request.form.get('valueA')
                value_b = request.form.get('valueB')
                info['parms'][parm_a] = value_a
                info['parms'][parm_b] = value_b

                # Converts values from str to int if they are numbers
                for parm, value in info['parms'].items():
                    if value.isdigit():
                        info['parms'][parm] = int(value)

                if info['stat_func'] == 'One-way ANOVA':
                    info['parm_names'] = list(set([parm[:-6] for parm in info['parm_names'] if 'bin' in parm]))

                return render_template(template, form=form,
                                       user=user, parm_names=info['parm_names'],
                                       stat_func=info['stat_func'], parms=list(info['parms'].keys()),
                                       values=list(info['parms'].values()), statready=True)

            # Choice of property to perform statistics on, building dataset and getting results
            elif request.form.get('getproperty'):
                info['statproperty'] = request.form.get('statproperty')

                if info['stat_func'] == 'Statistical Info':
                    dataset1 = DataSet(data_frame, info['statproperty'], **info['parms'])
                    result = display_stat_info(dataset1)
                else:
                    dataset1 = DataSet(data_frame, 'Total ' + info['statproperty'], **info['parms'])
                    result = one_way_anova(data_frame, dataset1, info['statproperty'])
                    result = result.to_html()

                if len(dataset1.data_frame) < 2:
                    result = "Insufficient data for the chosen parameters <br/>"
                    return render_template(template, form=form, user=user, result=result,
                                           parm_names=info['parm_names'], stat_func=info['stat_func'],
                                           parms=info['parms'], parm_values=info['parm_values'], statready=False)

                if user.is_authenticated:
                    compute_results = Compute()
                    form.populate_obj(compute_results)
                    compute_results.result = result
                    compute_results.plot = plot
                    compute_results.user = user
                    compute_results.filename = filename
                    db.session.add(compute_results)
                    db.session.commit()

                return render_template("view_output.html", form=form, result=result, plot=None, user=user)

        # Setup for statistical tools requiring two datasets
        elif info['stat_func'] in ['Normality Tests', 'Null Hypothesis Tests', 'Two-way ANOVA']:

            # Choice of parameters used for filtering data
            if request.form.get('parms'):
                parm1_a = request.form.get('parm1A')
                parm1_b = request.form.get('parm1B')
                parm2_a = request.form.get('parm2A')
                parm2_b = request.form.get('parm2B')
                info['parms'] = [dict(), dict()]
                info['parms'][0][parm1_a] = 0
                info['parms'][0][parm1_b] = 0
                info['parms'][1][parm2_a] = 0
                info['parms'][1][parm2_b] = 0

                info['parm_values'].append(list(set(data_frame[parm1_a])))
                info['parm_values'].append(list(set(data_frame[parm1_b])))
                info['parm_values'].append(list(set(data_frame[parm2_a])))
                info['parm_values'].append(list(set(data_frame[parm2_b])))

                return render_template(template, form=form,
                                       user=user, parm_names=info['parm_names'],
                                       stat_func=info['stat_func'],
                                       parms=list(info['parms'][0].keys()) + list(info['parms'][1].keys()),
                                       parm_values=info['parm_values'], statready=False)

            # Choice of values of parameters to include in dataset.
            elif request.form.get('values'):
                parm1_a = request.form.get('parm1A')
                parm1_b = request.form.get('parm1B')
                parm2_a = request.form.get('parm2A')
                parm2_b = request.form.get('parm2B')
                value1_a = request.form.get('value1A')
                value1_b = request.form.get('value1B')
                value2_a = request.form.get('value2A')
                value2_b = request.form.get('value2B')
                info['parms'][0][parm1_a] = value1_a
                info['parms'][0][parm1_b] = value1_b
                info['parms'][1][parm2_a] = value2_a
                info['parms'][1][parm2_b] = value2_b

                # Converts values from str to int if they are numbers
                for i in [0, 1]:
                    for parm, value in info['parms'][i].items():
                        if value.isdigit():
                            info['parms'][i][parm] = int(value)

                if info['stat_func'] == 'Two-way ANOVA':
                    info['parm_names'] = list(set([parm[:-6] for parm in info['parm_names'] if 'bin' in parm]))

                return render_template(template, form=form,
                                       user=user, parm_names=info['parm_names'],
                                       stat_func=info['stat_func'],
                                       parms=list(info['parms'][0].keys()) + list(info['parms'][1].keys()),
                                       values=list(info['parms'][0].values()) + list(info['parms'][1].values()),
                                       statready=True)

            elif request.form.get('getproperty'):
                info['statproperty'] = request.form.get('statproperty')
                if info['stat_func'] in ['Normality Tests', 'Null Hypothesis Tests']:
                    dataset1 = DataSet(data_frame, info['statproperty'], **info['parms'][0])
                    dataset2 = DataSet(data_frame, info['statproperty'], **info['parms'][1])
                    result = normality_tests(dataset1, dataset2)
                    result += display_stat_info(dataset1)
                    result += display_stat_info(dataset2)

                    if info['stat_func'] == 'Null Hypothesis Tests':
                        result += null_hypothesis_tests(dataset1, dataset2)
                else:
                    dataset1 = DataSet(data_frame, 'Total ' + info['statproperty'], **info['parms'][0])
                    dataset2 = DataSet(data_frame, 'Total ' + info['statproperty'], **info['parms'][1])
                    parm1_a = request.form.get('parm1A')
                    parm1_b = request.form.get('parm1B')
                    parm2_a = request.form.get('parm2A')
                    parm2_b = request.form.get('parm2B')
                    value1_a = request.form.get('value1A')
                    value1_b = request.form.get('value1B')
                    value2_a = request.form.get('value2A')
                    value2_b = request.form.get('value2B')

                    if parm1_a == parm2_a and value1_a != value2_a:
                        value_a = value1_a
                        value_b = value2_a
                        parameter = parm1_a
                    elif parm1_a == parm2_b and value1_a != value2_b:
                        value_a = value1_a
                        value_b = value2_b
                        parameter = parm1_a
                    elif parm1_b == parm2_a and value1_b != value2_a:
                        value_a = value1_b
                        value_b = value2_a
                        parameter = parm1_b
                    elif parm1_b == parm2_b and value1_b != value2_b:
                        value_a = value1_b
                        value_b = value2_b
                        parameter = parm1_b
                    else:
                        result = "Cannot perform two-way ANOVA for these two datasets."

                        return render_template("view.html", form=form,
                                               result=result, user=user)
                    
                    result, plot = two_way_anova(data_frame, dataset1, dataset2,
                                                 parameter, value_a, value_b, info['statproperty'])
                    result = result.to_html()

                if user.is_authenticated:
                    compute_results = Compute()
                    form.populate_obj(compute_results)
                    compute_results.result = result
                    compute_results.plot = plot
                    compute_results.user = user
                    compute_results.filename = filename
                    db.session.add(compute_results)
                    db.session.commit()

                return render_template("view_output.html", form=form, 
                                       result=result, user=user,
                                       plot=plot)

        elif request.form.get('reset'):
            reset_vars()
            return render_template("view.html", form=form, user=user)

    else:
        result = None
        return render_template("view.html", form=form, user=user)


def populate_form_from_instance(instance):
    """Repopulate form with previous values"""
    form = ComputeForm()
    for field in form:
        field.data = getattr(instance, field.name)
    return form


def send_email(user):
    from flask_mail import Mail, Message
    mail = Mail(app)
    msg = Message("Compute Computations Complete",
                  recipients=[user.email])
    msg.body = """
A simulation has been completed by the Flask Compute app.
Please log in at 

http://127.0.0.1:5000/login

to see the results.

---
If you don't want email notifications when a result is found,
please register a new user and leave the 'notify' field 
unchecked.
"""
    mail.send(msg)

@app.route("/about")
def about():
    return render_template('about.html', title='About')

@app.route('/reg', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reg.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template("login.html", title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/old')
@login_required
def old():
    data = []
    user = current_user
    if user.is_authenticated:
        instances = user.Compute.order_by(text('-id')).all()
        for instance in instances:
            form = populate_form_from_instance(instance)

            result = instance.result
            plot = instance.plot
            if instance.comments:
                comments = instance.comments
            else:
                comments = ''
            data.append({'form': form, 'result': result,
                         'id': instance.id, 'plot': plot, 
                         'comments': comments})
    return render_template("old.html", data=data)


@app.route('/add_comment', methods=['GET', 'POST'])
@login_required
def add_comment():
    user = current_user
    if request.method == 'POST' and user.is_authenticated:
        instance = user.Compute.order_by(text('-id')).first()
        instance.comments = request.form.get("comments", None)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<id>', methods=['GET','POST'])
@login_required
def delete_post(id):
    id = int(id)
    user = current_user
    if user.is_authenticated:
        if id == -1:
            instances = user.Compute.delete()
        else:
            try:
                instance = user.Compute.filter_by(id=id).first()
                db.session.delete(instance)
            except:
                pass

        db.session.commit()
    return redirect(url_for('old'))

