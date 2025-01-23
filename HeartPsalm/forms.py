#!/usr/bin/env python3
""" Registeration and login forms. """
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from heartpsalm.models import User
from wtforms.validators import (Length, EqualTo,
                                Email, DataRequired,
                                ValidationError)


class RegisterForm(FlaskForm):
    """
    Validates the uniqueness of username and email during registration.
    """
    def validate_username(self, check_for_user):
        """
        Checks if the username already exists in the database.
        """
        user = User.query.filter_by(username=check_for_user.data).first()
        if user:
            raise ValidationError('Username already exists! Try another name')

    def validate_email_address(self, check_for_email):
        """
        Checks if the email address already exists in the database.
        """
        query = User.query.filter_by(email_address=check_for_email.data)
        email = query.first()
        if email:
            raise ValidationError('Email Address already exists! Try another.')

    username = StringField(
            label='User Name:',
            validators=[Length(min=2, max=30), DataRequired()]
        )

    email_address = StringField(
            label='Email Address:',
            validators=[Email(), DataRequired()]
        )

    password1 = PasswordField(
            label='Choose Password:',
            validators=[Length(min=6), DataRequired()]
        )

    password2 = PasswordField(
            label='Confirm Password:',
            validators=[EqualTo('password1'), DataRequired()]
            )

    submit = SubmitField(label='Create Account')


class LoginForm(FlaskForm):
    """
    Validates the login credentials (username and password).
    """
    username = StringField(label='User Name:', validators=[DataRequired()])
    password = StringField(label='password:', validators=[DataRequired()])
    submit = SubmitField(label='Login')
