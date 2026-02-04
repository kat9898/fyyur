from datetime import datetime
import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    SelectMultipleField,
    DateTimeField,
    BooleanField,
)
from wtforms.validators import DataRequired, AnyOf, URL, ValidationError

# Allowed genres
GENRES = [
    "Alternative",
    "Blues",
    "Classical",
    "Country",
    "Electronic",
    "Folk",
    "Funk",
    "Hip-Hop",
    "Heavy Metal",
    "Instrumental",
    "Jazz",
    "Musical Theatre",
    "Pop",
    "Punk",
    "R&B",
    "Reggae",
    "Rock n Roll",
    "Soul",
    "Other",
]

# Allowed states
STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]


# Phone validation function
def validate_phone(form, field):
    phone_regex = re.compile(r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$")
    if field.data and not phone_regex.match(field.data):
        raise ValidationError("Invalid phone number. Expected format: XXX-XXX-XXXX")


# Genres validation function
def validate_genres(form, field):
    invalid_genres = [g for g in field.data if g not in GENRES]
    if invalid_genres:
        raise ValidationError(f'Invalid genre(s): {", ".join(invalid_genres)}')


# State validation function
def validate_state(form, field):
    if field.data not in STATES:
        raise ValidationError("Invalid state selection")


def validate_facebook(form, field):
    if field.data:
        if not field.data.startswith("https://www.facebook.com/"):
            raise ValidationError(
                'Facebook link must start with "https://www.facebook.com/"'
            )


class ShowForm(FlaskForm):
    artist_id = StringField("artist_id")
    venue_id = StringField("venue_id")
    start_time = DateTimeField(
        "start_time", validators=[DataRequired()], default=datetime.today()
    )


class VenueForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField(
        "state",
        validators=[DataRequired(), validate_state],
        choices=[(s, s) for s in STATES],
    )
    address = StringField("address", validators=[DataRequired()])
    phone = StringField("phone", validators=[validate_phone])
    image_link = StringField(
        "image_link", validators=[URL(require_tld=False, message="Invalid URL")]
    )
    genres = SelectMultipleField(
        "genres",
        validators=[DataRequired(), validate_genres],
        choices=[(g, g) for g in GENRES],
    )
    facebook_link = StringField(
        "facebook_link", validators=[URL(require_tld=False, message="Invalid URL")]
    )
    website_link = StringField(
        "website_link", validators=[URL(require_tld=False, message="Invalid URL")]
    )
    seeking_talent = BooleanField("seeking_talent")
    seeking_description = StringField("seeking_description")


class ArtistForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    city = StringField("city", validators=[DataRequired()])
    state = SelectField(
        "state",
        validators=[DataRequired(), validate_state],
        choices=[(s, s) for s in STATES],
    )
    phone = StringField("phone", validators=[validate_phone])
    image_link = StringField(
        "image_link", validators=[URL(require_tld=False, message="Invalid URL")]
    )
    genres = SelectMultipleField(
        "genres",
        validators=[DataRequired(), validate_genres],
        choices=[(g, g) for g in GENRES],
    )
    facebook_link = StringField(
        "facebook_link", validators=[URL(require_tld=False, message="Invalid URL")]
    )
    website_link = StringField("website_link", validators=[validate_facebook])
    seeking_venue = BooleanField("seeking_venue")
    seeking_description = StringField("seeking_description")
