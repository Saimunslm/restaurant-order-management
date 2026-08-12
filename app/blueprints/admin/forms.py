from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, IntegerField, PasswordField, SelectField, TextAreaField
from wtforms import DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    display_order = IntegerField("Display Order", default=0, validators=[Optional()])


class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    description = StringField("Description", validators=[Optional()])
    price = FloatField("Price", validators=[DataRequired(), NumberRange(min=0)])
    category_id = IntegerField("Category", validators=[DataRequired()])
    is_available = BooleanField("Available", default=True)


class TableForm(FlaskForm):
    table_number = IntegerField("Table Number", validators=[DataRequired(), NumberRange(min=1)])


class OfferForm(FlaskForm):
    product_id = IntegerField("Product", validators=[DataRequired()])
    offer_price = FloatField("Offer Price", validators=[DataRequired(), NumberRange(min=0)])
    start_date = DateTimeLocalField("Start Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    end_date = DateTimeLocalField("End Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])


class ComboOfferForm(FlaskForm):
    name = StringField("Combo Name", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    combo_price = FloatField("Combo Price", validators=[DataRequired(), NumberRange(min=0)])
    start_date = DateTimeLocalField("Start Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    end_date = DateTimeLocalField("End Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
