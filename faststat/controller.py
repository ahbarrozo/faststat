import os
from flask import render_template, request, redirect, send_from_directory, url_for, flash

from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import text
from werkzeug.utils import secure_filename
from pandas import DataFrame

from faststat import app, bcrypt, db, UPLOAD_DIR
from faststat.objects import FastStat
from faststat.forms import ComputeForm, StatForm, LoginForm, RegisterForm
from faststat.dataparse import DataSet, read_data
from faststat.db_models import User, Compute
from faststat.compute import display_stat_info, normality_tests, null_hypothesis_tests, one_way_anova, \
                    two_way_anova

# Allowed file types for file upload
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

# HTML extension that will be added to a data frame converted to HTML format. 
# Used for rendering
HTML_EXT = """
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KyZXEAg3QhqLMpG8r+8fhAXLRk2vvoC2f3B09zVXn8CA5QIVfZOJ3BCsw2P0p/We" crossorigin="anonymous">

    <link rel="stylesheet" type="text/css" href="{{ url_for('static',
    filename='basic.css') }}">

    """

info = FastStat()

def allowed_file(file_name):
    """Function to check if file_name have the right extension.
:arg file_name: str containing file name (must be either xls or xlsx)
:return bool"""
    return file_name.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def choose_template(func):
    """Based on the input of the user, chooses the proper HTML template to
    be rendered.
    :arg func: str with name of statistical analysis name
    :return str with HTML template name"""

    if func == 'Statistical Info' or func == 'One-way ANOVA':
        return "view_oneset_analysis.html"
    elif func == 'Normality Tests' or func == 'Null Hypothesis Tests' or func == 'Two-way ANOVA':
        return "view_twosets_analysis.html"
    else:
        return "view_input.html"



