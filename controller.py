from flask import Flask, render_template, request, redirect, url_for
from forms import ComputeForm, StatForm
from db_models import db, User, Compute
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import sys, os, urllib
from compute import check_outliers, display_stat_info, normality_tests, null_hypothesis_tests, two_way_anova
from app import app, statData, statParm, statFunc, parmNames, dataset1, dataset2
from werkzeug import secure_filename
from dataparse import DataSet, readData

login_manager = LoginManager()
login_manager.init_app(app)

# Relative path of directory for uploaded files
UPLOAD_DIR = 'uploads/'

app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.secret_key = 'MySecretKey'

if not os.path.isdir(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

# Allowed file types for file upload
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}


def allowed_file(filename):
    """Does filename have the right extension?"""
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/', methods=['GET', 'POST'])
def index():
    user = current_user
    form = StatForm(request.form)
    global filename, statData, statParm, statFunc, datasetA, datasetB, parmNames
    parms = []
    values = []
    parmValues = []
    statproperty = None
    plot = None
    
    if request.method == 'POST':

        # Save uploaded file on server if it exists and is valid
        if request.files:
            statData = None
            statFunc = None
            statParm = [{}, {}]
            dataset1 = None
            dataset2 = None
            parmNames = None
            selectfunc = None
            result = None
            file = request.files[form.filename.name]
            if file and allowed_file(file.filename):
                statData = readData(file)

                # Make a valid version of filename for any file system
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Store names of all statistical parameters (first row of the spread sheet)
                parmNames = statData.columns.values.tolist()

            return render_template("view_input.html", form=form, user=user, filename=filename)

        # Choice of statistical analysis
        if request.form.get('selectfunc') == 'Statistical Info' or request.form.get('selectfunc') == 'One-way ANOVA':
            selectfunc = request.form.get('selectfunc')
            statFunc = selectfunc
            return render_template("view_statinfo.html", form=form, user=user, parmNames=parmNames,
                                   selectfunc=selectfunc, parms=[])

        elif (request.form.get('selectfunc') == 'Normality Tests' or 
              request.form.get('selectfunc') == 'Null Hypothesis Tests' or 
              request.form.get('selectfunc') == 'Two-way ANOVA'):
            selectfunc = request.form.get('selectfunc')
            statFunc = selectfunc
            return render_template("view_normtests.html", form=form, user=user, parmNames=parmNames,
                                   selectfunc=selectfunc, parms=[])
      
        # Setup for simple statistical info display: one dataset
        if statFunc == 'Statistical Info':
     
            # Choice of parameters used for filtering data
            if request.form.get('parms'):
                parms.append(request.form.get('parm1A'))
                parms.append(request.form.get('parm1B'))
                parmValues.append(list(set(statData[parms[0]])))
                parmValues.append(list(set(statData[parms[1]])))
                return render_template("view_statinfo.html", form=form,
                                        user=user, parmNames=parmNames,
                                        selectfunc=statFunc, parms=parms,
                                        parmValues=parmValues,statready=False)

            # Choice of values of parameters to include in dataset.
            elif request.form.get('values'):
                parms.append(request.form.get('parm1A'))
                parms.append(request.form.get('parm1B'))
                values.append(request.form.get('value1A'))
                values.append(request.form.get('value1B'))

                # Converts values from str to int if they are numbers
                for index in range(0, len(values)):
                    if values[index].isdigit():
                        values[index] = int(values[index])
                statParm[0][request.form.get('parm1A')] = values[0]
                statParm[0][request.form.get('parm1B')] = values[1]

                return render_template("view_statinfo.html", form=form,
                                       user=user, parmNames=parmNames,
                                       selectfunc=statFunc, parms=parms,
                                       values=values, statready=True)

            # Choice of property to perform statistics on, building dataset and getting results
            elif request.form.get('getproperty'):
                statproperty = request.form.get('statproperty')
                dataset1 = DataSet(statData, statproperty, **statParm[0])

                if len(dataset1.data_frame()) < 2:
                    result = "Insufficient data for the chosen parameters <br/>"
                    return render_template("view_statinfo.html", form=form, user=user, result=result,
                                           parmNames=parmNames, selectfunc=statFunc,
                                           parms=parms, parmValues=parmValues, statready=False)

                result = display_stat_info(dataset1)

                if user.is_authenticated:
                    object = Compute()
                    form.populate_obj(object)
                    object.result = result
                    object.plot = plot
                    object.user = user
                    object.filename = filename
                    db.session.add(object)
                    db.session.commit()

                return render_template("view_output.html", form=form, result=result, plot=None, user=user)

        if statFunc == 'One-way ANOVA':

            # Choice of parameters used for filtering data
            if request.form.get('parms'):
                parms.append(request.form.get('parm1A'))
                parms.append(request.form.get('parm1B'))
                parmValues.append(list(set(statData[parms[0]])))
                parmValues.append(list(set(statData[parms[1]])))
                return render_template("view_owanova.html", form=form, user=user, parmNames=parmNames,
                                       selectfunc=statFunc, parms=parms, parmValues=parmValues, statready=False)

            # Choice of values of parameters to include in dataset.
            elif request.form.get('values'):
                parms.append(request.form.get('parm1A'))
                parms.append(request.form.get('parm1B'))
                values.append(request.form.get('value1A'))
                values.append(request.form.get('value1B'))

                # Converts values from str to int if they are numbers
                for index in range(0, len(values)):
                    if values[index].isdigit():
                        values[index] = int(values[index])
                statParm[0][request.form.get('parm1A')] = values[0]
                statParm[0][request.form.get('parm1B')] = values[1]

                return render_template("view_owanova.html", form=form,
                                       user=user, parmNames=parmNames,
                                       selectfunc=statFunc, parms=parms,
                                       values=values, statready=True)

            # Choice of property to perform statistics on, building dataset and getting results
            elif request.form.get('getproperty'):
                statproperty = request.form.get('statproperty')
                dataset1 = DataSet(statData, statproperty, **statParm[0])

                if len(dataset1.data_frame()) < 2:
                    result = "Insufficient data for the chosen parameters <br/>"
                    return render_template("view_owanova.html", form=form,
                                            user=user, result=result, 
                                            parmNames=parmNames, selectfunc=statFunc, 
                                            parms=parms, parmValues=parmValues, 
                                            statready=False)

                result = display_stat_info(dataset1)

                if user.is_authenticated:
                    object = Compute()
                    form.populate_obj(object)
                    object.result = result
                    object.plot = plot
                    object.user = user
                    object.filename = filename
                    db.session.add(object)
                    db.session.commit()

                return render_template("view_output.html", form=form, 
                                        result=result, plot=None, 
                                        user=user)

        # Setup for statistical tools requiring two datasets
        elif statFunc == 'Normality Tests' or statFunc == 'Null Hypothesis Tests' or statFunc == 'Two-way ANOVA':

            # Choice of parameters used for filtering data
            if request.form.get('parms'):
                parms.append(request.form.get('parm1A'))
                parms.append(request.form.get('parm1B'))
                parms.append(request.form.get('parm2A'))
                parms.append(request.form.get('parm2B'))
                for i in range(0, len(parms)):
                    parmValues.append(list(set(statData[parms[i]])))
                return render_template("view_normtests.html", form=form, 
                                        user=user, parmNames=parmNames, 
                                        selectfunc=statFunc, parms=parms, 
                                        parmValues=parmValues, statready=False)

            # Choice of values of parameters to include in dataset.
            elif request.form.get('values'):
                parms.append(request.form.get('parm1A'))
                parms.append(request.form.get('parm1B'))
                parms.append(request.form.get('parm2A'))
                parms.append(request.form.get('parm2B'))
                values.append(request.form.get('value1A'))
                values.append(request.form.get('value1B'))
                values.append(request.form.get('value2A'))
                values.append(request.form.get('value2B'))
                for index in range(0, len(values)):
                    if values[index].isdigit():
                        values[index] = int(values[index])
                statParm[0][request.form.get('parm1A')] = values[0]
                statParm[0][request.form.get('parm1B')] = values[1]
                statParm[1][request.form.get('parm2A')] = values[2]
                statParm[1][request.form.get('parm2B')] = values[3]
                if statFunc == 'Two-way ANOVA':
                    parmNames = list(set([ parm[:-6] for parm in parmNames if 'bin' in parm ]))
                return render_template("view_normtests.html", form=form, 
                                        user=user, parmNames=parmNames, 
                                        selectfunc=statFunc, parms=parms, 
                                        values=values, statready=True)

            elif request.form.get('getproperty'):
                statproperty = request.form.get('statproperty')
                if statFunc == 'Normality Tests' or statFunc == 'Null Hypothesis Tests':
                    dataset1 = DataSet(statData, statproperty, **statParm[0])
                    dataset2 = DataSet(statData, statproperty, **statParm[1])
                    result = normality_tests(dataset1, dataset2)
                    result += display_stat_info(dataset1)
                    result += display_stat_info(dataset2)

                    if statFunc == 'Null Hypothesis Tests':
                        result += null_hypothesis_tests(dataset1, dataset2)
                else:
                    dataset1 = DataSet(statData, 'Total ' + statproperty, **statParm[0])
                    dataset2 = DataSet(statData, 'Total ' + statproperty, **statParm[1])               
                    parm1A = request.form.get('parm1A')
                    parm1B = request.form.get('parm1B')
                    parm2A = request.form.get('parm2A')
                    parm2B = request.form.get('parm2B')
                    value1A = request.form.get('value1A')
                    value1B = request.form.get('value1B')
                    value2A = request.form.get('value2A')
                    value2B = request.form.get('value2B')

                    if parm1A == parm2A and value1A != value2A:
                        valueA = value1A
                        valueB = value2A
                        parameter = parm1A
                    elif parm1A == parm2B and value1A != value2B: 
                        valueA = value1A
                        valueB = value2B
                        parameter = parm1A
                    elif parm1B == parm2A and value1B != value2A:
                        valueA = value1B
                        valueB = value2A
                        parameter = parm1B
                    elif parm1B == parm2B and value1B != value2B:
                        valueA = value1B
                        valueB = value2B
                        parameter = parm1B
                    else:
                        print("Cannot perform two-way ANOVA for these two datasets.")
                        result = None
                        return render_template("view.html", form=form, 
                                                result=result, user=user)
                    
                    result, plot = two_way_anova(statData, dataset1, dataset2, 
                                                 parameter, valueA, valueB, statproperty)
                    result = result.to_html()

                if user.is_authenticated:
                    object = Compute()
                    form.populate_obj(object)
                    object.result = result
                    object.plot = plot
                    object.user = user
                    object.filename = filename
                    db.session.add(object)
                    db.session.commit()

                return render_template("view_output.html", form=form, 
                                        result=result, user=user, 
                                        plot=plot)

        elif request.form.get('reset'):
            filename = None
            statData = None
            statFunc = None
            statParm = [{}, {}]
            dataset1 = None
            dataset2 = None
            parmNames = None
            selectfunc = None
            result = None
            return render_template("view.html", form=form, user=user)

    else:
        selectfunc = None
        result = None
        return render_template("view.html", form=form, user=user)


def populate_form_from_instance(instance):
    """Repopulate form with previous values"""
    form = ComputeForm()
    for field in form:
        field.data = getattr(instance, field.name)
    return form


def send_email(user):
    from flask.ext.mail import Mail, Message
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


@app.route('/reg', methods=['GET', 'POST'])
def create_login():
    from forms import register_form
    form = register_form(request.form)
    if request.method == 'POST' and form.validate():
        user = User()
        form.populate_obj(user)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('index'))
    return render_template("reg.html", form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    from forms import login_form
    form = login_form(request.form)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        login_user(user)
        return redirect(url_for('index'))
    return render_template("login.html", form=form)

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
        instances = user.Compute.order_by('-id').all()
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


@app.route('/add_comment', methods=['GET','POST'])
@login_required
def add_comment():
    user = current_user
    if request.method == 'POST' and user.is_authenticated:
        instance = user.Compute.order_by('-id').first()
        instance.comments = request.form.get("comments",None)
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


if __name__ == '__main__':
    if not os.path.isfile(os.path.join(os.path.dirname(__file__), 'sqlite.db')):
        db.create_all()
    app.run(debug=True)
