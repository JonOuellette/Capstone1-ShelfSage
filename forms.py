from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired, Email, Length, DataRequired

class RegisterForm(FlaskForm):
    """Form for registering new users"""

    username = StringField('Username', validators=[InputRequired(), Length(min=5, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    email = StringField('Email', validators = [InputRequired(), Email(), Length(max=40)])
    first_name = StringField('First Name', validators=[InputRequired(), Length(max =25)])
    last_name = StringField('Last Name', validators=[InputRequired(), Length(max=30)])

class LoginForm(FlaskForm):
    """Form to login users"""
    username = StringField('Username', validators=[InputRequired(), Length(min=5, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])


class UserEditForm(FlaskForm):
    """Form for editting user information"""
    username = StringField('Username', validators=[InputRequired(), Length(min=5, max=15)])
    email = StringField('Email', validators = [InputRequired(), Email(), Length(max=40)])


class SearchForm(FlaskForm):
    """Search form for books"""
    search_query = StringField('Search Books:', validators=[DataRequired()])
    search_type = SelectField('Search Type:', choices=[('title', 'Title'), ('author', 'Author'), ('subject', 'Category')], default='title')
    submit = SubmitField('Search')

class BookShelfForm(FlaskForm):
    """Form for creating a bookshelf"""
    name = StringField('BookShelf Name', validators=[DataRequired(), Length(max=20)])
    description = StringField('Description:', validators = [Length(max=100)])