@app.route('/', methods=['GET', 'POST'])
def index():
    form = StatForm()
    global info
    plot = None

    if request.method == 'POST':
        # Save uploaded file on server if it exists and is valid
        if form.validate_on_submit(): 
            FILE = request.files[form.filename.name]

            if allowed_file(FILE.filename):
                flash(f'File {FILE.filename} read by the server.', 'success')
                info = FastStat(file = FILE)

            else:
                flash(f'Invalid file format.', 'danger')
                return render_template("view.html", 
                                       form=form, 
                                       filename=None)

            return render_template("view_input.html", form=form,
                                   filename=info.file_name)

        # Choice of statistical analysis
        if request.form.get('stat_func'):
            info.stat_func = request.form.get('stat_func')
            info.template = choose_template(info.stat_func)

            # In case no option is chosen
            if info.template == "view_input.html":
                flash(f'Please choose a tool.', 'danger')
                return render_template("view_input.html", form=form,
                                       filename=info.file_name)

            return render_template(info.template, 
                                   form=form, 
                                   filename=info.file_name,
                                   parm_names=info.parm_names,
                                   stat_func=info.stat_func, 
                                   parms=[])

        # Setup for simple statistical info display: one dataset
        if info.stat_func in ['Statistical Info', 'One-way ANOVA']:

            # Choice of parameters used for filtering data
            if request.form.get('parms'):
                parm_a = request.form.get('parm_a')
                parm_b = request.form.get('parm_b')


                # In case no option is chosen
                if parm_a == "none" or parm_b == "none":
                    flash(f'Please choose a parameter.', 'danger')
                    return render_template("view_input.html", form=form,
                                           stat_func=info.stat_func, 
                                           filename=info.file_name)

                info.parms[parm_a] = 0
                info.parms[parm_b] = 0
                info.parm_values.append(list(set(info.data_frame[parm_a])))
                info.parm_values.append(list(set(info.data_frame[parm_b])))
                return render_template(info.template, form=form,
                                       filename=info.file_name,
                                       parm_names=info.parm_names,
                                       stat_func=info.stat_func, 
                                       parms=list(info.parms.keys()),
                                       parm_values=info.parm_values, 
                                       statready=False)

            # Choice of values of parameters to include in dataset.
            elif request.form.get('values'):

                # From Python 3.7, we can access dict entries per order of insertion. This is used here
                parms = tuple(info.parms)
                parm_a, parm_b = parms
                value_a = request.form.get('value_a')
                value_b = request.form.get('value_b')
                info.parms[parm_a] = value_a
                info.parms[parm_b] = value_b

                # Converts values from str to int if they are numbers
                for parm, value in info.parms.items():
                    if type(value) is not int and value.isdigit():
                        info.parms[parm] = int(value)

                # The list of parameters in ANOVA is more restricted, so we
                # need to be able to parse them conditionally
                if info.stat_func == 'One-way ANOVA':
                    parm_names = tuple(set([parm[:-6] for parm in info.parm_names 
                                      if 'bin' in parm]))
                else:
                    parm_names = info.parm_names

                return render_template(info.template, form=form,
                                       filename=info.file_name,
                                       parm_names=parm_names,
                                       stat_func=info.stat_func, 
                                       parms=tuple(info.parms.keys()),
                                       values=tuple(info.parms.values()), 
                                       statready=True)


            # Choice of property to perform statistics on, building dataset and getting results
            elif request.form.get('getproperty'):
                info.stat_property = request.form.get('statproperty')

                if info.stat_func == 'Statistical Info':
                    dataset1 = DataSet(info.data_frame, info.stat_property,
                                       **info.parms)
                    result = display_stat_info(dataset1)
                else:
                    if 'Total ' + info.stat_property in info.parm_names:
                        prefix = 'Total '

                    elif 'Average ' + info.stat_property in info.parm_names:
                        prefix = 'Average '

                    else:
                        flash("""Could not identify any final observable
                              related to bin variable chosen (is it an 
                              Average, or a Total?). Please check your 
                              spreadsheet labeling and correct it.""", 'danger')
                        info.reset(hard_reset=True)
                        return redirect(url_for('index'))

                    dataset1 = DataSet(info.data_frame, prefix +
                                       info.stat_property, **info.parms)
                    result = one_way_anova(info.data_frame, dataset1, info.stat_property)
                    result = result.to_html()

                if dataset1.data_set.empty or len(dataset1.data_set) < 2:
                    flash('Insufficient data. Please check your input \
                          variaibles or spreadsheet', 'danger')

                    info.reset(hard_reset=True)
                    return redirect(url_for('index'))

                if current_user.is_authenticated:
                    compute_results = Compute()
                    form.populate_obj(compute_results)
                    compute_results.result = result
                    compute_results.plot = plot
                    compute_results.user = current_user
                    compute_results.filename = info.file_name
                    db.session.add(compute_results)
                    db.session.commit()

                return render_template("view_output.html", 
                                       form=form, 
                                       filename=info.file_name,
                                       result=result, plot=None)

        # Setup for statistical tools requiring two datasets
        elif info.stat_func in ['Normality Tests', 'Null Hypothesis Tests', 'Two-way ANOVA']:

            # Choice of parameters used for filtering data
            if request.form.get('parms'):
                parm_1a = request.form.get('parm_1a')
                parm_1b = request.form.get('parm_1b')
                parm_2a = request.form.get('parm_2a')
                parm_2b = request.form.get('parm_2b')
                info.parms = [dict(), dict()]
                info.parms[0][parm_1a] = 0
                info.parms[0][parm_1b] = 0
                info.parms[1][parm_2a] = 0
                info.parms[1][parm_2b] = 0
                info.parm_values.append(list(set(info.data_frame[parm_1a])))
                info.parm_values.append(list(set(info.data_frame[parm_1b])))
                info.parm_values.append(list(set(info.data_frame[parm_2a])))
                info.parm_values.append(list(set(info.data_frame[parm_2b])))

                return render_template(info.template, 
                                       form=form,
                                       filename=info.file_name,
                                       parm_names=info.parm_names,
                                       stat_func=info.stat_func,
                                       parms=tuple(info.parms[0].keys()) + tuple(info.parms[1].keys()),
                                       parm_values=info.parm_values, 
                                       statready=False)

            # Choice of values of parameters to include in dataset.
            elif request.form.get('values'):
                parms_1 = tuple(info.parms[0])
                parms_2 = tuple(info.parms[1])
                parm_1a, parm_1b = parms_1
                parm_2a, parm_2b = parms_2
                value_1a = request.form.get('value_1a')
                value_1b = request.form.get('value_1b')
                value_2a = request.form.get('value_2a')
                value_2b = request.form.get('value_2b')
                info.parms[0][parm_1a] = value_1a
                info.parms[0][parm_1b] = value_1b
                info.parms[1][parm_2a] = value_2a
                info.parms[1][parm_2b] = value_2b

                # Converts values from str to int if they are numbers
                for i in [0, 1]:
                    for parm, value in info.parms[i].items():
                        if type(value) is not int and value.isdigit():
                            info.parms[i][parm] = int(value)

                # The list of parameters in ANOVA is more restricted, so we
                # need to be able to parse them conditionally
                if info.stat_func == 'Two-way ANOVA':
                    parm_names = list(set([parm[:-6] for parm in
                                                info.parm_names if 'bin' in parm]))

                else:
                    parm_names = info.parm_names

                return render_template(info.template, 
                                       form=form,
                                       filename=info.file_name,
                                       parm_names=parm_names,
                                       stat_func=info.stat_func,
                                       parms=tuple(info.parms[0].keys()) + tuple(info.parms[1].keys()),
                                       values=tuple(info.parms[0].values()) + tuple(info.parms[1].values()),
                                       statready=True)

            elif request.form.get('getproperty'):
                info.stat_property = request.form.get('statproperty')
                if info.stat_func in ['Normality Tests', 'Null Hypothesis Tests']:
                    dataset1 = DataSet(info.data_frame, info.stat_property,
                                       **info.parms[0])
                    dataset2 = DataSet(info.data_frame, info.stat_property, 
                                       **info.parms[1])

                    """Check size of data sets to ensure it is possible to
                    perform analysis."""
                    if dataset1.data_set.empty or len(dataset1.data_set) < 2:
                        flash('Insufficient data for Dataset 1. Please check your input \
                              variaibles or spreadsheet', 'danger')

                        info.reset(hard_reset=True)
                        return redirect(url_for('index'))

                    if dataset2.data_set.empty or len(dataset2.data_set) < 2:
                        flash("""Insufficient data for Dataset 2. Please check
                              your input variaibles or spreadsheet""", 'danger')

                        info.reset(hard_reset=True)
                        return redirect(url_for('index'))

                    result = normality_tests(dataset1, dataset2)
                    result += display_stat_info(dataset1)
                    result += display_stat_info(dataset2)

                    if info.stat_func == 'Null Hypothesis Tests':
                        result += null_hypothesis_tests(dataset1, dataset2)
                else:
                    if 'Total ' + info.stat_property in info.parm_names:
                        prefix = 'Total '

                    elif 'Average ' + info.stat_property in info.parm_names:
                        prefix = 'Average '

                    else:
                        flash("""Could not identify any final observable
                              related to bin variable chosen (is it an 
                              Average, or a Total?). Please check your 
                              spreadsheet labeling and correct it.""", 'danger')
                        info.reset(hard_reset=True)
                        return redirect(url_for('index'))

                    dataset1 = DataSet(info.data_frame, prefix +
                                       info.stat_property, **info.parms[0])
                    dataset2 = DataSet(info.data_frame, prefix +
                                       info.stat_property, **info.parms[1])

                    """Check size of data sets to ensure it is possible to
                    perform analysis."""
                    if dataset1.data_set.empty or len(dataset1.data_set) < 2:
                        flash('Insufficient data for Dataset 1. Please check your input \
                              variaibles or spreadsheet', 'danger')
                        info.reset(hard_reset=True)

                        return redirect(url_for('index'))


                    if dataset2.data_set.empty or len(dataset2.data_set) < 2:
                        flash('Insufficient data for Dataset 2. Please check your input \
                              variaibles or spreadsheet', 'danger')
                        info.reset(hard_reset=True)

                        return redirect(url_for('index'))

                    parms_1 = tuple(info.parms[0])
                    parms_2 = tuple(info.parms[1])
                    parm_1a, parm_1b = parms_1
                    parm_2a, parm_2b = parms_2
                    value_1a = info.parms[0][parm_1a]
                    value_1b = info.parms[0][parm_1b]
                    value_2a = info.parms[1][parm_2a]
                    value_2b = info.parms[1][parm_2b]

                    if parm_1a == parm_2a and value_1a != value_2a:
                        value_a = value_1a
                        value_b = value_2a
                        parameter = parm_1a
                    elif parm_1a == parm_2b and value_1a != value_2b:
                        value_a = value_1a
                        value_b = value_2b
                        parameter = parm1_a
                    elif parm_1b == parm_2a and value_1b != value_2a:
                        value_a = value_1b
                        value_b = value_2a
                        parameter = parm_1b
                    elif parm_1b == parm_2b and value_1b != value_2b:
                        value_a = value_1b
                        value_b = value_2b
                        parameter = parm_1b
                    else:
                        flash('Cannot perform two-way ANOVA for these \
                              two datasets', 'danger')
                        info.reset(hard_reset=True)

                        return redirect(url_for('index'))
                    try:
                        result, plot = two_way_anova(info.data_frame, dataset1, dataset2,
                                                     parameter, value_a, value_b,
                                                     info.stat_property)
                    except ValueError:
                        flash("""Error due to non-numeric data. Please check your
                              spreadsheet.""", 'danger')
                        info.reset(hard_reset=True)
                        return redirect(url_for('index'))
                    except KeyError:
                        flash("""Numerical error while running Smirnov-Grubbs'
                              test. Check for extreme outliers. If problem
                              persists, please contact admin.""", 'danger')
                        info.reset(hard_reset=True)
                        return redirect(url_for('index'))

                    result = result.to_html()

                if current_user.is_authenticated:
                    compute_results = Compute()
                    form.populate_obj(compute_results)
                    compute_results.result = result
                    compute_results.plot = plot
                    compute_results.user = current_user
                    compute_results.filename = info.file_name
                    db.session.add(compute_results)
                    db.session.commit()

                return render_template("view_output.html", 
                                       form=form,
                                       filename=info.file_name,
                                       result=result, 
                                       plot=plot)

        elif request.form.get('reset'):
            info.reset()
            return render_template("view.html", 
                                   form=form,
                                   filename=info.file_name)

    else:
        if info.data_frame is not None:
            return render_template("view_input.html", 
                                   form=form, 
                                   filename=info.file_name)

        else:
            return render_template("view.html", 
                                   form=form,
                                   filename=None)


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


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    info.reset(hard_reset=True)
    return redirect(url_for('index'))

@app.route('/new_calc', methods=['GET', 'POST'])
def new_calc():
    info.reset()
    return redirect(url_for('index'))

@app.route('/get_df/<filename>')
def get_df(filename):
    #global data_frame
    html_form = info.data_frame.to_html()
    html_form = html_form.replace('<table border="1" class="dataframe">', 
                      '<table class="table table-striped">')
    html_filepath = os.path.join(app.config['UPLOAD_FOLDER'],f"{filename}.html")
    html_file = open(html_filepath, "w")
    html_file.write(HTML_EXT)
    html_file.write(html_form)
    html_file.close()

    return render_template(f'{UPLOAD_DIR}/{filename}.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/old')
@login_required
def old():
    data = []
    if current_user.is_authenticated:
        instances = current_user.Compute.order_by(text('-id')).all()
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
    if request.method == 'POST' and current_user.is_authenticated:
        instance = current_user.Compute.order_by(text('-id')).first()
        instance.comments = request.form.get("comments", None)
        db.session.commit()
    return redirect(url_for('old'))


@app.route('/delete/<id>', methods=['GET','POST'])
@login_required
def delete_post(id):
    id = int(id)
    if current_user.is_authenticated:
        if id == -1:
            instances = current_user.Compute.delete()
        else:
            try:
                instance = current_user.Compute.filter_by(id=id).first()
                db.session.delete(instance)
            except:
                pass

        db.session.commit()
    return redirect(url_for('old'))

